import datetime
import pytz

class MarketScheduler:
    """Determines active market sessions."""
    
    def __init__(self):
        self.timezone = pytz.UTC

    def get_active_session(self):
        """Get current market session."""
        now = datetime.datetime.now(self.timezone)
        weekday = now.weekday() # 0=Mon, 6=Sun
        hour = now.hour

        # Weekend Check (Forex closed Sat/Sun)
        if weekday >= 5:
            return "CLOSED"

        # Simple Session Logic (UTC)
        # Sydney: 22:00 - 07:00
        # Tokyo: 00:00 - 09:00
        # London: 08:00 - 17:00
        # New York: 13:00 - 22:00
        
        if 8 <= hour < 17:
            return "FOREX_LONDON"
        elif 13 <= hour < 22:
            return "FOREX_NY"
        elif 0 <= hour < 9:
            return "FOREX_TOKYO"
        else:
            return "FOREX_SYDNEY" # Catch-all for late night
