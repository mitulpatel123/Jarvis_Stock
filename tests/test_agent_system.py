import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.test_agent import TestAgent
from core.database import db
from core.redis_client import redis_client
from colorama import Fore, Style, init

init()

async def test_agent_system():
    print(f"{Fore.CYAN}🔍 Testing Core Agent Architecture...{Style.RESET_ALL}\n")
    
    # Connect infrastructure
    await db.connect()
    await redis_client.connect()
    
    # Initialize Agent
    agent = TestAgent()
    
    # Start Agent
    print(f"{Fore.YELLOW}Starting TestAgent (running for 15 seconds)...{Style.RESET_ALL}")
    await agent.start()
    
    # Let it run for 3 cycles (5s interval * 3 = 15s)
    await asyncio.sleep(16)
    
    # Stop Agent
    await agent.stop()
    
    # Verify logs in DB
    print(f"\n{Fore.YELLOW}Verifying logs in Database...{Style.RESET_ALL}")
    rows = await db.fetch(
        "SELECT * FROM logs WHERE agent_id = $1 ORDER BY timestamp DESC LIMIT 5", 
        "test_agent"
    )
    
    if len(rows) >= 3:
        print(f"{Fore.GREEN}✅ Agent System Verified! Found {len(rows)} logs.{Style.RESET_ALL}")
        for row in rows:
            print(f"   [{row['timestamp']}] {row['message']}")
    else:
        print(f"{Fore.RED}❌ Verification Failed: Not enough logs found.{Style.RESET_ALL}")

    # Cleanup
    await db.disconnect()
    await redis_client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_agent_system())
