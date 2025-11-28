import asyncio
import logging
import json
import asyncpraw
from agents.base_agent import BaseAgent
from core.llm import groq_rotator
from core.redis_client import redis_client
from config.settings import settings
from datetime import datetime

logger = logging.getLogger(__name__)

class SocialAgent(BaseAgent):
    """Agent to analyze Reddit sentiment using real API."""
    
    def __init__(self):
        super().__init__(name="social_agent", loop_interval=300) # 5 mins
        self.subreddits = ["Forex", "Daytrading", "algotrading"]
        self.reddit = None

    async def start(self):
        """Initialize Reddit API connection."""
        await super().start()
        if settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET:
            self.reddit = asyncpraw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT
            )
            logger.info("🤖 Reddit API Initialized")
        else:
            logger.warning("⚠️ Reddit Credentials Missing! Agent will run in mock mode or fail.")

    async def stop(self):
        """Close Reddit connection."""
        await super().stop()
        if self.reddit:
            await self.reddit.close()

    async def run(self):
        """Fetch and analyze Reddit posts."""
        if not self.reddit:
            logger.error("❌ Reddit API not initialized. Skipping run.")
            return

        all_text = []
        try:
            logger.info("🤖 Fetching Reddit posts...")
            for sub_name in self.subreddits:
                subreddit = await self.reddit.subreddit(sub_name)
                async for post in subreddit.hot(limit=10):
                    all_text.append(f"Title: {post.title}\nText: {post.selftext[:200]}")
            
            if not all_text:
                logger.warning("⚠️ No posts found.")
                return

            # Combine for analysis (limit length to avoid token limits)
            combined_text = "\n---\n".join(all_text[:15]) 
            
            prompt = f"""
            Analyze the sentiment of these Reddit posts regarding Forex pairs (EUR, USD, GBP, JPY, XAU).
            Posts:
            {combined_text}
            
            Return a JSON with sentiment score (-1.0 to +1.0) for each currency.
            Format: {{ "USD": 0.5, "EUR": -0.2, ... }}
            """
            
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
            await asyncio.sleep(60) # Backoff on error
