import logging
from groq import Groq
from config.settings import settings

logger = logging.getLogger(__name__)

class GroqRotator:
    """Rotates through multiple Groq API keys to maximize free usage."""
    
    def __init__(self):
        self.keys = settings.GROQ_API_KEYS
        if not self.keys:
            logger.warning("⚠️ No Groq API keys found in settings!")
        
        self.current_index = 0
        self.clients = [Groq(api_key=key) for key in self.keys]
        logger.info(f"✅ Loaded {len(self.keys)} Groq API keys")

    def get_client(self):
        """Get the next Groq client in rotation."""
        if not self.clients:
            raise ValueError("No Groq clients available")
            
        client = self.clients[self.current_index]
        # Rotate index
        self.current_index = (self.current_index + 1) % len(self.clients)
        return client

    def chat_completion(self, prompt, model="llama-3.1-8b-instant", system_prompt="You are a helpful AI assistant."):
        """Helper for simple chat completion."""
        client = self.get_client()
        
        try:
            completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                model=model,
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.error(f"❌ Groq API Error: {e}")
            # Optional: Retry with next key?
            raise e

groq_rotator = GroqRotator()
