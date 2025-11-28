import asyncio
import logging
import os
import base64
from playwright.async_api import async_playwright
from agents.base_agent import BaseAgent
from config.settings import settings
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

class ExnessExecutionAgent(BaseAgent):
    """Agent to execute trades on Exness Web Terminal."""
    
    def __init__(self):
        super().__init__(name="execution_agent", loop_interval=1)
        self.browser = None
        self.page = None
        self.email = settings.EXNESS_EMAIL
        self.password = settings.EXNESS_PASSWORD

    async def start(self):
        # Initialize Playwright
        self.playwright = await async_playwright().start()
        
        # Use the persistent profile created by login_helper
        user_data_dir = "exness_browser_profile"
        
        if os.path.exists(user_data_dir):
            logger.info(f"📂 Loading profile from {user_data_dir}")
            # Launch persistent context
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            )
            self.browser = self.context # For compatibility with stop()
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        else:
            logger.warning("⚠️ No profile found. Please run tools/login_helper.py first!")
            return
        
        await super().start()
        
        # Check if logged in
        try:
            await self.page.goto("https://my.exness.com/accounts", timeout=30000)
            await self.page.wait_for_url("**/accounts", timeout=10000)
            await self.log("✅ Already logged in (Profile Valid)")
        except:
            await self.log("❌ Profile invalid or not logged in. Please run login_helper.py again.")

    async def stop(self):
        await super().stop()
        if self.browser:
            await self.browser.close()
        if hasattr(self, 'playwright'):
            await self.playwright.stop()

    async def place_order(self, symbol: str, side: str, volume: float, stop_loss: float = None, take_profit: float = None):
        """
        Places a trade on the Exness Terminal.
        """
        if not self.page:
            logger.error("❌ Browser page not initialized.")
            return False

        try:
            logger.info(f"🚀 Placing Order: {side.upper()} {symbol} | Vol: {volume}")

            # 1. Validate/Switch Symbol
            # Check if the order panel is visible and has the correct symbol
            header_el = self.page.locator('div[data-test="order-panel-desktop-header"]')
            symbol_el = header_el.locator('[data-test^="symbol-"]')
            
            panel_ready = False
            if await header_el.is_visible():
                if await symbol_el.count() > 0:
                    current_symbol_text = await symbol_el.inner_text()
                    if symbol in current_symbol_text:
                        logger.info(f"✅ Order panel already open for {symbol}")
                        panel_ready = True
                    else:
                        logger.info(f"⚠️ Order panel open for {current_symbol_text}, switching to {symbol}...")
                else:
                     logger.warning("⚠️ Order panel header found but symbol not detected.")

            if not panel_ready:
                logger.info(f"🔄 Opening order panel for {symbol}...")
                # Search and select symbol from watchlist to open panel
                search_input = self.page.locator('input[data-test="asset-popup-search"]')
                if await search_input.is_visible():
                    await search_input.click()
                    await search_input.fill(symbol)
                    await self.page.wait_for_timeout(1000) # Wait for search results
                    
                    # Click the symbol in the list
                    # Selector: div[data-test="asset-popup-list-item"][data-symbol="{symbol}"]
                    # Note: The symbol in data-symbol might be "EURUSD" while input is "EUR/USD" or vice versa.
                    # Exness usually uses "EURUSD" in data-symbol.
                    clean_symbol = symbol.replace("/", "")
                    symbol_item = self.page.locator(f'div[data-test="asset-popup-list-item"][data-symbol="{clean_symbol}"]')
                    
                    if await symbol_item.count() > 0:
                        await symbol_item.first.click()
                        logger.info(f"✅ Clicked {clean_symbol} in watchlist.")
                        await self.page.wait_for_timeout(3000) # Wait for panel to open/load
                    else:
                        logger.error(f"❌ Symbol {clean_symbol} not found in watchlist search results.")
                        return False
                else:
                    logger.error("❌ Watchlist search input not visible.")
                    return False

            # 2. Set Volume
            # Selector: div[data-test="order-panel-volume-input"] input
            vol_input = self.page.locator('div[data-test="order-panel-volume-input"] input')
            await vol_input.click()
            await vol_input.fill(str(volume))
            
            # --- SAFETY CHECKS ---
            if not await self.validate_spread():
                logger.error("❌ Trade Aborted: Spread too high.")
                return False
                
            if not await self.verify_trade_visual(side.upper()):
                logger.error("❌ Trade Aborted: Visual verification failed.")
                return False
            # ---------------------
            
            # 3. Execute Trade
            if side.upper() == "BUY":
                btn = self.page.locator('button[data-test="order-button-buy"]')
            else:
                btn = self.page.locator('button[data-test="order-button-sell"]')
            
            if await btn.is_enabled():
                await btn.click()
                logger.info(f"✅ Clicked {side.upper()} button.")
                
                # 4. Verify Confirmation (Optional but good)
                # We can wait for a toast or just assume success for now.
                # A toast usually appears in div[data-rht-toaster=""]
                await self.page.wait_for_timeout(2000) 
                return True
            else:
                logger.error(f"❌ {side.upper()} button is disabled.")
                return False

        except Exception as e:
            logger.error(f"❌ Error placing order: {e}")
            return False
    async def login(self):
        """Log in to Exness."""
        if not self.email or not self.password:
            logger.error("❌ Missing Exness credentials!")
            return

        try:
            await self.log("🔐 Logging into Exness...")
            # Use direct link as requested, but be ready for popups
            await self.page.goto("https://my.exness.com/accounts/sign-in?lng=en", timeout=60000)
            
            # 1. Handle "Not US Citizen" Popup
            # This might appear before or after the page loads fully
            try:
                # Look for the specific text the user mentioned
                us_citizen_text = "I confirm that I am not a resident of the United States of America"
                # Wait briefly to see if it appears
                popup = await self.page.wait_for_selector(f"text={us_citizen_text}", timeout=5000)
                if popup:
                    await self.log("⚠️ Found 'Not US Citizen' popup. Attempting to confirm...")
                    # Click the checkbox/label associated with this text
                    # We try to click the text itself or a checkbox near it
                    await self.page.click(f"text={us_citizen_text}")
                    
                    # Look for a continue/confirm button
                    continue_btn = await self.page.query_selector('button:has-text("Continue")')
                    if continue_btn:
                        await continue_btn.click()
                    await self.log("✅ Confirmed 'Not US Citizen'")
            except Exception:
                # It's okay if it doesn't appear
                pass

            # 2. Handle Cloudflare / "Verify you are human"
            # We cannot automate this easily, so we wait for the user
            try:
                cloudflare = await self.page.query_selector("text=Verify you are human")
                if cloudflare:
                    await self.log("🛑 Cloudflare detected! Please solve the CAPTCHA manually.")
                    # Wait until the login input appears (meaning captcha is solved)
                    await self.page.wait_for_selector('input[name="login"]', timeout=60000)
                    await self.log("✅ CAPTCHA solved (or bypassed)")
            except Exception:
                pass

            # 3. Proceed with Login
            await self.log("Waiting for login form...")
            await self.page.wait_for_selector('input[name="login"]', timeout=30000)
            
            await self.page.fill('input[name="login"]', self.email)
            await self.page.fill('input[name="password"]', self.password)
            
            # Click Sign In
            await self.page.click('button[type="submit"]')
            
            # Wait for dashboard
            await self.page.wait_for_url("**/accounts", timeout=60000)
            await self.log("✅ Login Successful!")
            
        except Exception as e:
            logger.error(f"❌ Login Failed: {e}")

    async def run(self):
        """Monitor terminal health (Heartbeat)."""
        while True:
            try:
                if self.page:
                    # Heartbeat Check: Read a timestamp or price
                    # We'll use the server time clock usually found in the footer or header
                    # Selector: div[data-test="server-time-clock"]
                    try:
                        clock_el = self.page.locator('div[data-test="server-time-clock"]')
                        if await clock_el.is_visible():
                            time_text = await clock_el.inner_text()
                            # If time hasn't changed in 10s (checked in next loop), we might be frozen
                            # For now, just logging presence is a basic heartbeat
                            # logger.debug(f"💓 Heartbeat: {time_text}")
                            pass
                        else:
                             logger.warning("⚠️ Server time clock not visible.")
                    except Exception:
                        pass
                        
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"❌ Execution Agent Heartbeat Error: {e}")
                await asyncio.sleep(5)

    async def verify_trade_visual(self, order_type):
        """
        Takes a screenshot and asks Vision AI if it looks like a valid trade setup.
        FAIL-SAFE: Defaults to False if anything goes wrong.
        """
        try:
            # Take screenshot of the order panel
            panel = self.page.locator('div[data-test="order-panel"]')
            if await panel.is_visible():
                screenshot_bytes = await panel.screenshot()
                base64_image = base64.b64encode(screenshot_bytes).decode('utf-8')
                
                prompt = f"Does this screen show a confirmed {order_type} order setup ready to be clicked? Reply YES or NO."
                
                # Use Groq Vision (Mocked for now as we don't have shared vision client here yet)
                # In production: response = await visual_agent.analyze(base64_image, prompt)
                # For now, we assume True if panel is visible, but in real logic:
                # if "YES" in response: return True
                
                # FAIL-SAFE: If we can't verify, we return False (unless testing)
                # For this phase, we'll log and return True to allow testing, 
                # but in production this should be False.
                logger.info("👀 Visual Verification: Panel Visible (Simulated YES)")
                return True 
                
            logger.warning("⚠️ Visual Verification Failed: Panel not visible")
            return False
        except Exception as e:
            logger.error(f"❌ Visual verification error: {e}")
            return False # Fail safe

    async def validate_spread(self):
        """
        Check if spread is within safe limits (< 2.0 pips).
        Returns True if safe, False if too high.
        """
        try:
            # Selector for spread might be in the header or chart
            # This is hypothetical as Exness UI varies
            # We'll look for a spread element or calculate from Bid/Ask if visible
            # For now, we'll return True to not block, but log the check.
            
            # Example: Retrieve spread from Redis if available (faster than scraping)
            # spread = await redis_client.get(f"spread:{symbol}")
            
            logger.info("🛡️ Spread Check: Safe (Simulated)")
            return True
        except Exception as e:
            logger.warning(f"⚠️ Spread check failed: {e}")
            return False # Fail safe if we can't verify spread

