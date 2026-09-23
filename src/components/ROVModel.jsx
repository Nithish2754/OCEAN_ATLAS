import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';

export default function ROVModel({ targetPitch, targetRoll }) {
  const group = useRef();

  useFrame((state, delta) => {
    if (!group.current) return;
    
    // Smooth interpolation (lerp)
    // Adjust smoothing factor if it feels too sluggish or too jittery
    const smoothing = 5.0; 
    
    // Lerp rotation independently
    group.current.rotation.x = THREE.MathUtils.lerp(group.current.rotation.x, targetPitch, delta * smoothing);
    group.current.rotation.z = THREE.MathUtils.lerp(group.current.rotation.z, targetRoll, delta * smoothing);
  });

  return (
    <group ref={group}>
      {/* Main Body */}
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[1.5, 0.8, 2]} />
        <meshStandardMaterial color="#002d3d" metalness={0.6} roughness={0.4} />
        {/* Wireframe overlay to look more technical */}
        <mesh position={[0,0,0]}>
           <boxGeometry args={[1.501, 0.801, 2.001]} />
           <meshBasicMaterial color="#00d4ff" wireframe={true} transparent opacity={0.3}/>
        </mesh>
      </mesh>
      
      {/* Side Thrusters */}
      <mesh position={[-0.9, 0, 0.5]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.2, 0.2, 0.8, 16]} />
        <meshStandardMaterial color="#333333" metalness={0.9} roughness={0.1} />
      </mesh>
      <mesh position={[0.9, 0, 0.5]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.2, 0.2, 0.8, 16]} />
        <meshStandardMaterial color="#333333" metalness={0.9} roughness={0.1} />
      </mesh>
      
      {/* Top Dome (Sensors) */}
      <mesh position={[0, 0.4, 0.7]}>
        <sphereGeometry args={[0.3, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2]} />
        <meshStandardMaterial color="#00d4ff" metalness={0.9} roughness={0.1} transparent opacity={0.6} />
      </mesh>
      
      {/* Camera Lens in Dome */}
      <mesh position={[0, 0.5, 0.95]} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.1, 0.1, 0.1, 16]} />
        <meshStandardMaterial color="#000000" metalness={1} roughness={0} />
      </mesh>
      
      {/* Back Support Frame */}
      <mesh position={[0, 0, -1.1]}>
        <boxGeometry args={[1.0, 0.4, 0.2]} />
        <meshStandardMaterial color="#111111" metalness={0.8} roughness={0.2} />
      </mesh>
    </group>
  );
}
