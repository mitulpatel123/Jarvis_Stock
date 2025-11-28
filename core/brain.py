import asyncio
import logging
import json
from core.scheduler import MarketScheduler
from core.database import db
from core.redis_client import redis_client

# Agents
from agents.finnhub_agent import FinnhubWebSocketAgent
from agents.alpha_vantage_agent import AlphaVantageAgent
from agents.vision_agent import InvestingChartVisionAgent
from agents.technical_agent import TechnicalAnalysisAgent
from agents.sentiment_agent import SentimentAgent
from agents.execution_agent import ExnessExecutionAgent
from agents.risk_agent import DynamicRiskAgent

logger = logging.getLogger(__name__)

class MainBrain:
    """Central orchestrator for the trading system."""
    
    def __init__(self):
        self.scheduler = MarketScheduler()
        self.running = False
        
        # Initialize Agents
        self.agents = [
            FinnhubWebSocketAgent(),
            AlphaVantageAgent(),
            InvestingChartVisionAgent(),
            TechnicalAnalysisAgent(),
            SentimentAgent(),
            ExnessExecutionAgent(),
            DynamicRiskAgent()
        ]
        
        self.execution_agent = self.agents[5] # Reference for direct commands

    async def start(self):
        """Start the brain and all agents."""
        logger.info("🧠 Starting Main Brain...")
        self.running = True
        
        # Connect Infrastructure
        await db.connect()
        await redis_client.connect()
        
        # Start Agents
        for agent in self.agents:
            await agent.start()
            
        # Start Decision Loop
        asyncio.create_task(self.decision_loop())
        
        logger.info("🚀 System is LIVE!")

    async def stop(self):
        """Stop everything."""
        self.running = False
        for agent in self.agents:
            await agent.stop()
        await db.disconnect()
        await redis_client.disconnect()
        logger.info("🛑 System Stopped.")

    async def decision_loop(self):
        """Listen for signals and make decisions."""
        pubsub = await redis_client.subscribe("signals:*")
        
        while self.running:
            try:
                message = await pubsub.get_message(ignore_subscribe_messages=True)
                if message and message['type'] in ['message', 'pmessage']:
                    channel = message['channel']
                    data = json.loads(message['data'])
                    
                    await self.process_signal(channel, data)
                
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"❌ Brain Error: {e}")
                await asyncio.sleep(1)

    async def process_signal(self, channel, data):
        """Core Trading Logic."""
        session = self.scheduler.get_active_session()
        print(f"DEBUG: Session is {session}") # Debug print
        
        if session == "CLOSED":
            print("DEBUG: Market is CLOSED, ignoring signal.")
            return

        # Example Logic: If Technical says BUY
        if "technical" in channel:
            signal = data.get('signal')
            pair = data.get('pair')
            confidence = data.get('confidence', 0)
            
            print(f"DEBUG: Processing {signal} for {pair} with confidence {confidence}")
            
            if signal == "BUY" and confidence > 0.8:
                logger.info(f"💡 High Confidence BUY Signal for {pair}")
                # In real system: Check Sentiment & Risk here
                # Then execute:
                # For demonstration, let's assume a fixed lot_size for now
                lot_size = 0.01 # Example lot size
                
                # 4. Execute Trade
                if self.execution_agent:
                    success = await self.execution_agent.place_order(
                        symbol=pair, # Use 'pair' for symbol
                        side=signal, # Use 'signal' (which is "BUY") for side
                        volume=lot_size
                    )
                    if success:
                        print(f"✅ Trade Executed Successfully!")
                    else:
                        print(f"❌ Trade Execution Failed.")
                else:
                    print("⚠️ Execution Agent not available.")
                print(f"🚀 PLACING TRADE: BUY {pair} (Confidence: {confidence})")
                logger.info(f"🚀 PLACING TRADE: BUY {pair}")
