import asyncio
import logging
import os
from playwright.async_api import async_playwright
from agents.base_agent import BaseAgent

import base64
from core.llm import groq_rotator

logger = logging.getLogger(__name__)

class InvestingChartVisionAgent(BaseAgent):
    """Agent to capture chart screenshots from Investing.com."""
    
    def __init__(self, pairs=None):
        super().__init__(name="vision_agent", loop_interval=300) # Every 5 mins to avoid spamming
        self.pairs = pairs or ["EUR/USD"]
        self.browser = None
        self.context = None

    async def start(self):
        # Initialize Playwright
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        await super().start()

    async def stop(self):
        await super().stop()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def run(self):
        """Capture screenshots for pairs."""
        for pair in self.pairs:
            await self.capture_chart(pair)

    async def capture_chart(self, pair):
        """Navigate and screenshot."""
        # Map pair to URL (e.g., EUR/USD -> eur-usd)
        # Map pair to URL (e.g., EUR/USD -> EURUSD)
        symbol = pair.replace("/", "")
        url = f"https://www.tradingview.com/symbols/{symbol}/"
        
        page = await self.context.new_page()
        try:
            await page.goto(url, timeout=60000)
            
            # Wait for chart container
            # TradingView usually has a main chart widget
            try:
                # Wait for the advanced chart widget or the overview chart
                await page.wait_for_selector(".tv-chart-view", timeout=15000)
                element = await page.query_selector(".tv-chart-view")
            except:
                # Fallback to a broader container if specific one fails
                try:
                    await page.wait_for_selector("div[class*='chart-container']", timeout=5000)
                    element = await page.query_selector("div[class*='chart-container']")
                except:
                    element = await page.query_selector("body")

            if element:
                # 1. Capture Screenshot as Base64
                screenshot_bytes = await element.screenshot()
                base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                # 2. Get Groq Client
                client = groq_rotator.get_client()
                
                # 3. Analyze with Groq Vision
                # Using llama-3.2-11b-vision-preview (Free Tier)
                response = client.chat.completions.create(
                    model="meta-llama/llama-4-scout-17b-16e-instruct",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Analyze this forex chart. Identify the trend (BULLISH/BEARISH), key support/resistance levels, and any visible candlestick patterns. Return JSON: {trend, support, resistance, patterns, signal}"},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    temperature=0.1,
                    max_tokens=1024,
                    response_format={"type": "json_object"}
                )
                
                analysis = response.choices[0].message.content
                await self.log(f"👁️ Vision Analysis for {pair}: {analysis}")
                
                # Save locally for debug
                filename = f"data/charts/{symbol}_{int(asyncio.get_event_loop().time())}.png"
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, "wb") as f:
                    f.write(screenshot_bytes)
                # await self.log(f"📸 Screenshot saved: {filename}")
            else:
                logger.warning(f"⚠️ Could not find chart element for {pair}")

        except Exception as e:
            logger.error(f"❌ Vision Error for {pair}: {e}")
        finally:
            await page.close()


