import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  Waves,
  LogOut,
  MapPin,
  Zap,
  Map,
  Activity,
  TrendingUp,
  Clock,
} from 'lucide-react';
import LiveDepthChart from '../components/LiveDepthChart';
import SensorTelemetryPanel from '../components/SensorTelemetryPanel';
import ImageProcessingPanel from '../components/ImageProcessingPanel';

const initialSummary = {
  active_surveys: 3,
  anomaly_count: 0,
  last_map: 'CCZ-04',
  system_status: 'Nominal',
};

const defaultRecentActivity = [
  { time: 'syncing', event: 'Waiting for live telemetry...', type: 'info' },
];

const defaultSystemSensors = [
  { label: 'EM Array', status: 'Operational', pct: 100, color: '#6ee7b7' },
  { label: 'Magnetic Sensor', status: 'Operational', pct: 100, color: '#6ee7b7' },
  { label: 'Depth / IMU', status: 'Operational', pct: 100, color: '#6ee7b7' },
  { label: 'Ultrasonic', status: 'Standby', pct: 65, color: '#c9913a' },
  { label: 'Visual Camera', status: 'Operational', pct: 100, color: '#6ee7b7' },
];

export default function Dashboard() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const activityRef = useRef(defaultRecentActivity);
  const [activeTab, setActiveTab] = useState('sensors');
  const [summary, setSummary] = useState(initialSummary);
  const [activity, setActivity] = useState(defaultRecentActivity);
  const [devices, setDevices] = useState([]);
  const [connectionState, setConnectionState] = useState('connecting');
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    activityRef.current = activity;
  }, [activity]);

  const displayName = currentUser?.displayName || currentUser?.email?.split('@')[0] || 'Operator';
  const liveStatus = connectionState === 'connected' ? 'Live' : connectionState === 'reconnecting' ? 'Reconnecting…' : 'Offline';
  const liveStatusColor = connectionState === 'connected' ? '#6ee7b7' : connectionState === 'reconnecting' ? '#c9913a' : '#ff5d73';

  useEffect(() => {
    async function fetchInitialData() {
      if (!currentUser?.token) {
        setIsLoading(false);
        return;
      }

      try {
        const [summaryRes, activityRes, devicesRes] = await Promise.all([
          fetch('http://localhost:8000/api/dashboard/summary'),
          fetch('http://localhost:8000/api/activity?limit=6'),
          fetch('http://localhost:8000/api/devices'),
        ]);

        const summaryData = await summaryRes.json();
        const activityData = await activityRes.json();
        const devicesData = await devicesRes.json();

        setSummary((prev) => ({
          ...prev,
          ...summaryData,
          active_surveys: summaryData.active_surveys ?? prev.active_surveys,
          anomaly_count: summaryData.anomaly_count ?? prev.anomaly_count,
          last_map: summaryData.last_map ?? prev.last_map,
          system_status: summaryData.system_status ?? prev.system_status,
        }));
        setActivity(activityData.activity ?? defaultRecentActivity);
        setDevices(devicesData.devices ?? []);
      } catch {
        setActivity(defaultRecentActivity);
      } finally {
        setIsLoading(false);
      }
    }

    fetchInitialData();
  }, [currentUser?.token]);

  useEffect(() => {
    if (!currentUser?.token) {
      return undefined;
    }

    let socket;
    let retryTimeout;

    const connectLiveSocket = () => {
      setConnectionState('connecting');
      const url = `ws://localhost:8000/ws/live?token=${encodeURIComponent(currentUser.token)}`;
      socket = new WebSocket(url);

      socket.onopen = () => {
        setConnectionState('connected');
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);

          if (payload.type === 'state') {
            setSummary((prev) => ({ ...prev, ...payload.summary }));
            setActivity(payload.activity ?? defaultRecentActivity);
            setDevices(payload.devices ?? []);
            return;
          }

          if (payload.type === 'reading') {
            setSummary((prev) => ({
              ...prev,
              anomaly_count: payload.anomaly_count ?? prev.anomaly_count,
              last_map: payload.last_map ?? prev.last_map,
              system_status: payload.system_status ?? prev.system_status,
            }));

            const nextActivity = [
              {
                time: payload.timestamp?.slice(11, 16) ?? 'now',
                event: payload.message,
                type: payload.anomaly ? 'alert' : 'success',
              },
              ...activityRef.current,
            ].slice(0, 6);
            setActivity(nextActivity);
          }

          if (payload.type === 'device_status') {
            setDevices((prev) => {
              const next = prev.filter((device) => device.device_id !== payload.device_id);
              next.push({
                device_id: payload.device_id,
                status: payload.online ? 'online' : 'offline',
                last_seen: payload.timestamp,
              });
              return next;
            });
          }
        } catch {
          // ignore malformed message payloads
        }
      };

      socket.onclose = () => {
        setConnectionState('reconnecting');
        retryTimeout = window.setTimeout(() => {
          connectLiveSocket();
        }, 2000);
      };

      socket.onerror = () => {
        setConnectionState('disconnected');
      };
    };

    connectLiveSocket();

    return () => {
      if (retryTimeout) {
        window.clearTimeout(retryTimeout);
      }
      socket?.close();
    };
  }, [currentUser?.token]);

  async function handleLogout() {
    try {
      await logout();
      navigate('/');
    } catch {
      // silent
    }
  }

  const dashboardCards = [
    {
      id: 'active-surveys',
      icon: <MapPin size={22} />,
      label: 'Active Surveys',
      value: String(summary.active_surveys ?? 0),
      sub: devices.length > 0 ? `${devices.filter((device) => device.status === 'online').length} devices online` : '2 in coarse scan · 1 in fine scan',
      color: '#00d4ff',
      trend: '+1 since yesterday',
    },
    {
      id: 'detected-anomalies',
      icon: <Zap size={22} />,
      label: 'Detected Anomalies',
      value: String(summary.anomaly_count ?? 0),
      sub: 'Live deviation monitoring',
      color: '#c9913a',
      trend: 'Updated in real time',
    },
    {
      id: 'last-map',
      icon: <Map size={22} />,
      label: 'Last Metal-Priority Map',
      value: summary.last_map ?? 'CCZ-04',
      sub: 'Generated on the live pipeline',
      color: '#a78bfa',
      trend: 'Confidence stream active',
    },
    {
      id: 'system-status',
      icon: <Activity size={22} />,
      label: 'System Status',
      value: summary.system_status ?? 'Nominal',
      sub: 'Sensors and ingestion stream status',
      color: '#6ee7b7',
      trend: `Socket: ${liveStatus}`,
    },
  ];

  return (
    <div
      className="min-h-screen"
      style={{ background: 'linear-gradient(180deg, var(--bg-primary) 0%, var(--bg-secondary) 100%)' }}
    >
      <header
        className="sticky top-0 z-50"
        style={{
          background: 'var(--bg-card)',
          backdropFilter: 'blur(16px)',
          borderBottom: '1px solid var(--border-light)',
        }}
      >
        <div className="container-app py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full flex items-center justify-center" style={{ background: 'var(--border-light)' }}>
              <Waves size={18} className="text-[var(--accent-cyan)]" />
            </div>
            <span
              className="font-bold text-lg text-[var(--text-primary)]"
              style={{ fontFamily: "'Space Grotesk', sans-serif" }}
            >
              Ocean<span className="text-[var(--accent-cyan)]">Atlas</span>
              <span className="ml-2 text-[var(--text-muted)] font-normal text-sm">/ Dashboard</span>
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div
              className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium"
              style={{
                background: `${liveStatusColor}14`,
                border: `1px solid ${liveStatusColor}40`,
                color: liveStatusColor,
              }}
            >
              <span className="w-1.5 h-1.5 rounded-full bg-current animate-pulse" />
              {liveStatus}
            </div>
            <div className="text-sm text-[var(--text-muted)]">{displayName}</div>
            <button
              id="dashboard-logout-btn"
              onClick={handleLogout}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-[var(--text-muted)] hover:text-[var(--accent-cyan)] transition-all duration-200 border border-transparent"
              style={{ ':hover': { background: 'var(--border-light)', borderColor: 'var(--border-medium)' } }}
            >
              <LogOut size={14} />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </header>

      <main className="container-app dashboard-main">
        <div className="dashboard-welcome">
          <p className="text-[var(--text-muted)] text-sm mb-1">Welcome back,</p>
          <h1
            className="text-3xl md:text-4xl font-bold text-[var(--text-primary)]"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            {displayName}{' '}
            <span className="text-[var(--accent-cyan)]">👋</span>
          </h1>
          <p className="text-[var(--text-muted)] text-sm mt-2">
            <Clock size={13} className="inline mr-1" />
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long', year: 'numeric', month: 'long', day: 'numeric',
            })}
          </p>
        </div>

        {/* Main Content Section */}
        <div className="flex flex-col gap-8 w-full mt-6">
          
          {/* Tab Navigation */}
          <div className="flex justify-center gap-8 sm:gap-16">
            <button
              onClick={() => setActiveTab('sensors')}
              className={`pb-3 px-2 text-[15px] font-medium transition-colors relative ${
                activeTab === 'sensors' ? 'text-[var(--accent-cyan)]' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              Sensor Processing
              {activeTab === 'sensors' && (
                <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-[var(--accent-cyan)] shadow-[0_0_8px_var(--accent-cyan)] rounded-full" />
              )}
            </button>
            <button
              onClick={() => setActiveTab('camera')}
              className={`pb-3 px-2 text-[15px] font-medium transition-colors relative ${
                activeTab === 'camera' ? 'text-[var(--accent-cyan)]' : 'text-[var(--text-muted)] hover:text-[var(--text-primary)]'
              }`}
            >
              Image Processing
              {activeTab === 'camera' && (
                <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-[var(--accent-cyan)] shadow-[0_0_8px_var(--accent-cyan)] rounded-full" />
              )}
            </button>
          </div>
          
          {/* Content Area */}
          <div className="w-full">

        {activeTab === 'sensors' ? (
          <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 ease-out flex flex-col gap-6">
            <LiveDepthChart />
            <SensorTelemetryPanel />
          </div>
        ) : (
          <ImageProcessingPanel />
        )}
          </div>
        </div>
      </main>
    </div>
  );
}
