import asyncio
import base64
import logging
import json
from playwright.async_api import async_playwright
from agents.base_agent import BaseAgent
from core.llm import groq_rotator

logger = logging.getLogger(__name__)

class VisualBaseAgent(BaseAgent):
    """Base agent for agents that need to 'see' using Playwright and Vision AI."""
    
    def __init__(self, name, loop_interval=60):
        super().__init__(name, loop_interval)
        self.browser = None
        self.context = None
        self.page = None

    async def start(self):
        """Initialize Playwright."""
        await super().start()
        # We don't start the browser here to save resources, 
        # we start it on demand in capture_and_analyze or in subclass start
        
    async def stop(self):
        """Stop Playwright."""
        await super().stop()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()

    async def capture_and_analyze(self, url, prompt):
        """
        Navigates to a URL, takes a screenshot, and analyzes it with Groq Vision.
        """
        playwright = None
        browser = None
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            logger.info(f"📸 Navigating to {url}...")
            try:
                await page.goto(url, timeout=60000, wait_until="domcontentloaded")
            except Exception as e:
                logger.warning(f"⚠️ Navigation timeout (continuing anyway): {e}")
            
            # Take screenshot
            screenshot_bytes = await page.screenshot(full_page=False)
            base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
            
            logger.info(f"🧠 Sending screenshot to Vision AI...")
            
            # Construct message for Groq
            messages = [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            },
                        },
                    ],
                }
            ]
            
            # Get response from Groq Vision model
            # Note: We need to ensure groq_rotator supports vision requests or use a direct client here
            # Assuming groq_rotator has a method or we use the client directly
            client = groq_rotator.get_client()
            
            completion = client.chat.completions.create(
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                messages=messages,
                temperature=0.1,
                max_tokens=1024,
                response_format={"type": "json_object"}
            )
            
            response_text = completion.choices[0].message.content
            logger.info(f"✅ Vision Analysis: {response_text[:100]}...")
            
            return json.loads(response_text)

        except Exception as e:
            logger.error(f"❌ Vision Error: {e}")
            return None
        finally:
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
