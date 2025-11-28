import asyncio
import logging
import json
import aiohttp
from agents.base_agent import BaseAgent
from core.llm import groq_rotator
from core.redis_client import redis_client
from datetime import datetime

logger = logging.getLogger(__name__)

class SocialAgent(BaseAgent):
    """Agent to analyze Reddit sentiment."""
    
    def __init__(self):
        super().__init__(name="social_agent", loop_interval=300) # 5 mins
        self.subreddits = ["Forex", "Daytrading"]

    async def run(self):
        """Fetch and analyze Reddit posts."""
        all_posts = []
        
        # Mocking Reddit API for now as we don't have credentials in prompt
        # In production, use asyncpraw
        logger.info("🤖 Fetching Reddit posts (Mock)...")
        
        # Simulated posts
        mock_posts = [
            "USD is looking strong today after CPI",
            "EURUSD dropping like a stone, shorting now",
            "Gold breaking out, buy XAUUSD",
            "GBPUSD rejection at resistance, time to sell"
        ]
        
        prompt = f"""
        Analyze the sentiment of these Reddit post titles regarding Forex pairs:
        {mock_posts}
        
        Return a JSON with sentiment score (-1 to +1) for: USD, EUR, GBP, XAU.
        Format: {{ "USD": 0.5, "EUR": -0.2, ... }}
        """
        
        try:
            response = await groq_rotator.chat_completion(prompt)
            sentiment_data = json.loads(response)
            
            await redis_client.publish("signals:social", json.dumps({
                "agent_id": self.name,
                "sentiment": sentiment_data,
                "timestamp": datetime.utcnow().isoformat()
            }))
            logger.info(f"🗣️ Social Sentiment: {sentiment_data}")
            
        except Exception as e:
            logger.error(f"❌ Social Analysis Error: {e}")
