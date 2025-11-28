import asyncpg
import logging
from config.settings import settings

logger = logging.getLogger(__name__)

class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Create a connection pool to PostgreSQL"""
        if self.pool:
            return

        try:
            self.pool = await asyncpg.create_pool(
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                host=settings.DB_HOST,
                port=settings.DB_PORT
            )
            logger.info("✅ Connected to PostgreSQL")
            await self.init_schema()
        except Exception as e:
            logger.error(f"❌ Failed to connect to PostgreSQL: {e}")
            raise

    async def disconnect(self):
        """Close the connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("✅ Disconnected from PostgreSQL")

    async def init_schema(self):
        """Initialize database schema"""
        async with self.pool.acquire() as conn:
            # Table: Logs
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    level VARCHAR(20),
                    message TEXT,
                    agent_id VARCHAR(50)
                );
            """)
            
            # Table: Signals
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    pair VARCHAR(20),
                    agent_id VARCHAR(50),
                    signal VARCHAR(10),
                    confidence FLOAT,
                    data JSONB
                );
            """)

            # Table: Trades
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    pair VARCHAR(20),
                    direction VARCHAR(10),
                    entry_price FLOAT,
                    exit_price FLOAT,
                    pnl FLOAT,
                    status VARCHAR(20)
                );
            """)
            logger.info("✅ Database schema initialized")

    async def execute(self, query, *args):
        """Execute a query (INSERT, UPDATE, DELETE)"""
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetch(self, query, *args):
        """Fetch results (SELECT)"""
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

db = Database()
