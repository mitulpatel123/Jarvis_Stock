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

    async def start(self, mode="PAPER"):
        """Start the brain and all agents."""
        logger.info(f"🧠 Starting Main Brain in {mode} Mode...")
        
        # Connect Infrastructure
        await db.connect()
        await redis_client.connect()
        
        if not await self.system_health_check():
            logger.error("🛑 System Health Check Failed. Aborting.")
            return

        self.running = True
        
        # Start Agents
        for agent in self.agents:
            if isinstance(agent, ExnessExecutionAgent):
                await agent.start(mode=mode)
            else:
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
        self.pubsub = await redis_client.subscribe("signals:*")
        
        while self.running:
            try:
                message = await self.pubsub.get_message(ignore_subscribe_messages=True)
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

    async def determine_strategy(self):
        """
        Determine current strategy based on market conditions.
        Returns: "MOMENTUM_BREAKOUT", "MEAN_REVERSION", or "DEFENSIVE"
        """
        # Fetch latest status from Redis (or internal cache if we had one)
        # For now, we'll query Redis directly or assume we have latest data from signals
        # Ideally, VolatilityAgent and SessionAgent publish to 'market_status'
        
        # Simplified: Check last known volatility signal
        # We need a way to store global state. 
        # For this implementation, we'll assume default DEFENSIVE unless we see signals.
        
        return "DEFENSIVE" # Placeholder for complex logic reading from Redis state

    async def update_learning(self):
        """
        Reinforcement Learning: Update agent weights based on closed trades.
        """
        # Query DB for recently closed trades
        # For each trade, check which agents voted for it (need to store votes with trade)
        # If Profit -> Increase Weight
        # If Loss -> Decrease Weight
        pass

    async def process_voting(self, pair):
        """
        Core Decision Engine: Voting with Adaptive Weights.
        """
        votes = self.signal_buffer.get_signals(pair)
        if not votes:
            return

        buy_power = 0.0
        sell_power = 0.0
        total_weight = 0.0
        
        strategy = await self.determine_strategy()
        
        for signal in votes:
            # Assuming signal structure is {'agent': 'agent_name', 'direction': 'BUY'/'SELL', 'confidence': 0.8}
            # Need to adapt this based on actual signal structure from agents
            agent_name = signal.get('agent', 'unknown_agent')
            direction = signal.get('signal') or signal.get('sentiment') # Handle different keys
            confidence = signal.get('confidence', 0.5)

            # Normalize direction
            if isinstance(direction, str):
                if "BUY" in direction.upper() or "BULLISH" in direction.upper():
                    direction = "BUY"
                elif "SELL" in direction.upper() or "BEARISH" in direction.upper():
                    direction = "SELL"
                else:
                    direction = None # Ignore if not clear BUY/SELL

            if not direction:
                continue
            
            # Base Weight
            weight = self.agent_weights.get(agent_name, 1.0)
            
            # Adaptive Strategy Adjustments
            if strategy == "MOMENTUM_BREAKOUT":
                if agent_name in ["technical_agent", "alpha_vantage_agent"]: # Trend agents
                    weight *= 2.0
                # elif agent_name in ["oscillator_agent"]: # Mean reversion agents - Placeholder, need actual agent names
                #     weight *= 0.5
            elif strategy == "MEAN_REVERSION":
                # if agent_name in ["oscillator_agent"]:
                #     weight *= 2.0
                # elif agent_name in ["technical_agent"]:
                #     weight *= 0.5
                pass # Placeholder
            
            weighted_score = confidence * weight
            
            if direction == "BUY":
                buy_power += weighted_score
            elif direction == "SELL":
                sell_power += weighted_score
                
            total_weight += weight

        # Thresholds (Dynamic based on total weight)
        # If we have 10 agents with weight 1.0, max power is 10.0
        # We want > 75% consensus of active weight
        
        required_power = total_weight * 0.75
        
        decision = None
        if buy_power > required_power:
            decision = "BUY"
        elif sell_power > required_power:
            decision = "SELL"
            
        if decision:
            logger.info(f"🗳️ Voting Result for {pair}: {decision} (Power: {max(buy_power, sell_power):.2f}/{total_weight:.2f})")
            
            # Publish to Dashboard
            await redis_client.publish("brain_status", json.dumps({
                "pair": pair,
                "buy": buy_power,
                "sell": sell_power,
                "decision": decision,
                "confidence": (max(buy_power, sell_power) / total_weight * 100) if total_weight > 0 else 0
            }))
            
            # Risk Check
            risk_agent = next((a for a in self.agents if isinstance(a, DynamicRiskAgent)), None)
            if risk_agent:
                risk_check = await risk_agent.check_risk(pair, decision)
                if not risk_check['allowed']:
                    logger.warning(f"🛡️ Risk Agent blocked {decision} on {pair}: {risk_check['reason']}")
                    return

            # Execute
            execution_agent = next((a for a in self.agents if isinstance(a, ExnessExecutionAgent)), None)
            if execution_agent:
                logger.info(f"🚀 Executing {decision} on {pair}")
                success = await execution_agent.place_order(
                    symbol=pair,
                    side=decision,
                    volume=risk_check.get('lot_size', 0.01) # Use lot_size from risk_check
                )
                if success:
                    logger.info(f"🚀 Trade Executed: {decision} {pair}")
                    # Clear buffer to avoid double entry
                    self.signal_buffer.clear(pair)
                else:
                    logger.error(f"❌ Failed to execute trade: {decision} {pair}")
            else:
                logger.warning("❌ Execution Agent not found.")
        else:
            # Log why no decision was made (CRITICAL for debugging)
            max_power = max(buy_power, sell_power)
            direction = "BUY" if buy_power > sell_power else "SELL"
            confidence_pct = (max_power / total_weight * 100) if total_weight > 0 else 0
            logger.info(f"⚖️ Brain Decision: HOLD {pair} | {direction} Confidence: {confidence_pct:.1f}% (Threshold: 75%) | Buy: {buy_power:.1f}, Sell: {sell_power:.1f}")
            
            # Publish to Dashboard
            await redis_client.publish("brain_status", json.dumps({
                "pair": pair,
                "buy": buy_power,
                "sell": sell_power,
                "decision": "HOLD",
                "confidence": confidence_pct
            }))
