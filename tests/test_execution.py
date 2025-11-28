import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.execution_agent import ExnessExecutionAgent
from core.database import db
from core.redis_client import redis_client
from colorama import Fore, Style, init

init()

async def test_execution():
    print(f"{Fore.CYAN}🔍 Testing Execution Agent...{Style.RESET_ALL}\n")
    
    # Connect to DB to avoid logging errors
    await db.connect()
    await redis_client.connect()

    agent = ExnessExecutionAgent()
    
    print(f"{Fore.YELLOW}Launching Browser & Attempting Login...{Style.RESET_ALL}")
    print("⚠️  Please watch the browser window.")
    
    await agent.start()
    
    # Keep open for 30 seconds to allow manual verification/2FA
    print("⏳ Keeping browser open for 30 seconds...")
    await asyncio.sleep(30)
    
    await agent.stop()
    print(f"\n{Fore.GREEN}✅ Execution Test Complete.{Style.RESET_ALL}")

if __name__ == "__main__":
    asyncio.run(test_execution())
