import { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Waves } from 'lucide-react';

export default function LiveDepthChart() {
  const [data, setData] = useState([]);
  const [currentDepth, setCurrentDepth] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const wsRef = useRef(null);

  useEffect(() => {
    let reconnectTimeout;

    const connectWebSocket = () => {
      setConnectionStatus('Connecting...');
      
      const backendHost = window.location.hostname === 'localhost' ? 'localhost' : window.location.hostname;
      const wsUrl = `ws://${backendHost}:8000/ws/depth`;
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setConnectionStatus('Connected');
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'depth' && typeof payload.depth_cm === 'number') {
            setCurrentDepth(payload.depth_cm);
            
            setData(prevData => {
              const newData = [...prevData, {
                time: payload.timestamp,
                depth: payload.depth_cm
              }];
              
              // Keep only the last 100 points
              if (newData.length > 100) {
                newData.shift();
              }
              return newData;
            });
          }
        } catch (err) {
          console.error("Failed to parse depth data", err);
        }
      };

      ws.onclose = () => {
        setConnectionStatus('Disconnected');
        // Reconnect after 2 seconds
        reconnectTimeout = setTimeout(connectWebSocket, 2000);
      };

      ws.onerror = () => {
        setConnectionStatus('Disconnected');
      };
    };

    connectWebSocket();

    return () => {
      if (reconnectTimeout) clearTimeout(reconnectTimeout);
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  return (
    <div className="dashboard-panel glass-card rounded-2xl col-span-full mb-6">
      <div className="dashboard-panel-header flex justify-between items-center mb-4">
        <h2 className="text-lg font-bold text-[var(--text-primary)] flex items-center gap-2" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
          <Waves size={18} className="text-[var(--accent-cyan)]" />
          Live Seafloor Depth
        </h2>
        
        <div className="flex items-center gap-4">
          <div className="text-right">
            <span className="text-sm text-[var(--text-accent)] mr-2">Current Depth:</span>
            <span className="text-xl font-bold text-[var(--accent-cyan)]" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
              {currentDepth !== null ? `${currentDepth.toFixed(2)} cm` : '--'}
            </span>
          </div>
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium" 
            style={{
              background: connectionStatus === 'Connected' ? '#6ee7b714' : '#ff5d7314',
              border: `1px solid ${connectionStatus === 'Connected' ? '#6ee7b740' : '#ff5d7340'}`,
              color: connectionStatus === 'Connected' ? '#6ee7b7' : '#ff5d73'
            }}>
            <span className={`w-1.5 h-1.5 rounded-full ${connectionStatus === 'Connected' ? 'bg-[#6ee7b7] animate-pulse' : 'bg-[#ff5d73]'}`} />
            {connectionStatus}
          </div>
        </div>
      </div>
      
      <div className="w-full h-64">
        {data.length === 0 ? (
          <div className="w-full h-full flex items-center justify-center text-[var(--text-muted)] border border-dashed rounded-xl" style={{ borderColor: 'var(--border-medium)', background: 'var(--border-light)' }}>
            Waiting for depth data...
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: -20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border-medium)" vertical={false} />
              <XAxis 
                dataKey="time" 
                stroke="var(--text-muted)" 
                fontSize={12} 
                tickMargin={10}
                tickFormatter={(val) => {
                  // Show every Nth label or format time nicely if needed
                  return val;
                }} 
              />
              <YAxis 
                stroke="var(--text-muted)" 
                fontSize={12} 
                domain={['auto', 'auto']}
                tickFormatter={(val) => `${val}`}
              />
              <Tooltip 
                contentStyle={{ backgroundColor: 'var(--bg-card)', borderColor: 'var(--border-medium)', color: 'var(--text-primary)', borderRadius: '8px' }}
                itemStyle={{ color: 'var(--accent-cyan)' }}
                labelStyle={{ color: 'var(--text-accent)' }}
              />
              <Line 
                type="monotone" 
                dataKey="depth" 
                name="Depth (cm)"
                stroke="var(--accent-cyan)" 
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 6, fill: 'var(--accent-cyan)', stroke: 'var(--bg-card)', strokeWidth: 2 }}
                isAnimationActive={false} // Disable animation for better performance on live data
              />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
