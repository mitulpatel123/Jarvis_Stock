import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from core.database import db
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(self, name, loop_interval=10):
        self.name = name
        self.loop_interval = loop_interval
        self.running = False
        self.task = None

    async def start(self):
        """Start the agent loop."""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._loop())
        logger.info(f"🟢 Agent {self.name} started")

    async def stop(self):
        """Stop the agent loop."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info(f"🔴 Agent {self.name} stopped")

    async def _loop(self):
        """Internal loop wrapper."""
        while self.running:
            try:
                await self.run()
            except Exception as e:
                logger.error(f"❌ Error in agent {self.name}: {e}")
                logger.error(traceback.format_exc())
            
            await asyncio.sleep(self.loop_interval)

    @abstractmethod
    async def run(self):
        """Main agent logic. Must be implemented by subclasses."""
        pass

    async def log(self, message, level="INFO"):
        """Log to database and console."""
        print(f"[{self.name}] {message}")  # Console
        
        # Async log to DB (fire and forget)
        try:
            await db.execute(
                "INSERT INTO logs (level, message, agent_id) VALUES ($1, $2, $3)",
                level, message, self.name
            )
        except Exception as e:
            print(f"Failed to log to DB: {e}")
