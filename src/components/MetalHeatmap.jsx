import React, { useEffect, useRef, useState } from 'react';

// Generates a 256x1 gradient image data to use as a color lookup table
function createColorPalette() {
  const canvas = document.createElement('canvas');
  canvas.width = 256;
  canvas.height = 1;
  const ctx = canvas.getContext('2d');
  
  const gradient = ctx.createLinearGradient(0, 0, 256, 0);
  gradient.addColorStop(0.2, 'blue');
  gradient.addColorStop(0.4, 'cyan');
  gradient.addColorStop(0.6, 'lime');
  gradient.addColorStop(0.8, 'yellow');
  gradient.addColorStop(1.0, 'red');
  
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 256, 1);
  
  return ctx.getImageData(0, 0, 256, 1).data;
}

// Creates a radial gradient brush to draw each point
function createPointBrush(radius, blur) {
  const canvas = document.createElement('canvas');
  const size = radius + blur;
  canvas.width = size * 2;
  canvas.height = size * 2;
  const ctx = canvas.getContext('2d');
  
  ctx.shadowOffsetX = size * 2;
  ctx.shadowBlur = blur;
  ctx.shadowColor = 'black';
  
  ctx.beginPath();
  ctx.arc(-size, size, radius, 0, Math.PI * 2, true);
  ctx.closePath();
  ctx.fill();
  
  return canvas;
}

export default function MetalHeatmap({ points }) {
  const mainCanvasRef = useRef(null);
  const containerRef = useRef(null);
  
  const paletteRef = useRef(null);
  const brushRef = useRef(null);
  
  const [dimensions, setDimensions] = useState({ width: 600, height: 300 });

  // Handle Resize
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        setDimensions({
          width: entry.contentRect.width,
          height: entry.contentRect.height
        });
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // Initialize Palette and Brush
  useEffect(() => {
    paletteRef.current = createColorPalette();
    brushRef.current = createPointBrush(15, 25); // Radius, Blur
  }, []);

  // Draw Heatmap
  useEffect(() => {
    const canvas = mainCanvasRef.current;
    if (!canvas || points.length === 0 || !paletteRef.current || !brushRef.current) return;
    const ctx = canvas.getContext('2d');
    const { width, height } = dimensions;

    // We'll draw to an offscreen canvas first to calculate alpha densities
    const offscreenCanvas = document.createElement('canvas');
    offscreenCanvas.width = width;
    offscreenCanvas.height = height;
    const offCtx = offscreenCanvas.getContext('2d');

    // 1. Determine geographic bounds
    let minLat = Infinity, maxLat = -Infinity;
    let minLon = Infinity, maxLon = -Infinity;
    points.forEach(p => {
      if (p.lat < minLat) minLat = p.lat;
      if (p.lat > maxLat) maxLat = p.lat;
      if (p.lon < minLon) minLon = p.lon;
      if (p.lon > maxLon) maxLon = p.lon;
    });

    const latRange = Math.max(maxLat - minLat, 0.001);
    const lonRange = Math.max(maxLon - minLon, 0.001);

    // 2. Draw black alpha gradients for each point on the offscreen canvas
    offCtx.clearRect(0, 0, width, height);
    
    points.forEach(p => {
      const marginX = width * 0.1;
      const marginY = height * 0.1;
      const drawWidth = width - 2 * marginX;
      const drawHeight = height - 2 * marginY;

      const x = marginX + ((p.lon - minLon) / lonRange) * drawWidth;
      const y = marginY + (1 - ((p.lat - minLat) / latRange)) * drawHeight;
      
      // Intensity determines the opacity of the brush stamp
      // High voltage = more opaque stamp = hotter final color
      const intensity = Math.min(Math.max(p.voltage, 0.1), 1);
      offCtx.globalAlpha = p.detected ? intensity : intensity * 0.3;
      
      const brushSize = brushRef.current.width / 2;
      offCtx.drawImage(brushRef.current, x - brushSize, y - brushSize);
    });

    // 3. Colorize the offscreen canvas based on alpha values using the palette
    const imgData = offCtx.getImageData(0, 0, width, height);
    const data = imgData.data;
    const palette = paletteRef.current;

    for (let i = 0; i < data.length; i += 4) {
      const alpha = data[i + 3]; // Alpha value of the pixel
      
      if (alpha > 0) {
        // Look up color in palette (palette is 256 pixels wide, each 4 bytes)
        // Ensure index doesn't exceed 255
        const paletteIdx = Math.min(alpha * 4, (256 - 1) * 4);
        
        data[i] = palette[paletteIdx];       // R
        data[i + 1] = palette[paletteIdx + 1]; // G
        data[i + 2] = palette[paletteIdx + 2]; // B
        // We keep the original alpha (or we can increase it slightly)
        data[i + 3] = Math.min(255, alpha * 1.5); 
      }
    }

    // 4. Draw Map Background on Main Canvas
    ctx.clearRect(0, 0, width, height);
    
    // Nice ocean topography-like background
    ctx.fillStyle = '#0f172a'; // Deep water
    ctx.fillRect(0, 0, width, height);

    // Grid lines for scale
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 10; i++) {
      const gx = (i / 10) * width;
      const gy = (i / 10) * height;
      ctx.beginPath(); ctx.moveTo(gx, 0); ctx.lineTo(gx, height); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, gy); ctx.lineTo(width, gy); ctx.stroke();
    }

    // 5. Put the colorized heatmap on top
    offCtx.putImageData(imgData, 0, 0);
    ctx.drawImage(offscreenCanvas, 0, 0);

  }, [points, dimensions]);

  return (
    <div className="telemetry-card glass-card rounded-2xl w-full h-full flex flex-col md:col-span-2 lg:col-span-2">
      <div className="telemetry-card-label mb-3 flex items-center justify-between">
        <span className="flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-[var(--accent-cyan)]"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
          Metal Presence Density Map
        </span>
        <span className="text-xs text-[var(--text-muted)] font-normal">{points.length} samples</span>
      </div>
      
      <div 
        ref={containerRef}
        className="flex-1 relative rounded-lg overflow-hidden border border-[var(--border-light)] min-h-[250px]"
      >
        {/* We use a static background color in the canvas itself for better blending, 
            but this div can contain a map image in the future if desired. */}
        <canvas 
          ref={mainCanvasRef} 
          width={dimensions.width} 
          height={dimensions.height} 
          className="absolute inset-0 w-full h-full"
        />
      </div>

      <div className="text-xs text-[var(--text-muted)] mt-4 flex items-center justify-center bg-[#0f172a] p-2 rounded-lg border border-[var(--border-light)] mx-auto max-w-sm w-full">
        <span className="w-16 text-right">Low Density</span>
        <div className="flex-1 h-2 rounded-full mx-3" style={{ background: 'linear-gradient(to right, transparent, blue, cyan, lime, yellow, red)' }}></div>
        <span className="w-16">High Density</span>
      </div>
    </div>
  );
}
