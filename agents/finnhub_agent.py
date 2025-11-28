import asyncio
import json
import websockets
import logging
from collections import deque
from agents.base_agent import BaseAgent
from config.settings import settings
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

class FinnhubWebSocketAgent(BaseAgent):
    """Agent to stream real-time forex data from Finnhub."""
    
    def __init__(self, pairs=None):
        super().__init__(name="finnhub_agent", loop_interval=1)
        self.pairs = pairs or ["OANDA:EUR_USD", "OANDA:GBP_USD", "OANDA:USD_JPY"]
        self.api_key = settings.FINNHUB_API_KEYS[0] if settings.FINNHUB_API_KEYS else None
        self.tick_buffer = deque(maxlen=100)

    async def run(self):
        """Main loop - maintains WebSocket connection."""
        if not self.api_key:
            logger.error("❌ No Finnhub API key found!")
            await asyncio.sleep(5)
            return

        uri = f"wss://ws.finnhub.io?token={self.api_key}"
        
        try:
            async with websockets.connect(uri) as ws:
                await self.log("🔌 Connected to Finnhub WebSocket")
                
                # Subscribe to pairs
                for pair in self.pairs:
                    await ws.send(json.dumps({'type': 'subscribe', 'symbol': pair}))
                    logger.info(f"Subscribed to {pair}")

                # Process messages
                async for message in ws:
                    if not self.running:
                        break
                        
                    data = json.loads(message)
                    if data.get('type') == 'trade':
                        for trade in data['data']:
                            await self.process_tick(trade)
                            
        except Exception as e:
            logger.error(f"❌ WebSocket Error: {e}")
            await asyncio.sleep(5)  # Backoff before reconnect

    async def process_tick(self, tick):
        """Process a single tick."""
        symbol = tick['s']
        price = tick['p']
        timestamp = tick['t']
        
        # Publish to Redis for other agents
        await redis_client.publish(f"ticks:{symbol}", {
            "symbol": symbol,
            "price": price,
            "timestamp": timestamp,
            "source": "finnhub"
        })
        
        # Log occasionally
        self.tick_buffer.append(price)
        if len(self.tick_buffer) % 50 == 0:
            await self.log(f"📉 {symbol} @ {price}")
