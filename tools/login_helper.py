import asyncio
import os
from playwright.async_api import async_playwright
from colorama import Fore, Style, init

init()

# Use a real directory for the profile
USER_DATA_DIR = "exness_browser_profile"

async def login_helper():
    print(f"{Fore.CYAN}🔐 Exness Login Helper (Stealth Mode){Style.RESET_ALL}")
    print("This script will open a Chrome window with a persistent profile.")
    print("1. Log in manually.")
    print("2. If Cloudflare loops, try refreshing or clicking the extension button if available.")
    print("3. Once on the dashboard, close the browser.")
    
    # Create dir if not exists
    if not os.path.exists(USER_DATA_DIR):
        os.makedirs(USER_DATA_DIR)

    async with async_playwright() as p:
        # Launch persistent context which saves cookies/storage automatically
        # and looks more like a real browser
        browser = await p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport=None, # Let window decide
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars"
            ],
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        
        page = browser.pages[0] if browser.pages else await browser.new_page()

        print(f"{Fore.YELLOW}🚀 Opening Exness...{Style.RESET_ALL}")
        await page.goto("https://www.exness.com/", timeout=60000)

        print(f"{Fore.GREEN}👉 Please log in manually now.{Style.RESET_ALL}")
        print("Waiting for you to close the browser...")

        # Wait for the browser to be closed by the user
        try:
            # We monitor if the context is closed
            while browser.pages:
                await asyncio.sleep(1)
        except Exception:
            pass

        print(f"\n{Fore.GREEN}✅ Profile saved to '{USER_DATA_DIR}'!{Style.RESET_ALL}")
        print("You can now run the execution agent.")

if __name__ == "__main__":
    asyncio.run(login_helper())
