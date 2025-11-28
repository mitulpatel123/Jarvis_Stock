import asyncio
import os
from playwright.async_api import async_playwright
from colorama import Fore, Style, init

init()

USER_DATA_DIR = "exness_browser_profile"

async def inspect_terminal():
    print(f"{Fore.CYAN}🔍 Exness Terminal Inspector{Style.RESET_ALL}")
    
    if not os.path.exists(USER_DATA_DIR):
        print(f"{Fore.RED}❌ No profile found! Run login_helper.py first.{Style.RESET_ALL}")
        return

    async with async_playwright() as p:
        print(f"{Fore.YELLOW}🚀 Launching Browser with saved profile...{Style.RESET_ALL}")
        context = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
            viewport={"width": 1280, "height": 720}
        )
        
        page = context.pages[0] if context.pages else await context.new_page()
        
        # Try to go to the dashboard first, as terminal.exness.com might be blocked/redirected
        print("Navigating to Exness Dashboard...")
        await page.goto("https://my.exness.com/accounts", timeout=60000)
        
        print(f"{Fore.GREEN}👉 Please manually click 'Trade' -> 'Exness Terminal' to open the trading chart.{Style.RESET_ALL}")
        print("Waiting 30 seconds for you to open the terminal...")
        await asyncio.sleep(30)
        
        # Find the terminal page
        terminal_page = None
        for p in context.pages:
            title = await p.title()
            print(f"Found page: {title}")
            # Prioritize the trading terminal (usually has a pair name like "EUR/USD" or "Bid")
            if "/" in title or "Bid" in title:
                terminal_page = p
                break # Found it!
            elif "Terminal" in title:
                terminal_page = p
        
        # If a new page opened, it might be the last one
        if not terminal_page and len(context.pages) > 1:
            terminal_page = context.pages[-1]
            
        if terminal_page:
            print(f"📸 Capturing content from: {await terminal_page.title()}")
            html = await terminal_page.content()
            with open("exness_terminal.html", "w") as f:
                f.write(html)
            await terminal_page.screenshot(path="exness_terminal.png")
            print(f"{Fore.GREEN}✅ Saved 'exness_terminal.html' and 'exness_terminal.png'.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Could not find Terminal page. Capturing current page...{Style.RESET_ALL}")
            html = await page.content()
            with open("exness_terminal.html", "w") as f:
                f.write(html)
            await page.screenshot(path="exness_terminal.png")
            
        print("Closing in 5 seconds...")
        await asyncio.sleep(5)
        await context.close()

if __name__ == "__main__":
    asyncio.run(inspect_terminal())
