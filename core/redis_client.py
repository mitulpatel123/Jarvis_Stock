import redis.asyncio as redis
import json
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self):
        self.redis = None

    async def connect(self):
        """Connect to Redis"""
        if self.redis:
            return

        try:
            self.redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                decode_responses=True
            )
            await self.redis.ping()
            logger.info("✅ Connected to Redis")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise

    async def disconnect(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("✅ Disconnected from Redis")

    async def publish(self, channel, message):
        """Publish a message to a channel"""
        if isinstance(message, dict):
            message = json.dumps(message)
        await self.redis.publish(channel, message)

    async def subscribe(self, channel):
        """Subscribe to a channel (supports patterns)"""
        pubsub = self.redis.pubsub()
        if "*" in channel:
            await pubsub.psubscribe(channel)
        else:
            await pubsub.subscribe(channel)
        return pubsub

    async def set(self, key, value, expire=None):
        """Set a key-value pair"""
        await self.redis.set(key, value, ex=expire)

    async def get(self, key):
        """Get a value by key"""
        return await self.redis.get(key)

redis_client = RedisClient()
