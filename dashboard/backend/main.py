from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
import asyncio
import json
import logging
import os

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("dashboard_backend")

app = FastAPI()

# CORS (Allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Redis Connection
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def redis_listener():
    """Listen to Redis channels and broadcast to WebSockets."""
    pubsub = redis_client.pubsub()
    await pubsub.subscribe("market_status", "logs", "brain_status")
    # Pattern subscribe for signals
    await pubsub.psubscribe("signals:*")

    logger.info("🎧 Listening to Redis channels...")

    async for message in pubsub.listen():
        if message["type"] in ["message", "pmessage"]:
            channel = message["channel"]
            data = message["data"]
            
            # Construct payload
            payload = {
                "channel": channel,
                "data": data
            }
            
            # Broadcast to all connected clients
            await manager.broadcast(json.dumps(payload))

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(redis_listener())
