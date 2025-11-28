import asyncio
import logging
import json
import aiohttp
from agents.base_agent import BaseAgent
from core.redis_client import redis_client
from config.settings import settings
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CalendarAgent(BaseAgent):
    """Agent to fetch Economic Calendar events (FCS API)."""
    
    def __init__(self):
        super().__init__(name="calendar_agent", loop_interval=300) # Check every 5 mins
        self.api_key = settings.FCS_API_KEY
        self.base_url = "https://fcsapi.com/api-v3/forex/economy"

    async def run(self):
        """Fetch high impact events."""
        if not self.api_key:
            logger.warning("⚠️ FCS API Key missing. Calendar Agent disabled.")
            return

        try:
            # Fetch events for major currencies
            url = f"{self.base_url}?symbol=USD,EUR,GBP,JPY&api_key={self.api_key}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.error(f"❌ FCS API Error: {response.status}")
                        return
                    
                    data = await response.json()
                    
            if "response" not in data:
                return

            events = data["response"]
            high_impact_events = []
            
            now = datetime.utcnow()
            
            for event in events:
                # Filter for High Impact (importance usually 3 or 'High')
                # FCS API format varies, assuming 'importance' field is '3' or 'High'
                importance = str(event.get('importance', '0'))
                
                if importance == '3' or importance.lower() == 'high':
                    # Check time
                    event_time_str = event.get('date') # Format: YYYY-MM-DD HH:MM:SS
                    if not event_time_str: continue
                    
                    event_time = datetime.strptime(event_time_str, "%Y-%m-%d %H:%M:%S")
                    
                    # Check if event is in the next 30 minutes
                    time_diff = event_time - now
                    minutes_diff = time_diff.total_seconds() / 60
                    
                    if 0 <= minutes_diff <= 30:
                        high_impact_events.append({
                            "event": event.get('title'),
                            "currency": event.get('country'),
                            "time_until": f"{int(minutes_diff)} min",
                            "impact": "HIGH"
                        })

            if high_impact_events:
                # Publish to Redis
                await redis_client.publish("market_status", json.dumps({
                    "type": "news_alert",
                    "events": high_impact_events,
                    "timestamp": now.isoformat()
                }))
                logger.warning(f"🚨 High Impact News Incoming: {high_impact_events}")
            else:
                logger.info("📅 No high impact news in next 30 mins.")
                
        except Exception as e:
            logger.error(f"❌ Calendar Agent Error: {e}")
