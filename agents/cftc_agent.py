import asyncio
import logging
import json
import aiohttp
import re
from agents.base_agent import BaseAgent
from core.redis_client import redis_client
from datetime import datetime

logger = logging.getLogger(__name__)

class CFTCAgent(BaseAgent):
    """Agent to fetch CFTC COT data (Institutional Positioning)."""
    
    def __init__(self):
        super().__init__(name="cftc_agent", loop_interval=3600) # Check hourly
        self.url = "https://www.cftc.gov/dea/futures/deacmesf.htm"

    async def run(self):
        """Fetch and parse COT data."""
        # Only run on Fridays or if we don't have data (simplified logic: run every hour)
        # In production, check day of week: if datetime.now().weekday() != 4: return
        
        try:
            logger.info("🏛️ Fetching CFTC COT Data...")
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    if response.status != 200:
                        logger.error(f"❌ CFTC Fetch Failed: {response.status}")
                        return
                    text = await response.text()
            
            # Parse Data
            # Format is raw text, looking for "EURO FX" and "JAPANESE YEN"
            # Then extracting "NON-COMMERCIAL" section numbers
            
            data = {}
            
            # Helper to extract positions
            def extract_positions(currency_name, raw_text):
                # Find the currency section
                # This is a very basic parser for the complex CFTC format
                # We look for the currency name, then look ahead for "NON-COMMERCIAL"
                # Then grab the first two numbers (Long, Short)
                
                try:
                    # Split by currency name to find the block
                    parts = raw_text.split(currency_name)
                    if len(parts) < 2: return None
                    
                    section = parts[1]
                    # Find Non-Commercial line
                    # The format usually has "NON-COMMERCIAL" then numbers below it
                    # or in the same block. 
                    # Actually, the "Short Format" has headers then data lines.
                    # We'll use a regex to find the first line of numbers after "NON-COMMERCIAL"
                    
                    # Look for "NON-COMMERCIAL"
                    nc_split = section.split("NON-COMMERCIAL")
                    if len(nc_split) < 2: return None
                    
                    # The numbers are usually on the next few lines
                    # We look for a line with multiple integers
                    lines = nc_split[1].split('\n')
                    for line in lines[:10]: # Check first 10 lines after header
                        numbers = [int(s.replace(',', '')) for s in line.split() if s.replace(',', '').isdigit()]
                        if len(numbers) >= 2:
                            return {"long": numbers[0], "short": numbers[1]}
                    return None
                except Exception:
                    return None

            eur_pos = extract_positions("EURO FX", text)
            jpy_pos = extract_positions("JAPANESE YEN", text)
            
            if eur_pos:
                data["EUR"] = eur_pos
            if jpy_pos:
                data["JPY"] = jpy_pos
                
            if data:
                await redis_client.publish("signals:cftc", json.dumps({
                    "agent_id": self.name,
                    "positions": data,
                    "timestamp": datetime.utcnow().isoformat()
                }))
                logger.info(f"🏛️ CFTC Data Parsed: {len(data)} currencies")
            else:
                logger.warning("⚠️ CFTC Parsing Failed (No data found)")
                
        except Exception as e:
            logger.error(f"❌ CFTC Agent Error: {e}")
