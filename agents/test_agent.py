from agents.base_agent import BaseAgent
from core.llm import groq_rotator

class TestAgent(BaseAgent):
    """A simple agent to test the architecture."""
    
    def __init__(self):
        super().__init__(name="test_agent", loop_interval=5)
        self.counter = 0

    async def run(self):
        self.counter += 1
        await self.log(f"Cycle {self.counter}: Waking up...")
        
        # Test Groq
        response = groq_rotator.chat_completion(
            prompt=f"Say 'Hello from cycle {self.counter}' and nothing else.",
            system_prompt="Be concise."
        )
        
        await self.log(f"🤖 AI Response: {response}")
