import asyncio
import logging
import pytz
import json
from datetime import datetime
from agents.base_agent import BaseAgent
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

class SessionAgent(BaseAgent):
    """Agent to monitor market sessions and liquidity."""
    
    def __init__(self):
        super().__init__(name="session_agent", loop_interval=60)
        self.sessions = {
            "Sydney": {"start": 22, "end": 7},   # UTC (approx)
            "Tokyo": {"start": 0, "end": 9},
            "London": {"start": 8, "end": 17},
            "NewYork": {"start": 13, "end": 22}
        }

    async def run(self):
        """Check session status every minute."""
        current_time = datetime.now(pytz.utc)
        hour = current_time.hour
        
        active_sessions = []
        for city, hours in self.sessions.items():
            start = hours["start"]
            end = hours["end"]
            if start < end:
                if start <= hour < end:
                    active_sessions.append(city)
            else: # Crosses midnight
                if start <= hour or hour < end:
                    active_sessions.append(city)
        
        # Determine Liquidity
        liquidity = "LOW"
        if "London" in active_sessions and "NewYork" in active_sessions:
            liquidity = "HIGH" # Overlap
        elif "London" in active_sessions:
            liquidity = "MEDIUM"
        elif "NewYork" in active_sessions:
            liquidity = "MEDIUM"
        elif "Tokyo" in active_sessions:
            liquidity = "LOW"
            
        # Mock News Check (Replace with real API later)
        is_news_event = False 
        
        status = {
            "timestamp": current_time.isoformat(),
            "active_sessions": active_sessions,
            "liquidity": liquidity,
            "is_news_event": is_news_event
        }
        
        await redis_client.publish("market_status", json.dumps(status))
        logger.info(f"🌍 Market Status: {active_sessions} | Liquidity: {liquidity}")

    def get_liquidity_status(self, pair):
        """Helper to get liquidity for a specific pair (can be expanded)."""
        # For now, return global liquidity
        return "HIGH" # Placeholder
