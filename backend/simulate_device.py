import asyncio
import json
from random import random

import websockets


DEVICE_ID = "ROV-3"
TOKEN = "rov-seed-key-123"


async def send_readings() -> None:
    uri = f"ws://localhost:8000/ws/ingest/{DEVICE_ID}?token={TOKEN}"
    async with websockets.connect(uri) as websocket:
        while True:
            payload = {
                "device_id": DEVICE_ID,
                "timestamp": "2026-09-06T14:32:11Z",
                "deviation_percentage": round(7 + (random() * 30), 2),
                "schema_version": 1,
                "distance_cm": round(150 + (random() * 100), 1),
                "metal_detected": random() > 0.8,
                "metal_voltage": round(random(), 2),
                "accel_x": round(random() * 0.1, 2),
                "accel_y": round(random() * 0.1, 2),
                "accel_z": round(-1.0 + random() * 0.1, 2),
                "latitude": 5.2,
                "longitude": -152.8
            }
            await websocket.send(json.dumps(payload))
            await websocket.recv()
            await asyncio.sleep(1.5)


if __name__ == "__main__":
    asyncio.run(send_readings())
