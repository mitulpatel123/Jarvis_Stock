import json
import logging
from agents.base_agent import BaseAgent
from core.llm import groq_rotator
from core.redis_client import redis_client

logger = logging.getLogger(__name__)

class TechnicalAnalysisAgent(BaseAgent):
    """Agent to analyze technical data using Groq."""
    
    def __init__(self):
        super().__init__(name="technical_agent", loop_interval=1)
        self.pubsub = None

    async def start(self):
        await super().start()
        # Subscribe to technical data
        self.pubsub = await redis_client.subscribe("technical:*")

    async def run(self):
        """Listen for technical data and analyze it."""
        if not self.pubsub:
            return

        message = await self.pubsub.get_message(ignore_subscribe_messages=True)
        if message and message['type'] == 'message':
            data = json.loads(message['data'])
            await self.analyze(data)

    async def analyze(self, data):
        """Analyze technical data with Groq."""
        pair = data['pair']
        indicator = data['indicator']
        value = data['value']
        
        prompt = f"""
        You are a forex expert. 
        The {indicator} for {pair} is {value}.
        
        Analyze this single data point.
        Return JSON only:
        {{
            "signal": "BUY|SELL|NEUTRAL",
            "confidence": 0.0-1.0,
            "reasoning": "Brief explanation"
        }}
        """
        
        try:
            response = groq_rotator.chat_completion(prompt, system_prompt="Return JSON only.")
            # Clean response (sometimes LLMs add markdown)
            response = response.replace("```json", "").replace("```", "").strip()
            analysis = json.loads(response)
            
            await self.log(f"🧠 Analysis for {pair}: {analysis['signal']} ({analysis['reasoning']})")
            
            # Publish signal
            await redis_client.publish(f"signals:technical:{pair}", {
                "agent": self.name,
                "pair": pair,
                "signal": analysis['signal'],
                "confidence": analysis['confidence'],
                "reasoning": analysis['reasoning']
            })
            
        except Exception as e:
            logger.error(f"❌ Analysis Error: {e}")
