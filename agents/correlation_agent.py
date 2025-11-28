import asyncio
import logging
import json
from collections import deque
from agents.base_agent import BaseAgent
from core.redis_client import redis_client
from datetime import datetime

logger = logging.getLogger(__name__)

class CorrelationAgent(BaseAgent):
    """Agent to monitor correlations (EUR/USD vs USD/JPY)."""
    
    def __init__(self):
        super().__init__(name="correlation_agent", loop_interval=60)
        self.history = {
            "EUR/USD": deque(maxlen=60), # 60 minutes of 1-min snapshots
            "USD/JPY": deque(maxlen=60)
        }
        self.last_prices = {}

    async def run(self):
        """Monitor price streams and calculate correlation."""
        # Subscribe to ticks if not already (handled by main brain usually, but here we need data)
        # Actually, agents usually pull data or listen. 
        # For simplicity, we'll listen to the same 'ticks:*' channel or just fetch latest from Redis if available.
        # Since we don't have a shared state manager yet, we'll subscribe in a background task.
        
        if not hasattr(self, 'pubsub'):
            self.pubsub = await redis_client.subscribe("ticks:*")
            asyncio.create_task(self.process_ticks())

        # Analyze every 60 seconds
        await self.analyze_correlation()

    async def process_ticks(self):
        """Background task to collect ticks."""
        while self.running:
            try:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
                if message and message['type'] == 'message':
                    data = json.loads(message['data'])
                    pair = data.get('s') # Finnhub symbol format
                    price = data.get('p')
                    
                    if pair and price:
                        # Normalize pair name
                        if "EUR_USD" in pair: pair = "EUR/USD"
                        elif "USD_JPY" in pair: pair = "USD/JPY"
                        
                        if pair in self.history:
                            self.last_prices[pair] = price
            except Exception:
                pass
            await asyncio.sleep(0.1)

    async def analyze_correlation(self):
        """Calculate correlation/divergence."""
        # Snapshot current prices every minute
        for pair, price in self.last_prices.items():
            self.history[pair].append(price)
            
        if len(self.history["EUR/USD"]) < 2 or len(self.history["USD/JPY"]) < 2:
            return

        # Calculate % change over last hour (or available history)
        eur_start = self.history["EUR/USD"][0]
        eur_end = self.history["EUR/USD"][-1]
        eur_change = (eur_end - eur_start) / eur_start

        jpy_start = self.history["USD/JPY"][0]
        jpy_end = self.history["USD/JPY"][-1]
        jpy_change = (jpy_end - jpy_start) / jpy_start

        # Logic:
        # Normal: EUR/USD UP, USD/JPY DOWN (USD Weakness)
        # Normal: EUR/USD DOWN, USD/JPY UP (USD Strength)
        # Divergence: Both UP or Both DOWN
        
        signal = "NORMAL"
        if (eur_change > 0 and jpy_change > 0) or (eur_change < 0 and jpy_change < 0):
            signal = "WARNING_DIVERGENCE"
            
        await redis_client.publish("signals:correlation", json.dumps({
            "agent_id": self.name,
            "signal": signal,
            "details": {
                "EURUSD_Change": f"{eur_change*100:.4f}%",
                "USDJPY_Change": f"{jpy_change*100:.4f}%"
            },
            "timestamp": datetime.utcnow().isoformat()
        }))
        logger.info(f"🔗 Correlation: {signal} (EU: {eur_change*100:.2f}%, UJ: {jpy_change*100:.2f}%)")
