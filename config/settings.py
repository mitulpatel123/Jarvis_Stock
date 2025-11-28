import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # Groq
    GROQ_API_KEYS = [
        os.getenv(f"GROQ_API_KEY_{i}") for i in range(1, 51) 
        if os.getenv(f"GROQ_API_KEY_{i}")
    ]
    
    # Finnhub
    FINNHUB_API_KEYS = [
        os.getenv(f"FINNHUB_API_KEY_{i}") for i in range(1, 51) 
        if os.getenv(f"FINNHUB_API_KEY_{i}")
    ]
    
    # Alpha Vantage
    ALPHA_VANTAGE_KEYS = [
        os.getenv(f"ALPHA_VANTAGE_KEY_{i}") for i in range(1, 51) 
        if os.getenv(f"ALPHA_VANTAGE_KEY_{i}")
    ]
    
    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "jarvis_trader")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
    
    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

    # Exness
    EXNESS_EMAIL = os.getenv("EXNESS_EMAIL")
    EXNESS_PASSWORD = os.getenv("EXNESS_PASSWORD")

    # Reddit
    REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "jarvis_bot_v2")

    # FCS API
    FCS_API_KEY = os.getenv("FCS_API_KEY")

settings = Settings()
