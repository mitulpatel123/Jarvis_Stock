import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.finnhub_agent import FinnhubWebSocketAgent
from agents.alpha_vantage_agent import AlphaVantageAgent
from agents.vision_agent import InvestingChartVisionAgent
from core.database import db
from core.redis_client import redis_client
from colorama import Fore, Style, init

init()

async def test_data_agents():
    print(f"{Fore.CYAN}🔍 Testing Data Acquisition Agents...{Style.RESET_ALL}\n")
    
    await db.connect()
    await redis_client.connect()
    
    # 1. Test Finnhub
    print(f"{Fore.YELLOW}Testing Finnhub Agent (5s)...{Style.RESET_ALL}")
    finnhub = FinnhubWebSocketAgent(pairs=["OANDA:EUR_USD"])
    await finnhub.start()
    await asyncio.sleep(5)
    await finnhub.stop()
    
    # 2. Test Alpha Vantage
    print(f"\n{Fore.YELLOW}Testing Alpha Vantage Agent...{Style.RESET_ALL}")
    alpha = AlphaVantageAgent(pairs=["EUR/USD"])
    await alpha.start()
    await asyncio.sleep(5) # Give it time to make a request
    await alpha.stop()
    
    # 3. Test Vision
    print(f"\n{Fore.YELLOW}Testing Vision Agent (Taking 1 screenshot)...{Style.RESET_ALL}")
    vision = InvestingChartVisionAgent(pairs=["EUR/USD"])
    await vision.start()
    await vision.run() # Run once manually
    await vision.stop()
    
    print(f"\n{Fore.GREEN}✅ Data Agents Test Complete. Check logs above for details.{Style.RESET_ALL}")

    await db.disconnect()
    await redis_client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_data_agents())
