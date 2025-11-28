import asyncio
import logging
import sys
from core.brain import MainBrain
from colorama import Fore, Style, init

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

init()

async def main():
    print(f"{Fore.CYAN}🤖 Initializing Jarvis Stock Expert...{Style.RESET_ALL}")
    
    brain = MainBrain()
    
    try:
        await brain.start()
        
        # Keep running until Ctrl+C
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Shutting down...{Style.RESET_ALL}")
        await brain.stop()

if __name__ == "__main__":
    asyncio.run(main())
