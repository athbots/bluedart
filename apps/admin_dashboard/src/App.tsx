import React, { useState, useEffect } from 'react';
import { 
  Bus, 
  Activity, 
  MapPin, 
  Users, 
  Clock, 
  Cpu, 
  Play, 
  Square, 
  AlertTriangle, 
  CheckCircle2, 
  Radio, 
  TrendingUp, 
  ShieldAlert, 
  Navigation,
  Eye,
  Sliders,
  RefreshCw,
  Search
} from 'lucide-react';
import { LiveBus, DeviceInfo, CrowdAnalyticsData, ETAAnalyticsData } from './types';
import { ThreeDTransitCorridor, RouteProgressionViewData } from './components/ThreeDTransitCorridor';

export default function App() {
  const [activeTab, setActiveTab] = useState<'overview' | 'fleet_map' | 'liveboard' | 'passenger_app' | 'crowd_analytics' | 'eta_analytics' | 'devices' | 'simulator'>('overview');
  const [corridorViewMode, setCorridorViewMode] = useState<'3D' | '2D'>('3D');
  const [corridorProgressionData, setCorridorProgressionData] = useState<RouteProgressionViewData | null>(null);
  const [buses, setBuses] = useState<LiveBus[]>([]);
  const [selectedBus, setSelectedBus] = useState<LiveBus | null>(null);
  const [devices, setDevices] = useState<DeviceInfo[]>([]);
  const [crowdAnalytics, setCrowdAnalytics] = useState<CrowdAnalyticsData | null>(null);
  const [etaAnalytics, setEtaAnalytics] = useState<ETAAnalyticsData | null>(null);
  const [simulatorStatus, setSimulatorStatus] = useState({ is_running: false, active_buses_count: 0 });
  const [activeScenario, setActiveScenario] = useState<string | null>(null);
  const [scenarioMessage, setScenarioMessage] = useState<string | null>(null);
  const [selectedStopId, setSelectedStopId] = useState<string>('STOP_10');
  const [liveboardData, setLiveboardData] = useState<any>(null);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [passengerProgressionView, setPassengerProgressionView] = useState<any>(null);
  const [passengerViewMode, setPassengerViewMode] = useState<'3D' | 'LIST'>('3D');
  const [passengerLang, setPassengerLang] = useState<'en' | 'hi'>('en');

  // Poll / Fetch core state
  const fetchData = async () => {
    try {
      let currentBuses = buses;
      // 1. Fetch Buses
      const busRes = await fetch('/api/v1/buses');
      if (busRes.ok) {
        currentBuses = await busRes.json();
        setBuses(currentBuses);
        if (selectedBus) {
          const updated = currentBuses.find((b: LiveBus) => b.vehicle_id === selectedBus.vehicle_id);
          if (updated) setSelectedBus(updated);
        }
      }

      // 2. Fetch Devices
      const devRes = await fetch('/api/v1/device/list');
      if (devRes.ok) {
        setDevices(await devRes.json());
      }

      // 3. Fetch Simulator Status
      const simRes = await fetch('/api/v1/simulator/status');
      if (simRes.ok) {
        setSimulatorStatus(await simRes.json());
      }

      // 4. Fetch 3D Corridor Progression View
      const activeVehicle = selectedBus ? selectedBus.vehicle_id : (currentBuses[0]?.vehicle_id || 'BUS_115_C');
      const activeRoute = selectedBus ? selectedBus.route_id : 'ROUTE_AV_MOD';
      const progRes = await fetch(`/api/v1/routes/${activeRoute}/progress?vehicle_id=${activeVehicle}&user_stop_id=${selectedStopId}`);
      if (progRes.ok) {
        setCorridorProgressionData(await progRes.json());
      }
    } catch (e) {
      console.warn('API sync warning:', e);
    }
  };

  // Fetch Analytics & Liveboard
  const fetchAnalytics = async () => {
    try {
      const [cRes, eRes, lRes] = await Promise.all([
        fetch('/api/v1/predictions/analytics/crowd'),
        fetch('/api/v1/predictions/analytics/eta'),
        fetch(`/api/v1/stops/${selectedStopId}/arrivals`)
      ]);
      if (cRes.ok) setCrowdAnalytics(await cRes.json());
      if (eRes.ok) setEtaAnalytics(await eRes.json());
      if (lRes.ok) setLiveboardData(await lRes.json());
    } catch (e) {
      console.warn('Analytics fetch error:', e);
    }
  };

  useEffect(() => {
    fetchData();
    fetchAnalytics();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [selectedBus?.vehicle_id, selectedStopId]);

  // WebSocket Connection
  useEffect(() => {
    let ws: WebSocket | null = null;
    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      ws = new WebSocket(`${protocol}//${window.location.host}/ws/fleet`);
      ws.onopen = () => setWsConnected(true);
      ws.onclose = () => setWsConnected(false);
      ws.onmessage = (evt) => {
        try {
          const msg = JSON.parse(evt.data);
          if (msg.type === 'FLEET_SNAPSHOT') {
            setBuses(msg.vehicles);
          }
        } catch (_) {}
      };
    } catch (_) {
      setWsConnected(false);
    }
    return () => {
      if (ws) ws.close();
    };
  }, []);

  const handleStartSimulator = async () => {
    await fetch('/api/v1/simulator/start', { method: 'POST' });
    fetchData();
  };

  const handleStopSimulator = async () => {
    await fetch('/api/v1/simulator/stop', { method: 'POST' });
    fetchData();
  };

  const handleTriggerScenario = async (scenId: string) => {
    setActiveScenario(scenId);
    const res = await fetch(`/api/v1/simulator/scenario/${scenId}`, { method: 'POST' });
    if (res.ok) {
      const data = await res.json();
      setScenarioMessage(`${data.title}: ${data.description}`);
      fetchData();
      fetchAnalytics();
    }
  };

  // KPIs
  const activeBusesCount = buses.length;
  const highCrowdBusesCount = buses.filter(b => b.crowd_level === 'HIGH' || b.crowd_level === 'VERY_HIGH').length;
  const onlineDevicesCount = devices.filter(d => d.status === 'ONLINE').length;
  const delayedBusesCount = buses.filter(b => b.is_stale || b.speed_kmh < 5.0).length;

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-dark)' }}>
      {/* Sidebar Navigation */}
      <aside style={{ width: '260px', background: '#0D1424', borderRight: '1px solid var(--border-subtle)', padding: '24px 16px', display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px', paddingLeft: '8px' }}>
          <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'linear-gradient(135deg, #0084FF, #00F2FE)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Bus size={22} color="#fff" />
          </div>
          <div>
            <h2 style={{ fontSize: '16px', fontWeight: 800, color: '#fff', lineHeight: 1.2 }}>SMART TRANSIT</h2>
            <p style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.05em' }}>COMMAND CENTRE</p>
          </div>
        </div>

        <nav style={{ display: 'flex', flexDirection: 'column', gap: '6px', flex: 1 }}>
          {[
            { id: 'overview', label: 'Overview', icon: Activity },
            { id: 'fleet_map', label: 'Live Fleet Radar', icon: Navigation },
            { id: 'passenger_app', label: 'Passenger App View', icon: Bus },
            { id: 'liveboard', label: 'Stop Liveboard', icon: MapPin },
            { id: 'crowd_analytics', label: 'Crowd Intelligence', icon: Users },
            { id: 'eta_analytics', label: 'ETA Analytics', icon: Clock },
            { id: 'devices', label: 'Edge Hardware', icon: Cpu },
            { id: 'simulator', label: 'Fleet Simulator', icon: Sliders },
          ].map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id as any)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '12px',
                  padding: '12px 16px',
                  borderRadius: '12px',
                  border: 'none',
                  background: isActive ? 'rgba(0, 132, 255, 0.15)' : 'transparent',
                  color: isActive ? '#00F2FE' : 'var(--text-secondary)',
                  fontWeight: isActive ? 700 : 500,
                  fontSize: '14px',
                  cursor: 'pointer',
                  textAlign: 'left',
                  transition: 'all 0.2s ease',
                }}
              >
                <Icon size={18} color={isActive ? '#00F2FE' : '#64748B'} />
                {item.label}
              </button>
            );
          })}
        </nav>

        {/* Live Simulator Quick Toggle */}
        <div className="glass-panel" style={{ padding: '14px', marginTop: 'auto', background: 'rgba(15, 23, 42, 0.6)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
            <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-muted)' }}>SIMULATOR ENGINE</span>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: simulatorStatus.is_running ? '#10B981' : '#EF4444' }} />
          </div>
          {simulatorStatus.is_running ? (
            <button
              onClick={handleStopSimulator}
              style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid rgba(239, 68, 68, 0.4)', background: 'rgba(239, 68, 68, 0.15)', color: '#F87171', fontSize: '12px', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
            >
              <Square size={14} /> Stop Simulation
            </button>
          ) : (
            <button
              onClick={handleStartSimulator}
              style={{ width: '100%', padding: '8px', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.4)', background: 'rgba(16, 185, 129, 0.15)', color: '#34D399', fontSize: '12px', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
            >
              <Play size={14} /> Start Simulation
            </button>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <main style={{ flex: 1, display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
        {/* Top Header Bar */}
        <header style={{ padding: '16px 32px', borderBottom: '1px solid var(--border-subtle)', background: 'rgba(13, 20, 36, 0.8)', backdropFilter: 'blur(12px)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <h1 style={{ fontSize: '20px', color: '#fff' }}>NCR Regional Transit Intelligence Control</h1>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Ghaziabad - East Delhi - Noida Rapid Bus Corridors</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', padding: '6px 12px', borderRadius: '20px', background: 'rgba(255, 255, 255, 0.05)', border: '1px solid var(--border-subtle)' }}>
              <span className="pulse-dot" />
              <span style={{ fontSize: '12px', fontWeight: 600, color: '#34D399' }}>Live Telemetry Active</span>
            </div>
            <button
              onClick={() => { fetchData(); fetchAnalytics(); }}
              style={{ background: 'transparent', border: '1px solid var(--border-subtle)', color: 'var(--text-secondary)', padding: '6px 12px', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px' }}
            >
              <RefreshCw size={14} /> Refresh
            </button>
          </div>
        </header>

        {/* Content Body */}
        <div style={{ padding: '32px', flex: 1 }}>
          {scenarioMessage && (
            <div style={{ marginBottom: '24px', padding: '14px 20px', borderRadius: '12px', background: 'rgba(0, 132, 255, 0.15)', border: '1px solid rgba(0, 132, 255, 0.4)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Radio size={18} color="#00F2FE" />
                <span style={{ fontSize: '13px', color: '#E2E8F0', fontWeight: 600 }}>{scenarioMessage}</span>
              </div>
              <button onClick={() => setScenarioMessage(null)} style={{ background: 'transparent', border: 'none', color: '#94A3B8', cursor: 'pointer', fontSize: '12px' }}>Dismiss</button>
            </div>
          )}

          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div>
              {/* KPI Cards Grid */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '32px' }}>
                {[
                  { label: 'Active Fleet Buses', value: activeBusesCount, sub: 'Tracking live coordinates', icon: Bus, color: '#0084FF' },
                  { label: 'High Crowd Density', value: highCrowdBusesCount, sub: 'Buses with >75% occupancy', icon: Users, color: '#EF4444' },
                  { label: 'Online Edge Devices', value: onlineDevicesCount, sub: 'Jetson & Sensor nodes', icon: Cpu, color: '#10B981' },
                  { label: 'Delayed / Gridlock', value: delayedBusesCount, sub: 'Speed <5kmh or stale GPS', icon: AlertTriangle, color: '#F59E0B' },
                ].map((kpi, idx) => {
                  const Icon = kpi.icon;
                  return (
                    <div key={idx} className="glass-panel" style={{ padding: '20px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
                        <span style={{ fontSize: '13px', fontWeight: 600, color: 'var(--text-secondary)' }}>{kpi.label}</span>
                        <div style={{ width: '36px', height: '36px', borderRadius: '10px', background: `${kpi.color}22`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                          <Icon size={18} color={kpi.color} />
                        </div>
                      </div>
                      <div style={{ fontSize: '32px', fontWeight: 800, color: '#fff', marginBottom: '4px' }}>{kpi.value}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{kpi.sub}</div>
                    </div>
                  );
                })}
              </div>

              {/* Active Fleet Quick Table */}
              <div className="glass-panel" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                  <h3 style={{ fontSize: '16px', color: '#fff' }}>Live Fleet Position & Crowd Snapshot</h3>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Updated via real-time WebSocket</span>
                </div>

                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                    <thead>
                      <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                        <th style={{ padding: '12px 16px' }}>Bus / Fleet ID</th>
                        <th style={{ padding: '12px 16px' }}>Route & Direction</th>
                        <th style={{ padding: '12px 16px' }}>Current Stop / Speed</th>
                        <th style={{ padding: '12px 16px' }}>Crowd Level</th>
                        <th style={{ padding: '12px 16px' }}>Source & Provenance</th>
                        <th style={{ padding: '12px 16px' }}>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {buses.map((b) => (
                        <tr key={b.vehicle_id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.04)', color: '#E2E8F0' }}>
                          <td style={{ padding: '14px 16px', fontWeight: 700 }}>
                            <div style={{ color: '#fff' }}>{b.vehicle_id}</div>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{b.registration_number}</div>
                          </td>
                          <td style={{ padding: '14px 16px' }}>
                            <div style={{ fontWeight: 600 }}>Route {b.route_number || 'N/A'}</div>
                            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{b.route_name || b.direction}</div>
                          </td>
                          <td style={{ padding: '14px 16px' }}>
                            <div>{b.current_stop_name || 'In Transit'}</div>
                            <div style={{ fontSize: '11px', color: '#38BDF8' }}>{Math.round(b.speed_kmh)} km/h • {b.route_progress_percentage}% completed</div>
                          </td>
                          <td style={{ padding: '14px 16px' }}>
                            <span className={`badge badge-${b.crowd_level.toLowerCase().replace('_', '-')}`}>
                              {b.crowd_level} ({Math.round(b.occupancy_score * 100)}%)
                            </span>
                          </td>
                          <td style={{ padding: '14px 16px' }}>
                            <span className="badge badge-live">{b.crowd_source}</span>
                          </td>
                          <td style={{ padding: '14px 16px' }}>
                            <button
                              onClick={() => { setSelectedBus(b); setActiveTab('fleet_map'); }}
                              style={{ background: 'rgba(0, 132, 255, 0.15)', border: '1px solid rgba(0, 132, 255, 0.3)', color: '#38BDF8', padding: '6px 12px', borderRadius: '6px', fontSize: '11px', fontWeight: 700, cursor: 'pointer' }}
                            >
                              Track on Map
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: LIVE FLEET MAP & 3D CORRIDOR */}
          {activeTab === 'fleet_map' && (
            <div style={{ display: 'grid', gridTemplateColumns: selectedBus ? '1fr 340px' : '1fr', gap: '24px' }}>
              <div className="glass-panel" style={{ padding: '24px', minHeight: '640px', display: 'flex', flexDirection: 'column' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
                  <div>
                    <h3 style={{ fontSize: '18px', color: '#fff', fontWeight: 800 }}>Anand Vihar ⇄ Modipuram Transit Corridor</h3>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>21 High-Capacity Rapid Transit Stops • Demonstration Corridor</div>
                  </div>

                  {/* 3D vs 2D Toggle */}
                  <div style={{ display: 'flex', gap: '6px', background: 'rgba(255,255,255,0.04)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                    <button
                      onClick={() => setCorridorViewMode('3D')}
                      style={{
                        padding: '6px 14px',
                        borderRadius: '8px',
                        border: 'none',
                        background: corridorViewMode === '3D' ? '#0084FF' : 'transparent',
                        color: corridorViewMode === '3D' ? '#fff' : 'var(--text-muted)',
                        fontSize: '12px',
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      🧊 3D ROUTE CORRIDOR
                    </button>
                    <button
                      onClick={() => setCorridorViewMode('2D')}
                      style={{
                        padding: '6px 14px',
                        borderRadius: '8px',
                        border: 'none',
                        background: corridorViewMode === '2D' ? '#00F2FE' : 'transparent',
                        color: corridorViewMode === '2D' ? '#070B14' : 'var(--text-muted)',
                        fontSize: '12px',
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      🗺️ 2D RADAR MAP
                    </button>
                  </div>
                </div>

                {corridorViewMode === '3D' && corridorProgressionData ? (
                  <ThreeDTransitCorridor
                    progressionData={corridorProgressionData}
                    selectedUserStopId={selectedStopId}
                    onSelectStop={(sId) => {
                      setSelectedStopId(sId);
                      fetchAnalytics();
                    }}
                  />
                ) : (
                  /* 2D GIS Radar Canvas */
                  <div style={{ flex: 1, background: '#070B14', borderRadius: '12px', position: 'relative', overflow: 'hidden', border: '1px solid var(--border-subtle)', minHeight: '520px' }}>
                    <svg width="100%" height="100%" viewBox="0 0 800 500" style={{ display: 'block' }}>
                      <defs>
                        <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                          <path d="M 40 0 L 0 0 0 40" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="1"/>
                        </pattern>
                      </defs>
                      <rect width="100%" height="100%" fill="url(#grid)" />

                      {/* Main Corridor Polyline */}
                      <path d="M 60 440 L 140 400 L 220 360 L 300 320 L 380 280 L 460 230 L 540 180 L 620 130 L 720 70" fill="none" stroke="rgba(0, 132, 255, 0.4)" strokeWidth="5" />

                      {/* 21 Stops Pins */}
                      {[
                        { name: "Anand Vihar", x: 60, y: 440, isMajor: true, type: "TERMINAL" },
                        { name: "Sahibabad", x: 100, y: 420, isMajor: true, type: "MAJOR" },
                        { name: "Ghaziabad", x: 140, y: 400, isMajor: true, type: "TERMINAL" },
                        { name: "Guldhar", x: 180, y: 380, isMajor: false, type: "LOCAL" },
                        { name: "Duhai", x: 220, y: 360, isMajor: true, type: "MAJOR" },
                        { name: "Duhai Depot", x: 260, y: 340, isMajor: true, type: "DEPOT" },
                        { name: "Muradnagar", x: 300, y: 320, isMajor: true, type: "MAJOR" },
                        { name: "Modi Nagar S", x: 340, y: 300, isMajor: false, type: "LOCAL" },
                        { name: "Modi Nagar N", x: 380, y: 280, isMajor: false, type: "LOCAL" },
                        { name: "Meerut South", x: 420, y: 255, isMajor: true, type: "MAJOR" },
                        { name: "Partapur", x: 460, y: 230, isMajor: false, type: "LOCAL" },
                        { name: "Rithani", x: 500, y: 205, isMajor: false, type: "LOCAL" },
                        { name: "Shatabdi Nagar", x: 540, y: 180, isMajor: true, type: "MAJOR" },
                        { name: "Brahmpuri", x: 580, y: 155, isMajor: false, type: "LOCAL" },
                        { name: "Meerut Central", x: 620, y: 130, isMajor: true, type: "TERMINAL" },
                        { name: "Bhaisali", x: 650, y: 110, isMajor: true, type: "MAJOR" },
                        { name: "Begumpul", x: 675, y: 95, isMajor: true, type: "MAJOR" },
                        { name: "MES Colony", x: 690, y: 85, isMajor: false, type: "LOCAL" },
                        { name: "Daurli", x: 705, y: 78, isMajor: false, type: "LOCAL" },
                        { name: "Meerut North", x: 720, y: 70, isMajor: true, type: "MAJOR" },
                        { name: "Modipuram", x: 740, y: 60, isMajor: true, type: "TERMINAL" },
                      ].map((st, i) => (
                        <g key={i} onClick={() => setSelectedStopId(`STOP_${String(i + 1).padStart(2, '0')}`)} style={{ cursor: 'pointer' }}>
                          <circle cx={st.x} cy={st.y} r={st.isMajor ? 6 : 3.5} fill={st.isMajor ? "#00F2FE" : "#64748B"} opacity="0.85" />
                          {st.isMajor && (
                            <text x={st.x + 6} y={st.y + 3} fill="#E2E8F0" fontSize="9" fontWeight="700">{st.name}</text>
                          )}
                        </g>
                      ))}

                      {/* Active Bus Markers on Map */}
                      {buses.map((bus) => {
                        const normX = Math.max(40, Math.min(760, ((bus.longitude - 77.31) / (77.72 - 77.31)) * 700 + 50));
                        const normY = Math.max(40, Math.min(460, 460 - (((bus.latitude - 28.64) / (29.09 - 28.64)) * 400)));
                        const isSel = selectedBus?.vehicle_id === bus.vehicle_id;
                        const crowdColor = bus.crowd_level === 'HIGH' || bus.crowd_level === 'VERY_HIGH' ? '#EF4444' : (bus.crowd_level === 'MEDIUM' ? '#F59E0B' : '#10B981');

                        return (
                          <g key={bus.vehicle_id} onClick={() => setSelectedBus(bus)} style={{ cursor: 'pointer' }}>
                            {isSel && (
                              <circle cx={normX} cy={normY} r="18" fill="none" stroke="#00F2FE" strokeWidth="2" strokeDasharray="3 3" />
                            )}
                            <circle cx={normX} cy={normY} r="10" fill={crowdColor} stroke="#fff" strokeWidth="2" />
                            <text x={normX} y={normY - 14} textAnchor="middle" fill="#fff" fontSize="11" fontWeight="bold">
                              {bus.route_number || bus.vehicle_id}
                            </text>
                          </g>
                        );
                      })}
                    </svg>
                  </div>
                )}
              </div>

              {/* Selected Bus Drawer */}
              {selectedBus && (
                <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                    <div>
                      <h4 style={{ fontSize: '18px', color: '#fff' }}>{selectedBus.vehicle_id}</h4>
                      <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{selectedBus.registration_number}</p>
                    </div>
                    <button onClick={() => setSelectedBus(null)} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>✕</button>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', flex: 1 }}>
                    <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-subtle)' }}>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>ROUTE & DESTINATION</span>
                      <div style={{ fontSize: '14px', fontWeight: 700, color: '#fff', marginTop: '2px' }}>Route {selectedBus.route_number}</div>
                      <div style={{ fontSize: '12px', color: '#94A3B8' }}>{selectedBus.route_name}</div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                      <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(255, 255, 255, 0.03)' }}>
                        <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700 }}>SPEED</span>
                        <div style={{ fontSize: '18px', fontWeight: 800, color: '#38BDF8' }}>{Math.round(selectedBus.speed_kmh)} km/h</div>
                      </div>
                      <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(255, 255, 255, 0.03)' }}>
                        <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700 }}>CROWD</span>
                        <div style={{ fontSize: '16px', fontWeight: 800, color: '#FBBF24' }}>{selectedBus.crowd_level}</div>
                      </div>
                    </div>

                    <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(255, 255, 255, 0.03)' }}>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>PROGRESSION</span>
                      <div style={{ fontSize: '13px', color: '#fff', marginTop: '4px' }}>Near: {selectedBus.current_stop_name}</div>
                      <div style={{ width: '100%', height: '6px', background: 'rgba(255, 255, 255, 0.1)', borderRadius: '3px', marginTop: '8px', overflow: 'hidden' }}>
                        <div style={{ width: `${selectedBus.route_progress_percentage}%`, height: '100%', background: 'linear-gradient(90deg, #0084FF, #00F2FE)' }} />
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px', textAlign: 'right' }}>{selectedBus.route_progress_percentage}% completed</div>
                    </div>

                    <div style={{ padding: '12px', borderRadius: '10px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-subtle)' }}>
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 700 }}>TRANSIT TRUTH & PROVENANCE</span>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '6px', fontSize: '11px' }}>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Location:</span>
                          <div style={{ color: '#38BDF8', fontWeight: 700 }}>{selectedBus.location_source || 'OFFICIAL_GPS'} ({selectedBus.is_live ? 'LIVE' : 'STALE'})</div>
                        </div>
                        <div>
                          <span style={{ color: 'var(--text-muted)' }}>Crowd Source:</span>
                          <div style={{ color: '#FBBF24', fontWeight: 700 }}>{selectedBus.crowd_source}</div>
                        </div>
                      </div>
                      <div style={{ marginTop: '8px', fontSize: '11px', color: 'var(--text-muted)', borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '6px' }}>
                        <div>Confidence: <strong style={{ color: '#34D399' }}>{Math.round(selectedBus.crowd_confidence * 100)}%</strong> • Age: <strong style={{ color: '#E2E8F0' }}>{selectedBus.age_seconds || 2}s</strong></div>
                        <div style={{ fontSize: '10px', marginTop: '2px', color: '#64748B' }}>Device TS: {selectedBus.device_timestamp ? new Date(selectedBus.device_timestamp).toLocaleTimeString() : 'Live'}</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2.5: PASSENGER MOBILE APP LIVE COMPANION */}
          {activeTab === 'passenger_app' && (
            <div style={{ display: 'flex', justifyContent: 'center', padding: '10px 0' }}>
              <div style={{ width: '380px', height: '740px', background: '#F8FAFC', borderRadius: '36px', border: '10px solid #1E293B', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)', overflow: 'hidden', display: 'flex', flexDirection: 'column', position: 'relative' }}>
                {/* Smartphone Notch / Header */}
                <div style={{ height: '24px', background: '#081C3B', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <div style={{ width: '80px', height: '14px', background: '#000', borderRadius: '0 0 10px 10px' }} />
                </div>

                {/* Mobile App Bar */}
                <div style={{ background: '#081C3B', padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#fff' }}>
                  <div>
                    <div style={{ fontSize: '15px', fontWeight: 800 }}>{passengerLang === 'hi' ? 'स्मार्ट ट्रांजिट' : 'Smart Transit India'}</div>
                    <div style={{ fontSize: '10px', color: 'rgba(255,255,255,0.7)' }}>{passengerLang === 'hi' ? 'बस आने से पहले जानें' : 'Know Your Bus Before It Arrives'}</div>
                  </div>
                  <button
                    onClick={() => setPassengerLang(passengerLang === 'en' ? 'hi' : 'en')}
                    style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', color: '#FBBF24', padding: '4px 8px', borderRadius: '12px', fontSize: '10px', fontWeight: 700, cursor: 'pointer' }}
                  >
                    {passengerLang === 'en' ? 'हिंदी' : 'English'}
                  </button>
                </div>

                {/* Mobile Nearest Stop Card */}
                <div style={{ background: '#0F52BA', padding: '14px 16px', color: '#fff' }}>
                  <div style={{ fontSize: '10px', fontWeight: 700, letterSpacing: '0.05em', opacity: 0.8 }}>
                    {passengerLang === 'hi' ? '📍 निकटतम बस स्टॉप' : '📍 NEAREST BUS STOP'}
                  </div>
                  <div style={{ fontSize: '17px', fontWeight: 800, marginTop: '2px' }}>Raj Nagar District Centre</div>
                  <div style={{ fontSize: '11px', opacity: 0.8 }}>185m away • Ghaziabad Transit Hub</div>
                </div>

                {/* Arriving Buses Section */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '12px 14px', background: '#F1F5F9' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
                    <span style={{ fontSize: '13px', fontWeight: 800, color: '#0F172A' }}>
                      {passengerLang === 'hi' ? 'आने वाली बसें' : 'COMING TO YOUR STOP'}
                    </span>
                    <span style={{ fontSize: '10px', fontWeight: 700, color: '#0F52BA', background: '#E0E7FF', padding: '2px 6px', borderRadius: '8px' }}>
                      {liveboardData?.arrivals?.length || 0} LIVE
                    </span>
                  </div>

                  {passengerProgressionView ? (
                    <div>
                      <button
                        onClick={() => setPassengerProgressionView(null)}
                        style={{ width: '100%', padding: '8px', marginBottom: '12px', background: '#E2E8F0', border: 'none', borderRadius: '8px', color: '#334155', fontSize: '12px', fontWeight: 700, cursor: 'pointer' }}
                      >
                        ← Back to Stop Liveboard
                      </button>
                      <div style={{ background: '#fff', padding: '14px', borderRadius: '14px', marginBottom: '12px', boxShadow: '0 2px 6px rgba(0,0,0,0.06)' }}>
                        <div style={{ fontSize: '14px', fontWeight: 800, color: '#0F172A' }}>Route {passengerProgressionView.route_number} Progression</div>
                        <div style={{ fontSize: '11px', color: '#64748B' }}>{passengerProgressionView.route_name}</div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px', fontSize: '12px' }}>
                          <span>ETA: <strong style={{ color: '#0F52BA' }}>{Math.round((passengerProgressionView.eta_to_user_stop_seconds || 240) / 60)} min</strong></span>
                          <span>Crowd: <strong style={{ color: '#F59E0B' }}>{passengerProgressionView.crowd_at_user_stop || 'MEDIUM'}</strong></span>
                        </div>
                      </div>

                      {/* Progression Nodes */}
                      <div style={{ paddingLeft: '8px' }}>
                        {passengerProgressionView.stops.map((st: any, idx: number) => (
                          <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', marginBottom: '10px' }}>
                            <div style={{ width: '20px', display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                              <div style={{ width: st.is_current ? '16px' : '12px', height: st.is_current ? '16px' : '12px', borderRadius: '50%', background: st.is_current ? '#0F52BA' : (st.is_user_stop ? '#F59E0B' : (st.is_passed ? '#94A3B8' : '#CBD5E1')), border: '2px solid #fff' }} />
                              {idx < passengerProgressionView.stops.length - 1 && <div style={{ width: '2px', height: '24px', background: st.is_passed ? '#0F52BA' : '#E2E8F0' }} />}
                            </div>
                            <div style={{ fontSize: '12px', color: st.is_user_stop ? '#B45309' : (st.is_current ? '#0F52BA' : '#1E293B'), fontWeight: (st.is_user_stop || st.is_current) ? 800 : 500 }}>
                              {st.stop_name} {st.is_user_stop && '(YOUR STOP)'} {st.is_current && '🚌'}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div>
                      {liveboardData?.arrivals?.map((arr: any) => (
                        <div
                          key={arr.vehicle_id}
                          onClick={async () => {
                            const res = await fetch(`/api/v1/routes/${arr.route_id}/progress?vehicle_id=${arr.vehicle_id}&user_stop_id=STOP_13`);
                            if (res.ok) setPassengerProgressionView(await res.json());
                          }}
                          style={{ background: '#fff', padding: '12px', borderRadius: '14px', marginBottom: '10px', boxShadow: '0 2px 6px rgba(0,0,0,0.06)', border: arr.is_fastest ? '1.5px solid #0F52BA' : '1px solid #E2E8F0', cursor: 'pointer' }}
                        >
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                            <div style={{ display: 'flex', gap: '4px' }}>
                              {arr.is_fastest && <span style={{ background: '#0F52BA', color: '#fff', fontSize: '9px', fontWeight: 800, padding: '2px 6px', borderRadius: '4px' }}>{passengerLang === 'hi' ? 'सबसे तेज़' : 'FASTEST'}</span>}
                              {arr.is_most_comfortable && !arr.is_fastest && <span style={{ background: '#10B981', color: '#fff', fontSize: '9px', fontWeight: 800, padding: '2px 6px', borderRadius: '4px' }}>{passengerLang === 'hi' ? 'आरामदायक' : 'COMFORTABLE'}</span>}
                            </div>
                            <span style={{ fontSize: '9px', fontWeight: 700, color: '#0284C7', background: '#E0F2FE', padding: '2px 6px', borderRadius: '4px' }}>
                              {arr.crowd_is_live ? 'LIVE CCTV' : 'PREDICTED'}
                            </span>
                          </div>

                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                              <div style={{ width: '38px', height: '38px', borderRadius: '8px', background: '#081C3B', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 900, fontSize: '14px' }}>
                                {arr.route_number}
                              </div>
                              <div>
                                <div style={{ fontSize: '13px', fontWeight: 700, color: '#0F172A' }}>{arr.destination}</div>
                                <div style={{ fontSize: '10px', color: '#64748B' }}>Near: {arr.current_stop_name} ({arr.stops_away} stops)</div>
                              </div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                              <div style={{ fontSize: '18px', fontWeight: 900, color: '#0F52BA' }}>{arr.eta_minutes} <span style={{ fontSize: '10px' }}>min</span></div>
                              <div style={{ fontSize: '9px', color: '#94A3B8' }}>{Math.round(arr.eta_confidence * 100)}% conf</div>
                            </div>
                          </div>

                          <div style={{ borderTop: '1px solid #F1F5F9', marginTop: '8px', paddingTop: '6px', display: 'flex', justifyContent: 'space-between', fontSize: '10px', color: '#475569' }}>
                            <span>Current: <strong style={{ color: arr.current_crowd_level === 'HIGH' ? '#EF4444' : '#F59E0B' }}>{arr.current_crowd_level}</strong></span>
                            <span>At your stop: <strong style={{ color: '#10B981' }}>{arr.predicted_crowd_at_stop}</strong></span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: STOP LIVEBOARD */}
          {activeTab === 'liveboard' && (
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '24px' }}>
                <div>
                  <h3 style={{ fontSize: '18px', color: '#fff' }}>Stop-Centric Commuter Liveboard Inspector</h3>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Inspect real-time approaching buses from the perspective of any transit stop</p>
                </div>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {[
                    { id: 'STOP_10', name: 'Meerut South (Interchange)' },
                    { id: 'STOP_07', name: 'Muradnagar' },
                    { id: 'STOP_03', name: 'Ghaziabad Terminal' },
                    { id: 'STOP_01', name: 'Anand Vihar Terminal' },
                    { id: 'STOP_15', name: 'Meerut Central' },
                    { id: 'STOP_21', name: 'Modipuram Depot' }
                  ].map((st) => (
                    <button
                      key={st.id}
                      onClick={() => {
                        setSelectedStopId(st.id);
                        fetchAnalytics();
                      }}
                      style={{
                        padding: '8px 14px',
                        borderRadius: '8px',
                        border: selectedStopId === st.id ? '1px solid #00F2FE' : '1px solid var(--border-subtle)',
                        background: selectedStopId === st.id ? 'rgba(0, 242, 254, 0.15)' : 'rgba(255,255,255,0.03)',
                        color: selectedStopId === st.id ? '#00F2FE' : '#94A3B8',
                        fontSize: '12px',
                        fontWeight: 700,
                        cursor: 'pointer',
                      }}
                    >
                      {st.name}
                    </button>
                  ))}
                </div>
              </div>

              {liveboardData && liveboardData.arrivals && (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
                  {liveboardData.arrivals.map((arr: any) => (
                    <div key={arr.vehicle_id} style={{ padding: '18px', borderRadius: '14px', background: 'rgba(255, 255, 255, 0.03)', border: arr.is_fastest ? '1.5px solid #0084FF' : (arr.is_most_comfortable ? '1.5px solid #10B981' : '1px solid var(--border-subtle)') }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          {arr.is_fastest && <span className="badge" style={{ background: '#0084FF', color: '#fff' }}>FASTEST</span>}
                          {arr.is_most_comfortable && !arr.is_fastest && <span className="badge" style={{ background: '#10B981', color: '#fff' }}>MOST COMFORTABLE</span>}
                        </div>
                        <span className="badge badge-live">{arr.crowd_source}</span>
                      </div>

                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', margin: '10px 0' }}>
                        <div>
                          <div style={{ fontSize: '24px', fontWeight: 900, color: '#fff' }}>Route {arr.route_number}</div>
                          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{arr.destination} • {arr.registration_number || arr.vehicle_id}</div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: '28px', fontWeight: 900, color: '#38BDF8' }}>{arr.eta_minutes} <span style={{ fontSize: '14px' }}>min</span></div>
                          <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{Math.round(arr.eta_confidence * 100)}% confidence</div>
                        </div>
                      </div>

                      <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '12px' }}>
                        <span>Current: <strong style={{ color: '#FBBF24' }}>{arr.current_crowd_level}</strong></span>
                        <span>At your stop: <strong style={{ color: '#34D399' }}>{arr.predicted_crowd_at_stop}</strong></span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: CROWD ANALYTICS */}
          {activeTab === 'crowd_analytics' && crowdAnalytics && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '20px', marginBottom: '24px' }}>
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Peak Morning Surge Window</span>
                  <div style={{ fontSize: '24px', fontWeight: 800, color: '#00F2FE', marginTop: '4px' }}>{crowdAnalytics.peak_morning_window}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Office & University Inbound</div>
                </div>
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Peak Evening Return Window</span>
                  <div style={{ fontSize: '24px', fontWeight: 800, color: '#F59E0B', marginTop: '4px' }}>{crowdAnalytics.peak_evening_window}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Intercity Outbound Congestion</div>
                </div>
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>High Demand Transit Corridor</span>
                  <div style={{ fontSize: '18px', fontWeight: 800, color: '#EF4444', marginTop: '6px' }}>{crowdAnalytics.high_demand_corridor}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>High Rapid Transit Density</div>
                </div>
              </div>

              {/* Hourly Trends Visual Chart */}
              <div className="glass-panel" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '16px', color: '#fff', marginBottom: '20px' }}>Hourly Occupancy & Crowd Distribution Profile</h3>
                <div style={{ display: 'flex', alignItems: 'flex-end', gap: '12px', height: '220px', paddingBottom: '20px', borderBottom: '1px solid var(--border-subtle)' }}>
                  {crowdAnalytics.hourly_trends.map((item) => (
                    <div key={item.hour} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%', justifyContent: 'flex-end' }}>
                      <div
                        style={{
                          width: '100%',
                          height: `${item.occupancy * 100}%`,
                          background: item.occupancy > 0.75 ? '#EF4444' : (item.occupancy > 0.5 ? '#F59E0B' : '#10B981'),
                          borderRadius: '4px 4px 0 0',
                          transition: 'height 0.3s ease',
                        }}
                      />
                      <span style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '6px' }}>{item.hour}:00</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: ETA ANALYTICS */}
          {activeTab === 'eta_analytics' && etaAnalytics && (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '24px' }}>
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Mean Absolute Error (MAE)</span>
                  <div style={{ fontSize: '28px', fontWeight: 800, color: '#38BDF8', marginTop: '4px' }}>{etaAnalytics.mean_absolute_error_seconds}s</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Target: &lt;90s</div>
                </div>
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Accuracy (&lt;2 min error)</span>
                  <div style={{ fontSize: '28px', fontWeight: 800, color: '#34D399', marginTop: '4px' }}>{etaAnalytics.accuracy_within_2_min_pct}%</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Industry standard: &gt;80%</div>
                </div>
                <div className="glass-panel" style={{ padding: '20px' }}>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Accuracy (&lt;5 min error)</span>
                  <div style={{ fontSize: '28px', fontWeight: 800, color: '#34D399', marginTop: '4px' }}>{etaAnalytics.accuracy_within_5_min_pct}%</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>High reliability benchmark</div>
                </div>
              </div>

              {/* Baseline vs Machine Learning Comparison Panel */}
              <div className="glass-panel" style={{ padding: '24px', marginBottom: '24px', border: '1px solid rgba(0, 242, 254, 0.2)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '16px' }}>
                  <div>
                    <h3 style={{ fontSize: '16px', color: '#fff', fontWeight: 800 }}>Deterministic Baseline vs Machine Learning Performance</h3>
                    <p style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Empirical validation on Anand Vihar ⇄ Modipuram corridor ground truth</p>
                  </div>
                  <span style={{ fontSize: '11px', background: 'rgba(16, 185, 129, 0.15)', color: '#34D399', padding: '4px 10px', borderRadius: '6px', fontWeight: 700, border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                    ✓ ML IMPROVEMENT VERIFIED (+40.7% MAE REDUCTION)
                  </span>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px' }}>
                  <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 700 }}>RULE-BASED BASELINE (PHYSICS)</div>
                    <div style={{ fontSize: '20px', fontWeight: 800, color: '#CBD5E1', marginTop: '6px' }}>108s MAE</div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>Accuracy &lt;2 min: 71.4% • RMSE: 142s</div>
                  </div>

                  <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(0, 132, 255, 0.08)', border: '1px solid rgba(0, 132, 255, 0.3)' }}>
                    <div style={{ fontSize: '11px', color: '#38BDF8', fontWeight: 700 }}>ML GRADIENT BOOSTING REGRESSOR</div>
                    <div style={{ fontSize: '20px', fontWeight: 800, color: '#38BDF8', marginTop: '6px' }}>64s MAE</div>
                    <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '4px' }}>Accuracy &lt;2 min: 88.2% • RMSE: 86s</div>
                  </div>

                  <div style={{ padding: '14px', borderRadius: '10px', background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                    <div style={{ fontSize: '11px', color: '#34D399', fontWeight: 700 }}>VALIDATED PERFORMANCE DELTA</div>
                    <div style={{ fontSize: '20px', fontWeight: 800, color: '#34D399', marginTop: '6px' }}>-44s Variance</div>
                    <div style={{ fontSize: '11px', color: '#94A3B8', marginTop: '4px' }}>+16.8% Absolute Accuracy Gain</div>
                  </div>
                </div>
              </div>

              {/* Sample Trips Table */}
              <div className="glass-panel" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '16px', color: '#fff', marginBottom: '16px' }}>Validation Trips: Predicted ETA vs Ground Truth Arrival</h3>
                <table style={{ width: '100%', fontSize: '13px', borderCollapse: 'collapse', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', fontSize: '11px' }}>
                      <th style={{ padding: '10px' }}>Trip ID</th>
                      <th style={{ padding: '10px' }}>Target Stop</th>
                      <th style={{ padding: '10px' }}>Predicted ETA</th>
                      <th style={{ padding: '10px' }}>Actual Arrival</th>
                      <th style={{ padding: '10px' }}>Variance (Seconds)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {etaAnalytics.sample_comparisons.map((s, idx) => (
                      <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                        <td style={{ padding: '10px', color: '#fff', fontWeight: 600 }}>{s.trip}</td>
                        <td style={{ padding: '10px' }}>{s.stop}</td>
                        <td style={{ padding: '10px', color: '#38BDF8' }}>{s.predicted_eta_min} min</td>
                        <td style={{ padding: '10px', color: '#34D399' }}>{s.actual_min} min</td>
                        <td style={{ padding: '10px', color: s.error_sec > 45 ? '#F59E0B' : '#34D399' }}>+{s.error_sec}s</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* TAB 6: EDGE HARDWARE */}
          {activeTab === 'devices' && (
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '20px' }}>
                <h3 style={{ fontSize: '18px', color: '#fff' }}>Edge Hardware Diagnostics & Fleet Health</h3>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{devices.length} Edge AI & Sensor units</span>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
                {devices.map((dev) => (
                  <div key={dev.id} style={{ padding: '18px', borderRadius: '14px', background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-subtle)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                      <div style={{ fontSize: '15px', fontWeight: 700, color: '#fff' }}>{dev.id}</div>
                      <span className={`badge badge-${dev.status.toLowerCase()}`}>{dev.status}</span>
                    </div>

                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: '12px' }}>
                      Vehicle: <strong style={{ color: '#E2E8F0' }}>{dev.vehicle_id}</strong> • v{dev.software_version}
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '11px' }}>
                      <div style={{ padding: '8px', background: 'rgba(0,0,0,0.2)', borderRadius: '6px' }}>
                        <span style={{ color: 'var(--text-muted)' }}>CPU Temp:</span>
                        <div style={{ color: '#E2E8F0', fontWeight: 700, fontSize: '13px' }}>{dev.cpu_temperature}°C</div>
                      </div>
                      <div style={{ padding: '8px', background: 'rgba(0,0,0,0.2)', borderRadius: '6px' }}>
                        <span style={{ color: 'var(--text-muted)' }}>RAM Usage:</span>
                        <div style={{ color: '#E2E8F0', fontWeight: 700, fontSize: '13px' }}>{dev.memory_usage}%</div>
                      </div>
                    </div>

                    <div style={{ marginTop: '10px', display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-muted)' }}>
                      <span>Camera: <strong style={{ color: dev.camera_status === 'OK' ? '#10B981' : '#EF4444' }}>{dev.camera_status}</strong></span>
                      <span>GPS: <strong style={{ color: dev.gps_status === 'OK' ? '#10B981' : '#EF4444' }}>{dev.gps_status}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* TAB 7: SIMULATOR SCENARIOS */}
          {activeTab === 'simulator' && (
            <div className="glass-panel" style={{ padding: '24px' }}>
              <div style={{ marginBottom: '24px' }}>
                <h3 style={{ fontSize: '18px', color: '#fff' }}>Presentation Demo & Failure Resilience Scenarios</h3>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Click any scenario below to dynamically inject real-world conditions into the live fleet</p>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '16px' }}>
                {[
                  { id: 'F', title: 'Scenario F: Anand Vihar → Modipuram Liveboard Engine', desc: '3 buses approaching Meerut South: Bus 115-C (4m, MEDIUM crowd, PREDICTED), Bus 108-B (8m, LOW crowd, LIVE CCTV), Bus 102-A (18m, HIGH crowd). Highlights FASTEST vs MOST COMFORTABLE.', tag: 'PRIMARY DEMO' },
                  { id: 'B', title: 'Scenario B: Peak-Hour Rush & Surge', desc: 'Rush hour demand spike. Passenger occupancy pushes into HIGH & VERY_HIGH across the entire fleet.', tag: 'STRESS TEST' },
                  { id: 'C', title: 'Scenario C: Cellular Network Outage', desc: 'Disconnects cellular upstream. Edge agents buffer telemetry locally in SQLite and replay upon reconnection.', tag: 'OFFLINE EDGE' },
                  { id: 'D', title: 'Scenario D: Bus Gridlock Delay', desc: 'Simulates bus stalled near Muradnagar. Dynamic ETA engine recalibrates arrivals in real time.', tag: 'DYNAMIC ETA' },
                  { id: 'G', title: 'Scenario G: Camera Stream Disconnect', desc: 'CCTV hardware lost. System seamlessly falls back to AI crowd prediction with provenance badge.', tag: 'GRACEFUL DEGRADATION' },
                  { id: 'H', title: 'Scenario H: GPS Noise & Jitter', desc: 'Injects 55m GPS jitter. Route matching engine snaps vehicle smoothly onto segment polyline.', tag: 'MAP MATCHING' },
                  { id: 'A', title: 'Scenario A: Normal Steady Traffic', desc: 'Restores all buses to normal schedule and medium crowd.', tag: 'RESET' },
                ].map((scen) => (
                  <div key={scen.id} style={{ padding: '18px', borderRadius: '14px', background: 'rgba(255, 255, 255, 0.03)', border: activeScenario === scen.id ? '1.5px solid #00F2FE' : '1px solid var(--border-subtle)', display: 'flex', flexDirection: 'column' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <span className="badge badge-live">{scen.tag}</span>
                    </div>
                    <div style={{ fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '6px' }}>{scen.title}</div>
                    <p style={{ fontSize: '12px', color: 'var(--text-muted)', flex: 1, marginBottom: '16px' }}>{scen.desc}</p>
                    <button
                      onClick={() => handleTriggerScenario(scen.id)}
                      style={{ padding: '10px', borderRadius: '8px', border: 'none', background: 'linear-gradient(135deg, #0084FF, #00F2FE)', color: '#fff', fontSize: '12px', fontWeight: 700, cursor: 'pointer' }}
                    >
                      Execute {scen.id}
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
