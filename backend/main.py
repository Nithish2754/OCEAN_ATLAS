from __future__ import annotations

import asyncio
import base64
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ValidationError, field_validator


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

class SensorReading(BaseModel):
    """
    Unified telemetry model accepted from all ROV devices.

    Legacy fields (deviation_percentage, schema_version) are preserved so
    existing ROV-3 / ROV-1 firmware continues to work without changes.

    New hardware fields (metal_detected, metal_voltage, distance_cm, accel_*)
    are all optional so the validator never rejects old-format messages.
    """
    device_id: str = Field(..., min_length=1)
    timestamp: str | None = None
    schema_version: int = 1

    # Legacy EM-deviation field – kept for backward compatibility
    deviation_percentage: float = Field(default=0.0, ge=0, le=1000)

    # ── Real ESP32 hardware fields ──────────────────────────────────────────
    # HC-SR04 ultrasonic distance
    distance_cm: float | None = None

    # Metal detector (GPIO 34 ADC)
    metal_detected: bool | None = None
    metal_voltage: float | None = None

    # MPU6050 acceleration (converted to g-force on device)
    accel_x: float | None = None
    accel_y: float | None = None
    accel_z: float | None = None

    # Future GPS positioning – kept null until GPS module is added
    latitude: float | None = None
    longitude: float | None = None


class DepthReading(BaseModel):
    device_id: str = Field(..., min_length=1)
    depth_cm: float
    timestamp: str | None = None

    @field_validator("timestamp")
    @classmethod
    def stamp_if_missing(cls, value: str | None) -> str | None:
        if value is not None:
            return value
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

APP_ORIGINS = [
    "http://localhost:4173",
    "http://localhost:4174",
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:4173",
    "http://127.0.0.1:4174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

app = FastAPI(title="OceanAtlas Live Data API")
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Device authentication tokens
# ---------------------------------------------------------------------------

DEVICE_TOKENS = {
    # Legacy seed tokens
    "rov-seed-key-123": "ROV-3",
    "rov-seed-key-456": "ROV-1",
    # NodeMCU ESP32-S hardware token
    "rov-esp32-key-001": "ROV-01",
}


# ---------------------------------------------------------------------------
# WebSocket connection managers
# ---------------------------------------------------------------------------

class LiveConnectionManager:
    """Manages frontend /ws/live dashboard clients and device /ws/ingest clients."""

    def __init__(self) -> None:
        self.frontend_clients: set[WebSocket] = set()
        self.device_clients: dict[str, WebSocket] = {}

    async def connect_frontend(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.frontend_clients.add(websocket)

    async def connect_device(self, device_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self.device_clients[device_id] = websocket

    def disconnect_frontend(self, websocket: WebSocket) -> None:
        self.frontend_clients.discard(websocket)

    def disconnect_device(self, device_id: str) -> None:
        self.device_clients.pop(device_id, None)

    async def broadcast(self, message: dict[str, Any]) -> None:
        dead_clients: set[WebSocket] = set()
        for client in list(self.frontend_clients):
            try:
                await client.send_json(message)
            except RuntimeError:
                dead_clients.add(client)
        for client in dead_clients:
            self.frontend_clients.discard(client)

    async def send_device_command(self, device_id: str, command: dict[str, Any]) -> None:
        socket = self.device_clients.get(device_id)
        if socket is None:
            return
        try:
            await socket.send_json(command)
        except RuntimeError:
            self.device_clients.pop(device_id, None)


manager = LiveConnectionManager()

# Separate client sets for specialised channels
depth_clients: set[WebSocket] = set()
sensor_clients: set[WebSocket] = set()  # NEW: full telemetry for SensorTelemetryPanel


# ---------------------------------------------------------------------------
# In-memory stores
# ---------------------------------------------------------------------------

readings_store: list[dict[str, Any]] = []
activity_store: list[dict[str, Any]] = []
latest_map = {
    "map_id": "CCZ-04",
    "confidence": 0.87,
    "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
}

# Latest telemetry per device – sent to newly connected /ws/sensors clients
latest_telemetry: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def decode_base64_url_segment(segment: str) -> dict[str, Any]:
    padded = segment + "=" * (-len(segment) % 4)
    payload = base64.urlsafe_b64decode(padded.encode("utf-8"))
    return json.loads(payload.decode("utf-8"))


def validate_user_token(token: str | None) -> bool:
    if not token:
        return False
    parts = token.split(".")
    if len(parts) != 3:
        return False
    try:
        payload = decode_base64_url_segment(parts[1])
    except Exception:
        return False
    exp = payload.get("exp")
    if not exp:
        return False
    return int(exp) > int(datetime.now(timezone.utc).timestamp())


def normalize_timestamp(value: str | None) -> str:
    if value:
        return value
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def derive_anomaly_confidence(deviation_percentage: float) -> float:
    if deviation_percentage >= 30:
        return 0.94
    if deviation_percentage >= 20:
        return 0.76
    if deviation_percentage >= 15:
        return 0.58
    if deviation_percentage >= 8:
        return 0.35
    return 0.12


async def broadcast_to_sensor_clients(message: dict[str, Any]) -> None:
    """Broadcast a telemetry message to all /ws/sensors subscribers."""
    dead: set[WebSocket] = set()
    for client in list(sensor_clients):
        try:
            await client.send_json(message)
        except RuntimeError:
            dead.add(client)
    for client in dead:
        sensor_clients.discard(client)


async def broadcast_depth_to_depth_clients(device_id: str, distance_cm: float, ts: str) -> None:
    """Forward real distance_cm readings to /ws/depth so LiveDepthChart updates automatically."""
    data = {
        "type": "depth",
        "device_id": device_id,
        "depth_cm": distance_cm,
        "timestamp": ts,
    }
    dead: set[WebSocket] = set()
    for client in list(depth_clients):
        try:
            await client.send_json(data)
        except Exception:
            dead.add(client)
    for client in dead:
        depth_clients.discard(client)


def process_reading(reading: SensorReading) -> dict[str, Any]:
    """
    Process a unified SensorReading.
    Legacy deviation_percentage logic is preserved.
    New hardware fields are stored and forwarded separately.
    """
    deviation = float(reading.deviation_percentage)
    threshold = 15.0
    anomaly_flag = deviation > threshold
    confidence = derive_anomaly_confidence(deviation)
    device_state = "online"

    # Build activity event message
    if reading.metal_detected is True:
        event_message = (
            f"⚠ Metal detected by {reading.device_id} — "
            f"voltage {reading.metal_voltage:.2f} V"
            if reading.metal_voltage is not None
            else f"⚠ Metal detected by {reading.device_id}"
        )
        activity_type = "alert"
    elif anomaly_flag:
        event_message = (
            f"Deviation of {deviation:.1f}% flagged on {reading.device_id} — "
            "possible metal-rich zone"
        )
        activity_type = "alert"
    else:
        event_message = (
            f"Telemetry from {reading.device_id} — "
            f"distance {reading.distance_cm:.1f} cm"
            if reading.distance_cm is not None
            else f"Deviation of {deviation:.1f}% recorded on {reading.device_id} — "
            "survey corridor remains stable"
        )
        activity_type = "success"

    activity_entry = {
        "time": datetime.now(timezone.utc).strftime("%H:%M"),
        "event": event_message,
        "type": activity_type,
    }
    activity_store.insert(0, activity_entry)
    if len(activity_store) > 20:
        activity_store.pop()

    device_record = {
        "device_id": reading.device_id,
        "status": device_state,
        "last_seen": normalize_timestamp(reading.timestamp),
        "deviation_percentage": deviation,
        "anomaly_flag": anomaly_flag,
        "anomaly_confidence": confidence,
    }
    for index, item in enumerate(readings_store):
        if item.get("device_id") == reading.device_id:
            readings_store[index] = device_record
            break
    else:
        readings_store.append(device_record)

    payload = {
        "device_id": reading.device_id,
        "timestamp": normalize_timestamp(reading.timestamp),
        "deviation_percentage": deviation,
        "anomaly_flag": anomaly_flag,
        "anomaly_confidence": confidence,
        "fine_scan_mode": anomaly_flag and deviation >= 20,
        "schema_version": reading.schema_version,
        "message": event_message,
        # New hardware fields (may be None for legacy devices)
        "metal_detected": reading.metal_detected,
        "metal_voltage": reading.metal_voltage,
        "distance_cm": reading.distance_cm,
        "accel_x": reading.accel_x,
        "accel_y": reading.accel_y,
        "accel_z": reading.accel_z,
        "latitude": reading.latitude,
        "longitude": reading.longitude,
    }
    return payload


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/depth")
async def ingest_depth(reading: DepthReading):
    if reading.depth_cm < 0:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Depth cannot be negative")

    print(f"[Depth] {reading.device_id} -> {reading.depth_cm} cm")

    data = {
        "type": "depth",
        "device_id": reading.device_id,
        "depth_cm": reading.depth_cm,
        "timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S")
    }

    dead_clients = set()
    for client in list(depth_clients):
        try:
            await client.send_json(data)
        except Exception:
            dead_clients.add(client)

    for c in dead_clients:
        depth_clients.discard(c)

    return {"status": "ok", "forwarded": len(depth_clients)}


@app.get("/api/dashboard/summary")
async def get_dashboard_summary() -> dict[str, Any]:
    active_devices = [item for item in readings_store if item.get("status") == "online"]
    anomaly_count = sum(1 for item in readings_store if item.get("anomaly_flag"))
    return {
        "active_surveys": max(1, len(active_devices)),
        "anomaly_count": anomaly_count,
        "last_map": latest_map.get("map_id", "CCZ-04"),
        "system_status": "Nominal" if anomaly_count < 10 else "Review",
    }


@app.get("/api/devices")
async def get_devices() -> dict[str, list[dict[str, Any]]]:
    devices = [
        {
            "device_id": item.get("device_id"),
            "status": item.get("status", "offline"),
            "last_seen": item.get("last_seen"),
            "deviation_percentage": item.get("deviation_percentage", 0),
        }
        for item in readings_store
    ]
    return {"devices": devices}


@app.get("/api/activity")
async def get_activity(limit: int = 20) -> dict[str, list[dict[str, Any]]]:
    return {"activity": activity_store[:limit]}


@app.get("/api/maps/latest")
async def get_latest_map() -> dict[str, Any]:
    return latest_map


# ---------------------------------------------------------------------------
# WebSocket endpoints
# ---------------------------------------------------------------------------

@app.websocket("/ws/depth")
async def depth_websocket(websocket: WebSocket):
    await websocket.accept()
    depth_clients.add(websocket)
    print("[WebSocket] Client connected for live depth data")
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("[WebSocket] Client disconnected from live depth data")
        depth_clients.discard(websocket)


@app.websocket("/ws/sensors")
async def sensors_websocket(websocket: WebSocket):
    """
    Read-only broadcast channel for the SensorTelemetryPanel.
    No authentication required – data is non-sensitive telemetry.
    On connect, immediately replay the latest reading for each connected device.
    """
    await websocket.accept()
    sensor_clients.add(websocket)
    print("[WebSocket] Frontend connected to /ws/sensors")

    # Send cached latest telemetry immediately so the panel isn't blank on load
    for device_id, telemetry in latest_telemetry.items():
        try:
            await websocket.send_json(telemetry)
        except RuntimeError:
            break

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        print("[WebSocket] Frontend disconnected from /ws/sensors")
        sensor_clients.discard(websocket)


@app.websocket("/ws/live")
async def live_dashboard_socket(websocket: WebSocket, token: str | None = None):
    if not validate_user_token(token):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect_frontend(websocket)
    try:
        summary = await get_dashboard_summary()
        devices = await get_devices()
        active = await get_activity(limit=6)
        await websocket.send_json(
            {
                "type": "state",
                "summary": summary,
                "devices": devices["devices"],
                "activity": active["activity"],
            }
        )

        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect_frontend(websocket)


@app.websocket("/ws/ingest/{device_id}")
async def ingest_socket(websocket: WebSocket, device_id: str, token: str | None = None):
    if token not in DEVICE_TOKENS or DEVICE_TOKENS[token] != device_id:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect_device(device_id, websocket)

    # Notify frontend that this device came online
    online_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    await manager.broadcast({
        "type": "device_status",
        "device_id": device_id,
        "online": True,
        "timestamp": online_ts,
    })
    await broadcast_to_sensor_clients({
        "type": "device_status",
        "device_id": device_id,
        "online": True,
        "timestamp": online_ts,
    })
    print(f"[Ingest] Device {device_id} connected")

    try:
        while True:
            try:
                raw_message = await asyncio.wait_for(websocket.receive_text(), timeout=25)
            except asyncio.TimeoutError:
                await websocket.send_json({
                    "type": "heartbeat",
                    "device_id": device_id,
                    "status": "ping",
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                })
                continue

            if raw_message == "ping":
                await websocket.send_json({
                    "type": "pong",
                    "device_id": device_id,
                    "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                })
                continue

            if raw_message == "pong":
                continue

            try:
                incoming = json.loads(raw_message)
                reading = SensorReading.model_validate(incoming)
            except (json.JSONDecodeError, ValidationError) as e:
                print(f"[Ingest] Rejected payload from {device_id}: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": "Malformed payload rejected",
                })
                continue

            processed = process_reading(reading)
            ts = processed["timestamp"]
            ts_short = ts[11:19] if len(ts) >= 19 else ts  # HH:MM:SS

            # ── Broadcast to /ws/live (existing dashboard summary) ───────────
            await manager.broadcast({
                "type": "reading",
                "device_id": processed["device_id"],
                "anomaly": processed["anomaly_flag"],
                "anomaly_confidence": processed["anomaly_confidence"],
                "timestamp": ts,
                "message": processed["message"],
                "anomaly_count": sum(1 for item in readings_store if item.get("anomaly_flag")),
                "last_map": latest_map.get("map_id", "CCZ-04"),
                "system_status": "Nominal" if sum(1 for item in readings_store if item.get("anomaly_flag")) < 10 else "Review",
            })

            # ── Forward distance_cm to /ws/depth → LiveDepthChart ───────────
            if reading.distance_cm is not None and reading.distance_cm >= 0:
                await broadcast_depth_to_depth_clients(device_id, reading.distance_cm, ts_short)

            # ── Broadcast full telemetry to /ws/sensors → SensorTelemetryPanel
            telemetry_msg = {
                "type": "telemetry",
                "device_id": processed["device_id"],
                "timestamp": ts,
                "metal_detected": processed["metal_detected"],
                "metal_voltage": processed["metal_voltage"],
                "distance_cm": processed["distance_cm"],
                "accel_x": processed["accel_x"],
                "accel_y": processed["accel_y"],
                "accel_z": processed["accel_z"],
                "latitude": processed["latitude"],
                "longitude": processed["longitude"],
            }
            # Cache for new /ws/sensors clients that connect after device is online
            latest_telemetry[device_id] = telemetry_msg
            await broadcast_to_sensor_clients(telemetry_msg)

            # ── Fine-scan command ────────────────────────────────────────────
            if processed["fine_scan_mode"]:
                await manager.send_device_command(device_id, {
                    "type": "scan_mode",
                    "device_id": device_id,
                    "mode": "fine_scan",
                    "confidence": processed["anomaly_confidence"],
                    "timestamp": ts,
                })

            await websocket.send_json({
                "type": "ack",
                "device_id": device_id,
                "accepted": True,
                "reading": processed,
            })

    except WebSocketDisconnect:
        manager.disconnect_device(device_id)
        offline_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        offline_msg = {
            "type": "device_status",
            "device_id": device_id,
            "online": False,
            "timestamp": offline_ts,
        }
        await manager.broadcast(offline_msg)
        await broadcast_to_sensor_clients(offline_msg)
        # Remove from cache so reconnecting clients know device is offline
        latest_telemetry.pop(device_id, None)
        print(f"[Ingest] Device {device_id} disconnected")


# ---------------------------------------------------------------------------
# Startup seed data
# ---------------------------------------------------------------------------

@app.on_event("startup")
async def bootstrap_seed_data() -> None:
    seed_activity = [
        {"time": "14:32", "event": "ROV-3 fine scan completed — Zone CCZ-04-B", "type": "success"},
        {"time": "13:15", "event": "EM anomaly flagged at 5°12'N, 152°48'W — Mn nodule signature", "type": "alert"},
        {"time": "11:48", "event": "Metal-Priority Map CCZ-04 exported to research portal", "type": "info"},
    ]
    activity_store.extend(seed_activity)
    readings_store.extend([
        {"device_id": "ROV-3", "status": "online", "last_seen": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviation_percentage": 18.4, "anomaly_flag": True, "anomaly_confidence": 0.76},
        {"device_id": "ROV-1", "status": "online", "last_seen": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "deviation_percentage": 9.2, "anomaly_flag": False, "anomaly_confidence": 0.12},
    ])
