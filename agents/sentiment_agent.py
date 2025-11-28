import asyncio
import json
import logging
from agents.base_agent import BaseAgent
from core.llm import groq_rotator
from core.redis_client import redis_client
from playwright.async_api import async_playwright

logger = logging.getLogger(__name__)

class SentimentAgent(BaseAgent):
    """Agent to analyze market sentiment from real news."""
    
    def __init__(self):
        super().__init__(name="sentiment_agent", loop_interval=60)

    async def fetch_headlines(self):
        """Scrape real headlines from ForexLive."""
        headlines = []
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto("https://www.forexlive.com/", timeout=30000)
                
                # Wait for articles
                await page.wait_for_selector("a.article-slot-header__link h3", timeout=10000)
                
                # Get first 3 headlines
                elements = await page.query_selector_all("a.article-slot-header__link h3")
                for i, el in enumerate(elements[:3]):
                    text = await el.text_content()
                    if text:
                        headlines.append(text.strip())
                
                await browser.close()
        except Exception as e:
            logger.error(f"❌ Scraping Error: {e}")
            
        return headlines

    async def run(self):
        """Analyze real headlines."""
        headlines = await self.fetch_headlines()
        
        if not headlines:
            logger.warning("⚠️ No headlines found.")
            return

        headline = headlines[0] # Analyze the latest one
        await self.log(f"🗞️ Analyzed Headline: {headline}")
        
        prompt = f"""
        Analyze the sentiment of this forex news headline:
        "{headline}"
        
        Return JSON only:
        {{
            "sentiment": "BULLISH|BEARISH|NEUTRAL",
            "impact": "HIGH|MEDIUM|LOW",
            "reasoning": "Brief explanation"
        }}
        """
        
        try:
            response = groq_rotator.chat_completion(prompt, system_prompt="Return JSON only.")
            response = response.replace("```json", "").replace("```", "").strip()
            analysis = json.loads(response)
            
            await self.log(f"📰 Sentiment: {analysis['sentiment']} ({analysis['impact']})")
            
            # Publish signal
            await redis_client.publish("signals:sentiment:global", {
                "agent": self.name,
                "sentiment": analysis['sentiment'],
                "impact": analysis['impact'],
                "headline": headline
            })
            
        except Exception as e:
            logger.error(f"❌ Sentiment Error: {e}")
