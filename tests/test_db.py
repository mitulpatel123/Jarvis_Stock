import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.database import db
from core.redis_client import redis_client
from colorama import Fore, Style, init

init()

async def test_infrastructure():
    print(f"{Fore.CYAN}🔍 Testing Database & Redis Infrastructure...{Style.RESET_ALL}\n")
    
    # 1. Test PostgreSQL
    print(f"{Fore.YELLOW}Testing PostgreSQL...{Style.RESET_ALL}")
    try:
        await db.connect()
        
        # Insert test log
        await db.execute(
            "INSERT INTO logs (level, message, agent_id) VALUES ($1, $2, $3)",
            "INFO", "Test log message", "test_agent"
        )
        
        # Fetch test log
        rows = await db.fetch("SELECT * FROM logs WHERE agent_id = $1", "test_agent")
        if rows:
            print(f"{Fore.GREEN}✅ PostgreSQL Write/Read Successful{Style.RESET_ALL}")
            print(f"   Read: {rows[0]['message']}")
        else:
            print(f"{Fore.RED}❌ PostgreSQL Read Failed{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}❌ PostgreSQL Test Failed: {e}{Style.RESET_ALL}")

    # 2. Test Redis
    print(f"\n{Fore.YELLOW}Testing Redis...{Style.RESET_ALL}")
    try:
        await redis_client.connect()
        
        # Set key
        await redis_client.set("test_key", "Hello Redis")
        
        # Get key
        value = await redis_client.get("test_key")
        
        if value == "Hello Redis":
            print(f"{Fore.GREEN}✅ Redis Write/Read Successful{Style.RESET_ALL}")
            print(f"   Read: {value}")
        else:
            print(f"{Fore.RED}❌ Redis Read Failed{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}❌ Redis Test Failed: {e}{Style.RESET_ALL}")

    # Cleanup
    await db.disconnect()
    await redis_client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_infrastructure())
