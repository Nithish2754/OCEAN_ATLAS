import os
import time
import json
import serial
import threading
import asyncio

ARDUINO_SERIAL_PORT = os.getenv("ARDUINO_SERIAL_PORT", "COM7")
BAUD_RATE = 115200

def start_serial_bridge(telemetry_callback_coro, loop):
    """
    Starts a background thread to read JSON telemetry from the ESP32 via USB Serial.
    telemetry_callback_coro: An async function that processes the parsed JSON payload.
    loop: The FastAPI asyncio event loop.
    """
    def serial_loop():
        print(f"[Bridge] Starting serial bridge on port {ARDUINO_SERIAL_PORT} at {BAUD_RATE} baud")
        ser = None
        while True:
            try:
                if ser is None or not ser.is_open:
                    try:
                        ser = serial.Serial(ARDUINO_SERIAL_PORT, BAUD_RATE, timeout=2)
                        print("[Bridge] Connected successfully. Waiting for data...")
                    except serial.SerialException as e:
                        print(f"[Bridge] Waiting for port {ARDUINO_SERIAL_PORT}... (Please close PlatformIO Serial Monitor if open)")
                        time.sleep(3)
                        continue

                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line:
                    print(f"[Bridge Read] {line}", flush=True)
                if not line:
                    continue
                
                # Check for debug logs
                if line.startswith("[") and not line.startswith("[{") and not line.startswith("[\""):
                    print(f"[ESP32] {line}")
                    continue

                # Parse JSON telemetry
                if line.startswith("{"):
                    try:
                        payload = json.loads(line)
                        # Dispatch to FastAPI event loop
                        asyncio.run_coroutine_threadsafe(telemetry_callback_coro(payload), loop)
                    except json.JSONDecodeError:
                        print(f"[Bridge] Ignoring invalid JSON: {line}")
                else:
                    print(f"[ESP32 RAW] {line}")
                    
            except serial.SerialException:
                print("[Bridge] Serial connection lost. Reconnecting in 5 seconds...")
                if ser:
                    try:
                        ser.close()
                    except:
                        pass
                ser = None
                time.sleep(5)
            except Exception as e:
                print(f"[Bridge] Unexpected error: {e}")
                time.sleep(1)
                
    thread = threading.Thread(target=serial_loop, daemon=True, name="SerialBridgeThread")
    thread.start()
