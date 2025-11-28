import asyncio
import logging
import os
from playwright.async_api import async_playwright
from agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)

class InvestingChartVisionAgent(BaseAgent):
    """Agent to capture chart screenshots from Investing.com."""
    
    def __init__(self, pairs=None):
        super().__init__(name="vision_agent", loop_interval=30) # Every 30s
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
        slug = pair.lower().replace("/", "-")
        url = f"https://www.investing.com/currencies/{slug}-chart"
        
        page = await self.context.new_page()
        try:
            await page.goto(url, timeout=60000)
            
            # Wait for chart container
            # Note: Investing.com selectors change, this is a best guess for the generic container
            # We might need to adjust this selector based on actual page structure
            try:
                await page.wait_for_selector("#chart-container", timeout=10000)
                element = await page.query_selector("#chart-container")
            except:
                # Fallback to body if specific container not found (just to prove it works)
                element = await page.query_selector("body")

            if element:
                filename = f"data/charts/{slug}_{int(asyncio.get_event_loop().time())}.png"
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                await element.screenshot(path=filename)
                await self.log(f"📸 Screenshot saved: {filename}")
            else:
                logger.warning(f"⚠️ Could not find chart element for {pair}")

        except Exception as e:
            logger.error(f"❌ Vision Error for {pair}: {e}")
        finally:
            await page.close()
