/**
 * SensorTelemetryPanel.jsx
 *
 * Real-time hardware sensor display for Ocean Atlas dashboard.
 * Connects to /ws/sensors (no token needed – read-only broadcast).
 *
 * Displays:
 *  1. Metal Detection Status  – 🔴 METAL DETECTED / 🟢 CLEAR
 *  2. Metal Signal Voltage    – raw ADC voltage in V
 *  3. Distance / Depth        – distance_cm from HC-SR04
 *  4. MPU6050 Acceleration    – X / Y / Z in g
 *  5. Device Connection       – ROV-01 online / offline with timeout
 */

import { useEffect, useRef, useState } from 'react';
import { Cpu, Radar, Waves, Zap, Activity } from 'lucide-react';
import ROV3DViewer from './ROV3DViewer';
import MetalHeatmap from './MetalHeatmap';

const OFFLINE_TIMEOUT_MS = 6000;   // mark ROV offline if no data for 6 s
const MAX_WS_RETRY_MS    = 5000;   // WebSocket reconnect interval

const backendHost =
  window.location.hostname === 'localhost' ? 'localhost' : window.location.hostname;
const WS_URL = `ws://${backendHost}:8000/ws/sensors`;

export default function SensorTelemetryPanel() {
  // ── Sensor state ──────────────────────────────────────────────────────────
  const [metalDetected,  setMetalDetected]  = useState(null);   // null = no data yet
  const [metalVoltage,   setMetalVoltage]   = useState(null);
  const [distanceCm,     setDistanceCm]     = useState(null);
  const [accel,          setAccel]          = useState({ x: null, y: null, z: null });
  const [deviceId,       setDeviceId]       = useState('ROV-01');
  const [rovOnline,      setRovOnline]      = useState(false);
  const [lastSeen,       setLastSeen]       = useState(null);
  const [wsStatus,       setWsStatus]       = useState('Connecting');

  // Metal detection event tracking (only fire on false→true edge)
  const [metalAlertTime, setMetalAlertTime] = useState(null);
  const [detectCount, setDetectCount] = useState(0);
  const prevMetalRef     = useRef(null);

  const [heatmapPoints,  setHeatmapPoints]  = useState([]);

  const wsRef            = useRef(null);
  const retryRef         = useRef(null);
  const offlineTimerRef  = useRef(null);

  // ── MOCK DATA FOR 3D VIEWER TESTING ───────────────────────────────────────
  const MOCK_3D = false; // Set to true to test 3D Viewer

  useEffect(() => {
    if (!MOCK_3D) return;
    
    let t = 0;
    const interval = setInterval(() => {
      t += 0.05;
      
      // Simulate an ROV swaying in the water
      const pitchSway = Math.sin(t) * 0.4;
      const rollSway = Math.cos(t * 0.6) * 0.4;
      
      setAccel({
        x: pitchSway,
        y: rollSway,
        z: 1.0
      });
      setWsStatus('Connected');
      setRovOnline(true);
    }, 50);

    return () => clearInterval(interval);
  }, []);
  // ──────────────────────────────────────────────────────────────────────────

  // ── Offline watchdog ──────────────────────────────────────────────────────
  const resetOfflineTimer = () => {
    if (offlineTimerRef.current) clearTimeout(offlineTimerRef.current);
    offlineTimerRef.current = setTimeout(() => {
      setRovOnline(false);
    }, OFFLINE_TIMEOUT_MS);
  };

  // ── WebSocket connection ──────────────────────────────────────────────────
  useEffect(() => {
    const connect = () => {
      if (wsRef.current?.readyState === WebSocket.OPEN) return;

      setWsStatus('Connecting');
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = () => {
        setWsStatus('Connected');
      };

      ws.onmessage = (event) => {
        try {
          const msg = JSON.parse(event.data);

          if (msg.type === 'device_status') {
            setDeviceId(msg.device_id ?? 'ROV-01');
            setRovOnline(msg.online === true);
            if (!msg.online) {
              // Device disconnected – clear sensor data
              if (offlineTimerRef.current) clearTimeout(offlineTimerRef.current);
            }
            return;
          }

          if (msg.type === 'telemetry') {
            setDeviceId(msg.device_id ?? 'ROV-01');
            setRovOnline(true);
            setLastSeen(new Date());
            resetOfflineTimer();

            // ── Metal detection ─────────────────────────────────────────────
            const detected = msg.metal_detected;
            setMetalDetected(detected);
            if (detected === true && prevMetalRef.current !== true) {
              // Rising edge: false → true
              setMetalAlertTime(new Date());
              setDetectCount(prev => prev + 1);
            }
            prevMetalRef.current = detected;

            setMetalVoltage(msg.metal_voltage   ?? null);
            setDistanceCm( msg.distance_cm      ?? null);
            setAccel({
              x: msg.accel_x ?? null,
              y: msg.accel_y ?? null,
              z: msg.accel_z ?? null,
            });

            if (msg.latitude !== undefined && msg.longitude !== undefined) {
              setHeatmapPoints(prev => {
                const newPoint = {
                  lat: msg.latitude,
                  lon: msg.longitude,
                  voltage: msg.metal_voltage ?? 0,
                  detected: msg.metal_detected ?? false
                };
                return [...prev.slice(-399), newPoint]; // Keep last 400 points
              });
            }
          }
        } catch {
          // ignore malformed frames
        }
      };

      ws.onclose = () => {
        setWsStatus('Disconnected');
        retryRef.current = setTimeout(connect, MAX_WS_RETRY_MS);
      };

      ws.onerror = () => {
        setWsStatus('Error');
      };
    };

    connect();

    return () => {
      if (retryRef.current)   clearTimeout(retryRef.current);
      if (offlineTimerRef.current) clearTimeout(offlineTimerRef.current);
      wsRef.current?.close();
    };
  }, []);

  // ── Derived helpers ───────────────────────────────────────────────────────
  const fmt = (val, decimals = 2) =>
    val === null || val === undefined ? '—' : Number(val).toFixed(decimals);

  const metalLabel = metalDetected === null
    ? '— Awaiting data'
    : metalDetected
      ? `🔴 METAL DETECTED`
      : '🟢 CLEAR';

  const distLabel = distanceCm === null
    ? '—'
    : distanceCm < 0
      ? 'Out of range'
      : `${fmt(distanceCm, 1)} cm`;

  const rovStatusColor  = rovOnline ? '#6ee7b7' : '#ff5d73';
  const rovStatusLabel  = rovOnline ? '🟢 Online' : '🔴 Offline';
  const metalCardClass  = `telemetry-card glass-card rounded-2xl ${metalDetected ? 'telemetry-card--alert' : ''}`;

  return (
    <div className="dashboard-panel glass-card rounded-2xl col-span-full mb-6" id="sensor-telemetry-panel">
      {/* ── Panel header ── */}
      <div className="dashboard-panel-header">
        <h2
          className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2"
          style={{ fontFamily: "'Space Grotesk', sans-serif" }}
        >
          <Radar size={18} className="text-[var(--accent-cyan)]" />
          Live Hardware Telemetry
        </h2>

        <div className="flex items-center gap-3">
          {/* Metal alert badge – only shows on detection event */}
          {metalAlertTime && (
            <div
              className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold animate-pulse"
              style={{
                background: '#ff5d7322',
                border: '1px solid #ff5d7360',
                color: '#ff5d73',
              }}
            >
              ⚠ Metal at {metalAlertTime.toLocaleTimeString()}
            </div>
          )}

          {/* WebSocket status */}
          <div
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium"
            style={{
              background: wsStatus === 'Connected' ? '#6ee7b714' : '#ff5d7314',
              border: `1px solid ${wsStatus === 'Connected' ? '#6ee7b740' : '#ff5d7340'}`,
              color:   wsStatus === 'Connected' ? '#6ee7b7'   : '#ff5d73',
            }}
          >
            <span
              className={`w-1.5 h-1.5 rounded-full bg-current ${wsStatus === 'Connected' ? 'animate-pulse' : ''}`}
            />
            {wsStatus}
          </div>
        </div>
      </div>

      {/* ── Telemetry card grid ── */}
      <div className="telemetry-grid">

        {/* 1. Metal Detection Status */}
        <div className={metalCardClass} id="metal-status-card">
          <div className="telemetry-card-icon" style={{ color: metalDetected ? '#ff5d73' : '#6ee7b7' }}>
            <Zap size={20} />
          </div>
          <div className="telemetry-card-label">Metal Status</div>
          <div
            className="telemetry-card-value"
            style={{
              color: metalDetected === null
                ? 'var(--text-muted)'
                : metalDetected
                  ? '#ff5d73'
                  : '#6ee7b7',
              fontSize: metalDetected ? '1rem' : '1.1rem',
            }}
          >
            {metalLabel}
          </div>
          {metalAlertTime && (
            <div className="telemetry-card-sub" style={{ color: '#ff5d7399' }}>
              Last detect: {metalAlertTime.toLocaleTimeString()}
            </div>
          )}
        </div>

        {/* 2. Distance / Depth */}
        <div className="telemetry-card glass-card rounded-2xl" id="distance-card">
          <div className="telemetry-card-icon" style={{ color: 'var(--accent-cyan)' }}>
            <Waves size={20} />
          </div>
          <div className="telemetry-card-label">Depth / Distance</div>
          <div className="telemetry-card-value" style={{ color: 'var(--accent-cyan)' }}>
            {distLabel}
          </div>
          <div className="telemetry-card-sub">HC-SR04 ultrasonic</div>
        </div>

        {/* 3. MPU6050 Acceleration */}
        <div className="telemetry-card glass-card rounded-2xl" id="imu-card">
          <div className="telemetry-card-icon" style={{ color: '#a78bfa' }}>
            <Cpu size={20} />
          </div>
          <div className="telemetry-card-label">Acceleration (MPU6050)</div>
          <div className="telemetry-accel" id="imu-values">
            <div>
              <span className="telemetry-axis">X</span>
              <span style={{ color: '#a78bfa' }}>{fmt(accel.x)} g</span>
            </div>
            <div>
              <span className="telemetry-axis">Y</span>
              <span style={{ color: '#a78bfa' }}>{fmt(accel.y)} g</span>
            </div>
            <div>
              <span className="telemetry-axis">Z</span>
              <span style={{ color: '#a78bfa' }}>{fmt(accel.z)} g</span>
            </div>
          </div>
        </div>

        {/* 4. Device Status */}
        <div className="telemetry-card glass-card rounded-2xl" id="device-status-card">
          <div
            className="telemetry-card-icon"
            style={{ color: rovStatusColor }}
          >
            <span className={`w-3 h-3 rounded-full inline-block ${rovOnline ? 'animate-pulse' : ''}`}
                  style={{ background: rovStatusColor }} />
          </div>
          <div className="telemetry-card-label">{deviceId}</div>
          <div className="telemetry-card-value" style={{ color: rovStatusColor }}>
            {rovStatusLabel}
          </div>
          <div className="telemetry-card-sub">
            {lastSeen
              ? `Last data: ${lastSeen.toLocaleTimeString()}`
              : 'No data received yet'}
          </div>
        </div>

      </div>

      {/* ── 3D Attitude Viewer ── */}
      <ROV3DViewer accel={accel} wsStatus={wsStatus} />

      {/* ── Metal Presence Heatmap ── */}
      <div className="mt-6">
        <MetalHeatmap points={heatmapPoints} />
      </div>
    </div>
  );
}
