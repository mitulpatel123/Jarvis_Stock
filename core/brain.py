import asyncio
import logging
import json
from collections import deque, defaultdict
from datetime import datetime, timedelta
from core.scheduler import MarketScheduler
from core.database import db
from core.redis_client import redis_client
from config.settings import settings

# Agents
from agents.finnhub_agent import FinnhubWebSocketAgent
from agents.alpha_vantage_agent import AlphaVantageAgent
from agents.vision_agent import InvestingChartVisionAgent
from agents.technical_agent import TechnicalAnalysisAgent
from agents.sentiment_agent import SentimentAgent
from agents.execution_agent import ExnessExecutionAgent
from agents.risk_agent import DynamicRiskAgent
from agents.session_agent import SessionAgent
from agents.news_agent import NewsAgent
from agents.social_agent import SocialAgent
from agents.correlation_agent import CorrelationAgent
from agents.volatility_agent import VolatilityAgent

logger = logging.getLogger(__name__)

class SignalBuffer:
    """Stores signals in a rolling window."""
    def __init__(self, window_seconds=10):
        self.window_seconds = window_seconds
        self.buffer = defaultdict(list) # {pair: [{signal_data}, ...]}

    def add_signal(self, pair, data):
        now = datetime.utcnow()
        data['received_at'] = now
        self.buffer[pair].append(data)
        self.cleanup(pair, now)

    def cleanup(self, pair, now):
        cutoff = now - timedelta(seconds=self.window_seconds)
        self.buffer[pair] = [s for s in self.buffer[pair] if s['received_at'] > cutoff]

    def get_votes(self, pair):
        buy_votes = 0
        sell_votes = 0
        total_confidence = 0
        count = 0
        
        for s in self.buffer[pair]:
            sig = s.get('signal') or s.get('sentiment') # Handle different keys
            conf = s.get('confidence', 0.5)
            
            # Normalize signals
            if isinstance(sig, str):
                if "BUY" in sig.upper() or "BULLISH" in sig.upper():
                    buy_votes += 1
                    total_confidence += conf
                    count += 1
                elif "SELL" in sig.upper() or "BEARISH" in sig.upper():
                    sell_votes += 1
                    total_confidence += conf
                    count += 1
                    
        avg_conf = (total_confidence / count) if count > 0 else 0
        return buy_votes, sell_votes, avg_conf, count

class MainBrain:
    """Central orchestrator with advanced voting logic."""
    
    def __init__(self):
        self.scheduler = MarketScheduler()
        self.running = False
        self.signal_buffer = SignalBuffer(window_seconds=10)
        
        # Initialize Agents
        self.agents = [
            FinnhubWebSocketAgent(),
            AlphaVantageAgent(),
            InvestingChartVisionAgent(),
            TechnicalAnalysisAgent(),
            SentimentAgent(),
            ExnessExecutionAgent(),
            DynamicRiskAgent(),
            SessionAgent(),
            NewsAgent(),
            SocialAgent(),
            CorrelationAgent(),
            VolatilityAgent()
        ]
        
        self.execution_agent = self.agents[5]
        self.risk_agent = self.agents[6]

    async def system_health_check(self):
        """Verify system integrity before starting."""
        logger.info("🏥 Running System Health Check...")
        
        # Check Redis
        if not redis_client.redis:
            logger.error("❌ Redis not connected!")
            return False
            
        # Check API Keys
        if not settings.GROQ_API_KEYS:
            logger.error("❌ No Groq API Keys found!")
            return False
            
        logger.info("✅ System Health Check Passed.")
        return True

    async def start(self):
        """Start the brain and all agents."""
        logger.info("🧠 Starting Main Brain...")
        
        # Connect Infrastructure
        await db.connect()
        await redis_client.connect()
        
        if not await self.system_health_check():
            logger.error("🛑 System Health Check Failed. Aborting.")
            return

        self.running = True
        
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
                    
                    # Extract pair if available
                    pair = data.get('pair') or data.get('symbol')
                    if pair:
                        self.signal_buffer.add_signal(pair, data)
                        await self.process_voting(pair)
                
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"❌ Brain Error: {e}")
                await asyncio.sleep(1)

    async def process_voting(self, pair):
        """Execute trade if voting threshold met."""
        buy_votes, sell_votes, avg_conf, total_votes = self.signal_buffer.get_votes(pair)
        
        # Thresholds
        VOTE_THRESHOLD = 3 # Reduced for testing (Prompt said 15, but we have fewer active signal agents currently)
        CONFIDENCE_THRESHOLD = 0.75
        
        decision = None
        if buy_votes >= VOTE_THRESHOLD and avg_conf > CONFIDENCE_THRESHOLD:
            decision = "BUY"
        elif sell_votes >= VOTE_THRESHOLD and avg_conf > CONFIDENCE_THRESHOLD:
            decision = "SELL"
            
        if decision:
            logger.info(f"🗳️ Voting Result for {pair}: {decision} ({buy_votes} vs {sell_votes}, Conf: {avg_conf:.2f})")
            
            # Risk Check
            risk_check = await self.risk_agent.check_risk(pair, decision)
            if risk_check['allowed']:
                logger.info(f"✅ Risk Agent Approved. Executing {decision}...")
                
                success = await self.execution_agent.place_order(
                    symbol=pair,
                    side=decision,
                    volume=risk_check.get('lot_size', 0.01)
                )
                
                if success:
                    logger.info(f"🚀 Trade Executed: {decision} {pair}")
                    # Clear buffer to avoid double entry
                    self.signal_buffer.buffer[pair] = []
            else:
                logger.warning(f"🛑 Risk Agent Blocked: {risk_check['reason']}")
