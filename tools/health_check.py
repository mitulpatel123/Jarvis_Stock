import asyncio
import logging
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.redis_client import redis_client
from core.database import db
from config.settings import settings

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("HealthCheck")

async def check_health():
    print("\n🏥 STARTING SYSTEM HEALTH CHECK...\n")
    all_passed = True
    
    # 1. Check Redis
    try:
        await redis_client.connect()
        if await redis_client.redis.ping():
            print("✅ Redis Connection: OK")
        else:
            print("❌ Redis Connection: FAILED")
            all_passed = False
    except Exception as e:
        print(f"❌ Redis Connection: ERROR ({e})")
        all_passed = False
        
    # 2. Check Database
    try:
        await db.connect()
        # Simple query
        await db.pool.fetchval("SELECT 1")
        print("✅ Database Connection: OK")
    except Exception as e:
        print(f"❌ Database Connection: ERROR ({e})")
        all_passed = False
        
    # 3. Check API Keys
    groq_count = len(settings.GROQ_API_KEYS)
    finnhub_count = len(settings.FINNHUB_API_KEYS)
    alpha_count = len(settings.ALPHA_VANTAGE_KEYS)
    
    if groq_count > 0:
        print(f"✅ Groq API Keys: {groq_count} Loaded")
    else:
        print("❌ Groq API Keys: NONE FOUND")
        all_passed = False
        
    if finnhub_count > 0:
        print(f"✅ Finnhub API Keys: {finnhub_count} Loaded")
    else:
        print("⚠️ Finnhub API Keys: NONE FOUND (Warning)")
        
    if alpha_count > 0:
        print(f"✅ Alpha Vantage Keys: {alpha_count} Loaded")
    else:
        print("⚠️ Alpha Vantage Keys: NONE FOUND (Warning)")
        
    # 4. Check Exness Credentials
    if settings.EXNESS_EMAIL and settings.EXNESS_PASSWORD:
        print("✅ Exness Credentials: SET")
    else:
        print("⚠️ Exness Credentials: MISSING (Live Trading will fail)")
        
    print("\n" + "="*30)
    if all_passed:
        print("🚀 SYSTEM STATUS: HEALTHY")
        return True
    else:
        print("🛑 SYSTEM STATUS: UNHEALTHY")
        return False

if __name__ == "__main__":
    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        success = asyncio.run(check_health())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        pass
