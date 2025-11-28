import asyncio
import sys
import os
import json
from colorama import Fore, Style, init
import redis.asyncio as redis

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings

init()

async def send_signal():
    print(f"{Fore.CYAN}📡 Connecting to Redis...{Style.RESET_ALL}")
    
    # Connect to Redis
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        decode_responses=True
    )
    
    print(f"{Fore.YELLOW}🚀 Sending HIGH CONFIDENCE BUY Signal for EUR/USD...{Style.RESET_ALL}")
    
    # Payload
    signal_data = {
        "agent": "manual_injector",
        "pair": "EUR/USD",
        "signal": "BUY",
        "confidence": 0.99,
        "reasoning": "Manual test injection for live execution verification."
    }
    
    # Publish
    await redis_client.publish("signals:technical:EUR/USD", json.dumps(signal_data))
    
    print(f"{Fore.GREEN}✅ Signal Sent! Check your running 'main.py' console and the Browser.{Style.RESET_ALL}")
    
    await redis_client.close()

if __name__ == "__main__":
    asyncio.run(send_signal())
