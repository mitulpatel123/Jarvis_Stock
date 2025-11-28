import asyncio
import aiohttp
import logging
from agents.base_agent import BaseAgent
from config.settings import settings
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

class AlphaVantageAgent(BaseAgent):
    """Agent to fetch historical/technical data from Alpha Vantage."""
    
    def __init__(self, pairs=None):
        super().__init__(name="alpha_vantage_agent", loop_interval=60) # Run every minute
        self.pairs = pairs or ["EUR/USD", "GBP/USD", "USD/JPY"]
        self.api_keys = settings.ALPHA_VANTAGE_KEYS
        self.current_key_idx = 0

    def get_next_key(self):
        if not self.api_keys:
            return None
        key = self.api_keys[self.current_key_idx]
        self.current_key_idx = (self.current_key_idx + 1) % len(self.api_keys)
        return key

    async def run(self):
        """Fetch technical indicators for all pairs."""
        if not self.api_keys:
            logger.error("❌ No Alpha Vantage API keys found!")
            return

        async with aiohttp.ClientSession() as session:
            for pair in self.pairs:
                await self.fetch_rsi(session, pair)
                await asyncio.sleep(2) # Avoid rate limits

    async def fetch_rsi(self, session, pair):
        """Fetch RSI for a pair."""
        key = self.get_next_key()
        symbol = pair.replace("/", "") # EUR/USD -> EURUSD
        
        url = f"https://www.alphavantage.co/query?function=RSI&symbol={symbol}&interval=1min&time_period=14&series_type=close&apikey={key}"
        
        try:
            async with session.get(url) as response:
                data = await response.json()
                
                if "Technical Analysis: RSI" in data:
                    last_refresh = data["Meta Data"]["3: Last Refreshed"]
                    rsi_val = list(data["Technical Analysis: RSI"].values())[0]["RSI"]
                    
                    await self.log(f"📊 {pair} RSI: {rsi_val}")
                    
                    # Publish to Redis
                    await redis_client.publish(f"technical:{pair}", {
                        "pair": pair,
                        "indicator": "RSI",
                        "value": float(rsi_val),
                        "timestamp": last_refresh
                    })
                elif "Note" in data:
                    logger.warning(f"⚠️ Alpha Vantage Rate Limit: {data['Note']}")
                    
        except Exception as e:
            logger.error(f"❌ Alpha Vantage Error: {e}")
