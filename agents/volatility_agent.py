import asyncio
import logging
import json
from agents.base_agent import BaseAgent
from core.redis_client import redis_client
from datetime import datetime

logger = logging.getLogger(__name__)

class VolatilityAgent(BaseAgent):
    """Agent to monitor volatility (ATR)."""
    
    def __init__(self):
        super().__init__(name="volatility_agent", loop_interval=60)

    async def run(self):
        """Calculate ATR and signal volatility state."""
        # Mock ATR calculation
        atr_value = 0.0015 # 15 pips
        threshold_low = 0.0010
        threshold_high = 0.0030
        
        state = "NORMAL"
        if atr_value < threshold_low:
            state = "WAIT_CONSOLIDATION"
        elif atr_value > threshold_high:
            state = "BREAKOUT_WATCH"
            
        await redis_client.publish("signals:volatility", json.dumps({
            "agent_id": self.name,
            "state": state,
            "atr": atr_value,
            "timestamp": datetime.utcnow().isoformat()
        }))
        logger.info(f"zz Volatility State: {state} (ATR: {atr_value})")
