import asyncio
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.brain import MainBrain
from core.redis_client import redis_client
from colorama import Fore, Style, init

init()

async def test_integration():
    print(f"{Fore.CYAN}🔍 Testing Full System Integration...{Style.RESET_ALL}\n")
    
    # Initialize Brain (but don't start all agents to keep it quiet, or mock them)
    # For this test, we'll start it fully but short-lived
    brain = MainBrain()
    await brain.start()
    
    # Wait for Brain to subscribe to Redis (fix race condition)
    await asyncio.sleep(2)
    
    print(f"{Fore.YELLOW}📡 Simulating HIGH CONFIDENCE BUY Signal...{Style.RESET_ALL}")
    
    # Inject a fake signal into Redis
    await redis_client.publish("signals:technical:EUR/USD", {
        "agent": "test_injector",
        "pair": "EUR/USD",
        "signal": "BUY",
        "confidence": 0.95,
        "reasoning": "Test signal"
    })
    
    # Wait for Brain to process
    print("⏳ Waiting for Brain to react...")
    await asyncio.sleep(5)
    
    # Wait for brain to process
    await asyncio.sleep(10) # Increased wait time for browser interaction
    
    print("✅ Test Signal Sent. Check MainBrain logs for 'PLACING TRADE'.")

if __name__ == "__main__":
    asyncio.run(test_integration())
