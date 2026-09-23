import asyncio
import json
from random import random
from datetime import datetime, timezone
import websockets


DEVICE_ID = "ROV-3"
TOKEN = "rov-seed-key-123"


async def send_readings() -> None:
    uri = f"ws://127.0.0.1:8000/ws/ingest/{DEVICE_ID}?token={TOKEN}"
    
    # Scan variables
    lat = 5.2000
    lon = -152.8000
    direction = 1
    
    while True:
        try:
            async with websockets.connect(uri, ping_interval=None) as websocket:
                print(f"Connected to {uri}")
                while True:
                    # Simulate a sweeping pattern
                    lon += 0.0002 * direction
                    if lon > -152.7980 or lon < -152.8020:
                        direction *= -1
                        lat += 0.0001 # Move up a row when reaching edge

                    # Simulate hot spots
                    dist_to_hotspot1 = ((lat - 5.2010)**2 + (lon + 152.7990)**2)**0.5
                    dist_to_hotspot2 = ((lat - 5.2005)**2 + (lon + 152.8010)**2)**0.5
                    
                    metal_prob = 0.05
                    if dist_to_hotspot1 < 0.0008:
                        metal_prob = 0.8
                    elif dist_to_hotspot2 < 0.0006:
                        metal_prob = 0.9

                    is_metal = random() < metal_prob
                    voltage = round(0.7 + random()*0.3 if is_metal else random()*0.2, 2)

                    payload = {
                        "device_id": DEVICE_ID,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "deviation_percentage": round(7 + (random() * 30), 2),
                        "schema_version": 1,
                        "distance_cm": round(150 + (random() * 100), 1),
                        "metal_detected": is_metal,
                        "metal_voltage": voltage,
                        "accel_x": round(random() * 0.1, 2),
                        "accel_y": round(random() * 0.1, 2),
                        "accel_z": round(-1.0 + random() * 0.1, 2),
                        "latitude": round(lat, 5),
                        "longitude": round(lon, 5)
                    }
                    await websocket.send(json.dumps(payload))
                    await websocket.recv()
                    await asyncio.sleep(1.0)
        except Exception as e:
            print(f"Connection dropped ({e}). Retrying in 3s...")
            await asyncio.sleep(3)


if __name__ == "__main__":
    asyncio.run(send_readings())
