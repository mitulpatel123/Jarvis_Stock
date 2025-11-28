import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.technical_agent import TechnicalAnalysisAgent
from agents.sentiment_agent import SentimentAgent
from agents.alpha_vantage_agent import AlphaVantageAgent
from core.database import db
from core.redis_client import redis_client
from colorama import Fore, Style, init

init()

async def test_analysis_agents():
    print(f"{Fore.CYAN}🔍 Testing Analysis Agents (REAL DATA)...{Style.RESET_ALL}\n")
    
    await db.connect()
    await redis_client.connect()
    
    # 1. Start Technical Agent
    print(f"{Fore.YELLOW}Starting Technical Agent...{Style.RESET_ALL}")
    tech_agent = TechnicalAnalysisAgent()
    await tech_agent.start()
    
    # Fetch REAL data using AlphaVantageAgent
    print(f"📡 Fetching REAL technical data from Alpha Vantage...")
    alpha_agent = AlphaVantageAgent(pairs=["EUR/USD"])
    await alpha_agent.run() # This will fetch and publish to Redis
    
    # Wait for Technical Agent to process it
    await asyncio.sleep(5)
    await tech_agent.stop()
    
    # 2. Start Sentiment Agent
    print(f"\n{Fore.YELLOW}Starting Sentiment Agent (Scraping ForexLive)...{Style.RESET_ALL}")
    sent_agent = SentimentAgent()
    await sent_agent.start()
    await sent_agent.run() # Force run immediately
    
    # Wait for analysis
    await asyncio.sleep(5)
    await sent_agent.stop()
    
    print(f"\n{Fore.GREEN}✅ Analysis Agents Test Complete.{Style.RESET_ALL}")

    await db.disconnect()
    await redis_client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_analysis_agents())
