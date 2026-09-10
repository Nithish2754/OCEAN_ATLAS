import os
import sys
import time
import requests
import serial

# Configuration
ARDUINO_SERIAL_PORT = os.getenv("ARDUINO_SERIAL_PORT", "COM7")
BAUD_RATE = 115200
API_URL = os.getenv("BACKEND_HOST", "http://127.0.0.1:8000") + "/api/depth"
DEVICE_ID = "ROV-3"

def main():
    print(f"[Bridge] Starting serial bridge on port {ARDUINO_SERIAL_PORT} at {BAUD_RATE} baud")
    
    try:
        ser = serial.Serial(ARDUINO_SERIAL_PORT, BAUD_RATE, timeout=2)
    except serial.SerialException as e:
        print(f"[Bridge] ERROR: Could not open serial port {ARDUINO_SERIAL_PORT}: {e}")
        print("[Bridge] Make sure the Arduino is connected, and the port is correct.")
        sys.exit(1)

    print("[Bridge] Connected successfully. Waiting for data...")

    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue

            print(f"[Serial] {line}")

            if line.startswith("DEPTH:"):
                value_str = line.split("DEPTH:")[1].strip()
                
                # Check for "No echo / out of range"
                if "No echo" in value_str or "out of range" in value_str:
                    print("[Bridge] Out of range reading skipped.")
                    continue
                
                try:
                    depth_cm = float(value_str)
                    if depth_cm < 0:
                        raise ValueError("Negative depth")
                        
                    print(f"[Bridge] Sending depth: {depth_cm} cm")
                    
                    payload = {
                        "device_id": DEVICE_ID,
                        "depth_cm": depth_cm
                    }
                    
                    response = requests.post(API_URL, json=payload, timeout=2)
                    if response.status_code != 200:
                        print(f"[Bridge] API Error: {response.status_code} {response.text}")
                        
                except ValueError:
                    print(f"[Bridge] Invalid numeric depth value: {value_str}")
                except requests.RequestException as e:
                    print(f"[Bridge] Connection to FastAPI failed: {e}")

        except serial.SerialException:
            print("[Bridge] Serial connection lost. Attempting to reconnect in 5 seconds...")
            ser.close()
            time.sleep(5)
            try:
                ser = serial.Serial(ARDUINO_SERIAL_PORT, BAUD_RATE, timeout=2)
                print("[Bridge] Reconnected.")
            except:
                pass
        except KeyboardInterrupt:
            print("\n[Bridge] Shutting down.")
            ser.close()
            break

if __name__ == "__main__":
    main()
