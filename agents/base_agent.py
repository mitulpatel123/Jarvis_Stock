
import asyncio
import logging
import traceback
from abc import ABC, abstractmethod
from core.database import db
from core.redis_client import redis_client
import json
import os

logger = logging.getLogger(__name__)

class BaseAgent:
    """Base class for all agents."""
    
    def __init__(self, name, loop_interval=60):
        self.name = name
        self.loop_interval = loop_interval
        self.running = False
        self.memory = {}
        self.memory_file = f"memory/{self.name}.json"
        self.load_memory()

    def load_memory(self):
        """Load agent memory from JSON file."""
        if not os.path.exists("memory"):
            os.makedirs("memory")
            
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f:
                    self.memory = json.load(f)
                logger.info(f"🧠 {self.name} loaded memory.")
            except Exception as e:
                logger.error(f"❌ Failed to load memory for {self.name}: {e}")
                self.memory = {}
        else:
            self.memory = {}

    def save_memory(self):
        """Save agent memory to JSON file."""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
            # logger.debug(f"💾 {self.name} saved memory.")
        except Exception as e:
            logger.error(f"❌ Failed to save memory for {self.name}: {e}")

    def learn_navigation(self, page_name, selector, success=True):
        """Record success/failure of a selector."""
        if "navigation" not in self.memory:
            self.memory["navigation"] = {}
            
        if page_name not in self.memory["navigation"]:
            self.memory["navigation"][page_name] = {}
            
        if success:
            self.memory["navigation"][page_name]["best_selector"] = selector
            self.memory["navigation"][page_name]["last_success"] = True
        else:
            # If it failed, maybe clear best_selector if it was this one
            if self.memory["navigation"][page_name].get("best_selector") == selector:
                del self.memory["navigation"][page_name]["best_selector"]
            self.memory["navigation"][page_name]["last_success"] = False
            
        self.save_memory()

    async def start(self):
        """Start the agent loop."""
        self.running = True
        logger.info(f"🟢 {self.name} Started.")
        asyncio.create_task(self._loop())

    async def stop(self):
        """Stop the agent loop."""
        self.running = False
        logger.info(f"🔴 {self.name} Stopped.")

    async def _loop(self):
        """Internal loop wrapper."""
        while self.running:
            try:
                await self.run()
            except Exception as e:
                logger.error(f"❌ {self.name} Error: {e}")
            
            await asyncio.sleep(self.loop_interval)

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
