import asyncio
import sys
import os
import logging
from colorama import init, Fore, Style

import redis

# Initialize colorama
init(autoreset=True)

class RedisLogHandler(logging.Handler):
    """Publishes logs to Redis for the Dashboard."""
    def __init__(self):
        super().__init__()
        try:
            self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        except Exception:
            self.redis = None
    
    def emit(self, record):
        if not self.redis: return
        try:
            msg = self.format(record)
            self.redis.publish("logs", msg)
        except Exception:
            pass

# Configure Logging to Redis
redis_handler = RedisLogHandler()
redis_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(redis_handler)

async def main():
    print(Fore.CYAN + Style.BRIGHT + """
    ╔══════════════════════════════════════════════════════════════╗
    ║               J.A.R.V.I.S. TRADING SYSTEM v2.0               ║
    ║        Autonomous Multi-Agent Forex Trading Ecosystem        ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    print(Fore.YELLOW + "Select Mode:")
    print("1. 📄 Paper Trade (Simulation)")
    print("2. 💸 Live Trade (Real Money)")
    
    choice = input(Fore.GREEN + "\nEnter choice [1/2]: ").strip()
    
    mode = "PAPER"
    if choice == "2":
        mode = "LIVE"
        print(Fore.RED + "\n⚠️  WARNING: LIVE TRADING SELECTED. REAL MONEY AT RISK.")
        confirm = input("Type 'CONFIRM' to proceed: ")
        if confirm != "CONFIRM":
            print("Aborted.")
            return
            
        # Verify Credentials
        from config.settings import settings
        if not settings.EXNESS_EMAIL or not settings.EXNESS_PASSWORD:
            print(Fore.RED + "❌ Error: Exness credentials missing in .env")
            return
    
    print(Fore.BLUE + f"\n🚀 Initializing {mode} Mode...")
    
    # Run Health Check
    print(Fore.WHITE + "Running System Health Check...")
    from tools.health_check import check_health
    healthy = await check_health()
    
    if not healthy:
        print(Fore.RED + "❌ Health Check Failed. Please fix issues above.")
        return
        
    # Start Brain
    print(Fore.GREEN + "\n🧠 Launching Main Brain...")
    from core.brain import MainBrain
    
    brain = MainBrain()
    try:
        await brain.start(mode=mode)
        
        # Keep alive
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n🛑 Shutting down...")
        await brain.stop()
    except Exception as e:
        print(Fore.RED + f"\n❌ Critical Error: {e}")
        await brain.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
