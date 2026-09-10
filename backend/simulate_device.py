import asyncio
import json
from random import random

import websockets


DEVICE_ID = "ROV-3"
TOKEN = "rov-seed-key-123"


async def send_readings() -> None:
    uri = f"ws://localhost:8000/ws/ingest/{DEVICE_ID}?token={TOKEN}"
    async with websockets.connect(uri) as websocket:
        for i in range(25):
            payload = {
                "device_id": DEVICE_ID,
                "timestamp": "2026-09-06T14:32:11Z",
                "deviation_percentage": round(7 + (random() * 30), 2),
                "schema_version": 1,
            }
            await websocket.send(json.dumps(payload))
            await websocket.recv()
            await asyncio.sleep(1.5)


if __name__ == "__main__":
    asyncio.run(send_readings())
