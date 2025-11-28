import asyncio
import logging
import json
from datetime import datetime
from agents.visual_base_agent import VisualBaseAgent
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

class NewsAgent(VisualBaseAgent):
    """Agent to scrape ForexLive and analyze sentiment."""
    
    def __init__(self):
        super().__init__(name="news_agent", loop_interval=60)
        self.url = "https://www.forexlive.com/"

    async def run(self):
        """Scrape and analyze news."""
        prompt = """
        Analyze this screenshot of ForexLive homepage.
        1. Extract the top 3 most recent forex-related headlines.
        2. For each headline, determine if it is Bullish, Bearish, or Neutral for USD, EUR, or GBP.
        3. Provide a confidence score (0.0 - 1.0).
        
        Return JSON format:
        {
            "headlines": [
                {"text": "headline 1", "sentiment": "Bullish USD", "confidence": 0.9},
                ...
            ],
            "overall_sentiment": "Bullish/Bearish/Neutral"
        }
        """
        
        analysis = await self.capture_and_analyze(self.url, prompt)
        
        if analysis:
            await redis_client.publish("signals:news", json.dumps({
                "agent_id": self.name,
                "data": analysis,
                "timestamp": datetime.utcnow().isoformat()
            }))
            logger.info(f"📰 News Analysis Published: {analysis.get('overall_sentiment')}")
