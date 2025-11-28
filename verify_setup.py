import os
import asyncio
from dotenv import load_dotenv
from colorama import Fore, Style, init
from groq import Groq

# Initialize colorama
init()

async def verify_setup():
    print(f"{Fore.CYAN}🔍 Verifying Jarvis Environment Setup...{Style.RESET_ALL}\n")
    
    # 1. Check .env file
    if os.path.exists(".env"):
        print(f"{Fore.GREEN}✅ .env file found{Style.RESET_ALL}")
        load_dotenv()
    else:
        print(f"{Fore.RED}❌ .env file NOT found{Style.RESET_ALL}")
        return

    # 2. Check API Keys
    groq_key = os.getenv("GROQ_API_KEY_1")
    if groq_key:
        print(f"{Fore.GREEN}✅ Groq API Key found{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}❌ Groq API Key missing in .env{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}👉 Please add GROQ_API_KEY_1 to .env{Style.RESET_ALL}")
        return

    # 3. Test Groq Connection
    print(f"\n{Fore.YELLOW}Testing Groq API connection...{Style.RESET_ALL}")
    try:
        client = Groq(api_key=groq_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": "Say 'System Ready' if you can hear me.",
                }
            ],
            model="llama3-8b-8192",
        )
        response = chat_completion.choices[0].message.content
        print(f"{Fore.GREEN}✅ Groq API Connection Successful!{Style.RESET_ALL}")
        print(f"🤖 AI Response: {response}")
        
    except Exception as e:
        print(f"{Fore.RED}❌ Groq API Connection Failed{Style.RESET_ALL}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(verify_setup())
