import { useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import ROVModel from './ROVModel';

// Simple configuration for mapping MPU6050 axes to 3D axes
const AXIS_CONFIG = {
  pitchInvert: false, // If nose goes up instead of down, toggle this
  rollInvert: false,  // If ROV tilts left instead of right, toggle this
};

export default function ROV3DViewer({ accel, wsStatus }) {
  const [pitch, setPitch] = useState(0);
  const [roll, setRoll] = useState(0);

  // Derive roll and pitch from accelerometer data
  useEffect(() => {
    if (!accel || accel.x === null || accel.y === null || accel.z === null) return;

    // Pitch: Rotation around X-axis. 
    // In MPU6050: tilting forward typically means X acceleration changes.
    // Gravity points down. If ROV sits flat, Z is ~1g, X and Y are ~0g.
    const rawPitch = Math.atan2(
      AXIS_CONFIG.pitchInvert ? accel.x : -accel.x,
      Math.sqrt(accel.y * accel.y + accel.z * accel.z)
    );
    
    // Roll: Rotation around Z-axis. 
    // Tilting left/right changes Y acceleration.
    const rawRoll = Math.atan2(
      AXIS_CONFIG.rollInvert ? -accel.y : accel.y,
      accel.z
    );

    setPitch(rawPitch);
    setRoll(rawRoll);
  }, [accel]);

  const radToDeg = (rad) => (rad * (180 / Math.PI)).toFixed(1);

  const isLive = wsStatus === 'Connected' && accel?.z !== null;
  const statusColor = isLive ? '#6ee7b7' : wsStatus === 'Connecting' ? '#c9913a' : '#ff5d73';
  const statusText = isLive ? 'LIVE' : wsStatus === 'Connecting' ? 'WAITING' : 'OFFLINE';

  const fmt = (val) => (val === null || val === undefined ? '—' : Number(val).toFixed(2));

  return (
    <div className="telemetry-card glass-card rounded-2xl w-full h-[320px] flex flex-col relative overflow-hidden mb-6 border" style={{ borderColor: 'var(--border-medium)' }}>
      {/* 3D Scene */}
      <div className="w-full h-full cursor-move" style={{ background: 'radial-gradient(circle at center, #00121a 0%, #00080d 100%)' }}>
        <Canvas camera={{ position: [3, 2, 4], fov: 45 }}>
          <ambientLight intensity={0.4} />
          <directionalLight position={[5, 10, 5]} intensity={1.5} color="#00d4ff" />
          <directionalLight position={[-5, 5, -5]} intensity={0.5} color="#c9913a" />
          
          <ROVModel targetPitch={pitch} targetRoll={roll} />
          
          <Grid 
            infiniteGrid 
            fadeDistance={15} 
            sectionColor="#004455" 
            cellColor="#001122" 
            sectionThickness={1.5} 
            cellThickness={0.8} 
            position={[0, -1, 0]} 
          />
          <OrbitControls 
            enablePan={false} 
            enableZoom={true} 
            minDistance={2} 
            maxDistance={10} 
            maxPolarAngle={Math.PI / 2} 
            autoRotate={false}
          />
        </Canvas>
      </div>
    </div>
  );
}
