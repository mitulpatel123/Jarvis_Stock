import asyncio
import logging
import json
from playwright.async_api import async_playwright
from agents.base_agent import BaseAgent
from core.redis_client import redis_client
from datetime import datetime

logger = logging.getLogger(__name__)

class OrderBookAgent(BaseAgent):
    """Agent to scrape MyFxBook Order Book for contrarian signals."""
    
    def __init__(self):
        super().__init__(name="orderbook_agent", loop_interval=60)
        self.url = "https://www.myfxbook.com/forex-market/orderbook"

    async def run(self):
        """Scrape order book data."""
        playwright = None
        browser = None
        try:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
            page = await browser.new_page()
            
            logger.info("📖 Scraping MyFxBook Order Book...")
            await page.goto(self.url, timeout=60000)
            
            # Wait for table
            await page.wait_for_selector("#orderBookContainer", timeout=30000)
            
            # Extract data for major pairs
            pairs_to_check = ["EURUSD", "GBPUSD", "USDJPY"]
            signals = []
            
            for pair in pairs_to_check:
                # Find row containing the pair
                # Selector strategy: Find link with text 'EURUSD', then get parent row
                # Note: MyFxBook structure might vary, using a robust text search
                row = page.locator(f"tr:has-text('{pair}')")
                
                if await row.count() > 0:
                    # Extract percentages (usually in columns 3 and 4 or similar)
                    # We'll grab all text from the row and parse
                    text = await row.first.inner_text()
                    # Example text: "EURUSD ... 40% ... 60% ..."
                    # This is brittle, but sufficient for scraping demo
                    
                    # Better approach: Get specific cells if possible
                    # Assuming standard table layout: Symbol, ..., Short %, Long %, ...
                    # Let's try to find percentage signs
                    import re
                    percentages = re.findall(r"(\d+)%", text)
                    
                    if len(percentages) >= 2:
                        short_pct = int(percentages[0])
                        long_pct = int(percentages[1])
                        
                        sentiment = "NEUTRAL"
                        if short_pct > 70:
                            sentiment = "BULLISH" # Contrarian: Retail is Short -> We Buy
                        elif long_pct > 70:
                            sentiment = "BEARISH" # Contrarian: Retail is Long -> We Sell
                            
                        signals.append({
                            "pair": pair[:3] + "/" + pair[3:],
                            "short_retail": short_pct,
                            "long_retail": long_pct,
                            "sentiment": sentiment
                        })
            
            if signals:
                await redis_client.publish("signals:orderbook", json.dumps({
                    "agent_id": self.name,
                    "signals": signals,
                    "timestamp": datetime.utcnow().isoformat()
                }))
                logger.info(f"📖 Order Book Signals: {len(signals)} pairs analyzed")
                
        except Exception as e:
            logger.error(f"❌ Order Book Scraping Error: {e}")
        finally:
            if browser:
                await browser.close()
            if playwright:
                await playwright.stop()
