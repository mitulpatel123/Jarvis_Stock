import logging
from agents.base_agent import BaseAgent
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

class DynamicRiskAgent(BaseAgent):
    """Agent to calculate position size and manage risk."""
    
    def __init__(self):
        super().__init__(name="risk_agent", loop_interval=5)
        self.account_balance = 10000.0 # Mock balance for now
        self.risk_per_trade = 0.01 # 1%

    async def run(self):
        """Monitor risk."""
        # In real implementation, this would fetch balance from Exness
        pass

    def calculate_lot_size(self, stop_loss_pips):
        """Calculate lot size based on risk."""
        risk_amount = self.account_balance * self.risk_per_trade
        # Standard lot = $10 per pip (approx for EURUSD)
        # Lot = Risk / (SL * PipValue)
        pip_value = 10 
        if stop_loss_pips == 0: return 0.01
        
        lot_size = risk_amount / (stop_loss_pips * pip_value)
        return round(lot_size, 2)
