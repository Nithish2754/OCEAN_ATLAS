import React, { useState, useEffect } from 'react';
import { Camera, ShieldAlert, Cpu, Activity } from 'lucide-react';
import DetectionSummary from './DetectionSummary';
import DetectionHistory from './DetectionHistory';

export default function ImageProcessingPanel() {
  const streamUrl = 'http://localhost:8000/api/video_feed'; 
  
  const [summary, setSummary] = useState(null);
  const [history, setHistory] = useState(null);
  
  const fetchDetections = async () => {
    try {
      const sumRes = await fetch('http://localhost:8000/api/detections/summary');
      if (sumRes.ok) setSummary(await sumRes.json());
      
      const histRes = await fetch('http://localhost:8000/api/detections');
      if (histRes.ok) setHistory((await histRes.json()).history);
    } catch (err) {
      console.error('Error fetching detections:', err);
    }
  };

  useEffect(() => {
    fetchDetections();
    
    // Connect to WebSocket for real-time detection updates
    const ws = new WebSocket('ws://localhost:8000/ws/detections');
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'new_detection') {
          // Re-fetch to get updated counts and history easily, 
          // or manually update state. We'll just fetch for simplicity.
          fetchDetections();
        }
      } catch (err) {
        console.error(err);
      }
    };
    
    return () => {
      ws.close();
    };
  }, []);

  const handleReset = async () => {
    if (!window.confirm("Are you sure you want to reset the current session? Evidence images will remain on disk, but counts will be reset.")) {
      return;
    }
    try {
      await fetch('http://localhost:8000/api/detections/reset', { method: 'POST' });
      fetchDetections();
    } catch (err) {
      console.error(err);
    }
  };

  const handleGenerateReport = () => {
    window.open('http://localhost:8000/api/detections/report', '_blank');
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Are you sure you want to delete this detection?")) {
      return;
    }
    try {
      await fetch(`http://localhost:8000/api/detections/${id}`, { method: 'DELETE' });
      fetchDetections();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="flex flex-col gap-6 w-full animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      
      {/* Evidence & Reporting Section */}
      <div className="grid grid-cols-1 gap-6">
        <DetectionHistory 
          history={history} 
          onReset={handleReset} 
          onGenerateReport={handleGenerateReport} 
          onDelete={handleDelete}
        />
        <DetectionSummary summary={summary} />
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="glass-card rounded-2xl p-5 border border-[var(--border-light)] flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[var(--accent-cyan)]/10 text-[var(--accent-cyan)]">
            <Cpu size={20} />
          </div>
          <div>
            <div className="text-xs text-[var(--text-muted)] font-medium">Model Status</div>
            <div className="text-lg font-bold text-[var(--text-primary)]">Custom Metal YOLO Active</div>
          </div>
        </div>
        
        <div className="glass-card rounded-2xl p-5 border border-[var(--border-light)] flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-green-500/10 text-green-400">
            <Activity size={20} />
          </div>
          <div>
            <div className="text-xs text-[var(--text-muted)] font-medium">Inference Speed</div>
            <div className="text-lg font-bold text-[var(--text-primary)]">~30 FPS</div>
          </div>
        </div>

        <div className="glass-card rounded-2xl p-5 border border-[var(--border-light)] flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-[#c9913a]/10 text-[#c9913a]">
            <ShieldAlert size={20} />
          </div>
          <div>
            <div className="text-xs text-[var(--text-muted)] font-medium">Recent Detections</div>
            <div className="text-lg font-bold text-[var(--text-primary)]">
              {history && history.length > 0 ? history[0].class_name : 'None'}
            </div>
          </div>
        </div>
      </div>

      {/* Main Video Panel */}
      <div className="glass-card rounded-2xl border border-[var(--border-light)] overflow-hidden flex flex-col">
        <div className="px-6 py-4 border-b border-[var(--border-light)] flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Camera size={18} className="text-[var(--text-accent)]" />
            <h2 className="font-bold text-lg text-[var(--text-primary)]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              Live Camera Feed
            </h2>
          </div>
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            Stream Active
          </div>
        </div>
        
        <div className="relative bg-[#050b14] w-full aspect-video flex items-center justify-center overflow-hidden group border-b border-[var(--border-light)]">
          <div className="absolute inset-0 flex flex-col items-center justify-center text-[var(--text-muted)] z-0">
            <Camera size={48} className="opacity-20 mb-4" />
            <p>Waiting for video stream...</p>
            <p className="text-xs opacity-50 mt-1">Make sure the OpenCV backend is running</p>
          </div>
          
          <img 
            src={streamUrl} 
            alt="Live Object Detection Feed"
            className="w-full h-full object-contain relative z-10"
            onError={(e) => { e.target.style.display = 'none'; }}
            onLoad={(e) => { e.target.style.display = 'block'; }}
          />

          <div className="absolute top-4 left-4 z-20 flex flex-col gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300">
            <div className="bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-md text-xs text-white/90 font-mono border border-white/10">
              RES: 1280x720
            </div>
            <div className="bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-md text-xs text-white/90 font-mono border border-white/10">
              CONF THRESH: 0.46
            </div>
          </div>
        </div>
      </div>

    </div>
  );
}
