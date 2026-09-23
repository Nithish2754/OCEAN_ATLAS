# Ocean Atlas 🌊

Ocean Atlas is a modern, event-driven, three-tier IoT system designed for real-time telemetry ingestion, processing, and visualization of sub-sea environments. It is engineered to track underwater remotely operated vehicles (ROVs) and map ocean floor metal distributions in real-time.

## 🏗️ Architecture

The software architecture is divided into three main layers:

1. **Edge Tier (Firmware & Hardware Integration)**
   - Developed in C++ on the **ESP32** microcontroller platform.
   - Interfaces directly with environmental hardware including ultrasonic (HC-SR04), inertial (MPU6050), and electromagnetic sensors.
   - Handles low-level signal processing and aggregates high-frequency analog and digital signals.
   - Packages telemetry into structured payloads for transmission to the middleware via local WebSockets or serial bridging.

2. **Middleware Tier (Backend & Message Broker)**
   - Engineered as a high-throughput Python server utilizing the **FastAPI** framework and Uvicorn.
   - Functions as an asynchronous message broker to ingest raw telemetry streams with near-zero latency.
   - Executes anomaly detection algorithms and manages state persistence for accurate spatial mapping.
   - Abstracts hardware dependencies by providing robust simulation modules (`simulate_device.py`) and automated connection keepalive management.

3. **Presentation Tier (Frontend & Data Visualization)**
   - Built as a Single Page Application utilizing the **React** library and **Vite**.
   - Establishes a persistent, zero-polling WebSocket connection to the middleware for real-time state delivery.
   - Utilizes WebGL and `@react-three/fiber` to render dynamic 3D spatial orientation models based on inertial data.
   - Implements the HTML5 Canvas API to compute and render continuous radial density heatmaps (Metal Presence) without degrading UI thread performance.

---

## 🚀 Getting Started

### Prerequisites
- [Node.js](https://nodejs.org/) (v18+)
- [Python 3.10+](https://www.python.org/)
- [PlatformIO](https://platformio.org/) (for ESP32 flashing)

### Running the Project (Simulation Mode)

If you don't have the physical ROV hardware plugged in, you can run the entire software stack in simulation mode using the provided startup script. This will launch the backend, the frontend, and a device simulator that feeds fake coordinate and metal detection data to generate the live heatmap.

**On Windows:**
Simply double-click the `START_ALL_FAKE.bat` file in the root directory. 
Alternatively, run it via command prompt:
```cmd
.\START_ALL_FAKE.bat
```

### Running the Project (Hardware Mode)

If you have the ESP32 hooked up via USB:
1. Edit the `START_ALL.bat` to match your COM port (default is COM7).
2. Run `START_ALL.bat`. This will flash the ESP32, open the serial monitor, and launch the backend and frontend servers.

### Accessing the Dashboard

Once the services are running, open your browser and navigate to:
**http://localhost:5173/**

---

## 🛠️ Technology Stack
- **Frontend:** React 19, Vite, TailwindCSS, React Three Fiber, Recharts, Lucide Icons.
- **Backend:** Python, FastAPI, Uvicorn, WebSockets.
- **Firmware:** C++, PlatformIO, ESP32.
