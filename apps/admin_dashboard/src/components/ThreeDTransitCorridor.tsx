import React, { useState, useEffect, useRef } from 'react';

export interface RouteProgressionNode {
  stop_id: string;
  stop_name: string;
  display_name?: string;
  sequence: number;
  latitude: number;
  longitude: number;
  cumulative_distance_meters: number;
  stop_type: string;
  is_major_stop: boolean;
  is_interchange_stop: boolean;
  is_terminal_stop: boolean;
  is_depot: boolean;
  is_passed: boolean;
  is_current: boolean;
  is_next: boolean;
  is_user_stop: boolean;
  distance_from_bus_meters?: number;
  estimated_arrival_seconds?: number;
  predicted_crowd_level?: string;
  crowd_confidence?: number;
}

export interface RouteProgressionViewData {
  vehicle_id: string;
  registration_number?: string;
  route_id: string;
  route_number: string;
  route_name: string;
  direction: string;
  origin: string;
  destination: string;
  current_speed_kmh: number;
  route_progress_percentage: number;
  stops_passed_count: number;
  total_stops_count: number;
  current_stop_name?: string;
  next_major_stop_name?: string;
  current_bus_latitude?: number;
  current_bus_longitude?: number;
  stops: RouteProgressionNode[];
  user_stop_id?: string;
  user_stop_name?: string;
  eta_to_user_stop_seconds?: number;
  crowd_at_user_stop?: string;
  provenance?: any;
  demo_corridor?: boolean;
}

interface Props {
  progressionData: RouteProgressionViewData;
  onSelectStop?: (stopId: string) => void;
  selectedUserStopId?: string;
}

export const ThreeDTransitCorridor: React.FC<Props> = ({
  progressionData,
  onSelectStop,
  selectedUserStopId = 'STOP_10',
}) => {
  const [cameraMode, setCameraMode] = useState<'OVERVIEW' | 'FOLLOW_BUS'>('OVERVIEW');
  const [inspectedStop, setInspectedStop] = useState<RouteProgressionNode | null>(null);
  const [animTime, setAnimTime] = useState(0);

  // Subtle continuous animation loop for glowing pulses & bus headlights
  useEffect(() => {
    let animFrame: number;
    const animate = () => {
      setAnimTime((t) => (t + 0.04) % 100);
      animFrame = requestAnimationFrame(animate);
    };
    animFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animFrame);
  }, []);

  const stops = progressionData.stops || [];
  const currentIdx = stops.findIndex((s) => s.is_current);
  const activeStopIdx = currentIdx >= 0 ? currentIdx : 0;
  const progressPct = progressionData.route_progress_percentage || 0;

  // Viewport bounds for camera modes
  const visibleStartIndex = cameraMode === 'FOLLOW_BUS' ? Math.max(0, activeStopIdx - 1) : 0;
  const visibleEndIndex = cameraMode === 'FOLLOW_BUS' ? Math.min(stops.length - 1, activeStopIdx + 6) : stops.length - 1;
  const displayedStops = stops.slice(visibleStartIndex, visibleEndIndex + 1);

  // 3D Isometric projection math for route ribbon
  // Visual rail runs in isometric S-curve with perspective depth
  const getIsoCoords = (index: number, total: number) => {
    const fraction = total > 1 ? index / (total - 1) : 0;
    
    // Isometric depth curve (diagonal perspective from bottom-left to top-right)
    const startX = 80;
    const endX = 740;
    const startY = 460;
    const endY = 90;
    
    // Gentle natural S-curve curvature
    const curveOffset = Math.sin(fraction * Math.PI) * 45;
    
    const x = startX + fraction * (endX - startX) + curveOffset;
    const y = startY - fraction * (startY - endY);
    const zElevation = Math.sin(fraction * Math.PI) * 15; // 3D elevated mid-corridor
    
    return { x, y: y - zElevation, z: zElevation, fraction };
  };

  // Interpolated 3D Bus Position
  const getBusIsoPosition = () => {
    if (stops.length < 2) return { x: 400, y: 300, angle: 0 };
    const globalFrac = Math.max(0, Math.min(1.0, progressPct / 100.0));
    const rawIndex = globalFrac * (stops.length - 1);
    const prevIdx = Math.floor(rawIndex);
    const nextIdx = Math.min(stops.length - 1, prevIdx + 1);
    const segFrac = rawIndex - prevIdx;

    const p1 = getIsoCoords(prevIdx, stops.length);
    const p2 = getIsoCoords(nextIdx, stops.length);

    const busX = p1.x + (p2.x - p1.x) * segFrac;
    const busY = p1.y + (p2.y - p1.y) * segFrac - 12; // Elevated bus clearance
    const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x) * (180 / Math.PI);

    return { x: busX, y: busY, angle };
  };

  const busPos = getBusIsoPosition();

  // Dynamic Camera ViewBox calculation
  const getViewBox = () => {
    if (cameraMode === 'OVERVIEW') {
      return '0 0 820 540';
    }
    // Focused Follow-Bus bounding box with clamping
    const targetW = 480;
    const targetH = 340;
    const minX = Math.max(0, Math.min(820 - targetW, busPos.x - targetW / 2));
    const minY = Math.max(0, Math.min(540 - targetH, busPos.y - targetH / 2));
    return `${minX} ${minY} ${targetW} ${targetH}`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100%', height: '100%', gap: '16px' }}>
      {/* 3D Visual HUD Bar */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ fontSize: '18px', fontWeight: 800, color: '#fff' }}>
              Route {progressionData.route_number}: {progressionData.origin} → {progressionData.destination}
            </span>
            <span style={{ fontSize: '11px', background: 'rgba(0, 242, 254, 0.15)', color: '#00F2FE', padding: '3px 8px', borderRadius: '6px', fontWeight: 700, border: '1px solid rgba(0, 242, 254, 0.3)' }}>
              3D PERSPECTIVE
            </span>
            {progressionData.demo_corridor && (
              <span style={{ fontSize: '10px', background: 'rgba(251, 191, 36, 0.15)', color: '#FBBF24', padding: '2px 6px', borderRadius: '4px', border: '1px solid rgba(251, 191, 36, 0.3)' }}>
                DEMO CORRIDOR
              </span>
            )}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
            Progress: <strong style={{ color: '#38BDF8' }}>{progressPct}%</strong> • Stops Passed: <strong style={{ color: '#E2E8F0' }}>{progressionData.stops_passed_count} / {progressionData.total_stops_count}</strong> • Next Major: <strong style={{ color: '#00F2FE' }}>{progressionData.next_major_stop_name}</strong>
          </div>
        </div>

        {/* Camera Controls */}
        <div style={{ display: 'flex', gap: '8px', background: 'rgba(255,255,255,0.04)', padding: '4px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
          <button
            onClick={() => setCameraMode('OVERVIEW')}
            style={{
              padding: '6px 14px',
              borderRadius: '8px',
              border: 'none',
              background: cameraMode === 'OVERVIEW' ? '#0084FF' : 'transparent',
              color: cameraMode === 'OVERVIEW' ? '#fff' : 'var(--text-muted)',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            🌐 OVERVIEW CORRIDOR
          </button>
          <button
            onClick={() => setCameraMode('FOLLOW_BUS')}
            style={{
              padding: '6px 14px',
              borderRadius: '8px',
              border: 'none',
              background: cameraMode === 'FOLLOW_BUS' ? '#00F2FE' : 'transparent',
              color: cameraMode === 'FOLLOW_BUS' ? '#070B14' : 'var(--text-muted)',
              fontSize: '12px',
              fontWeight: 700,
              cursor: 'pointer',
              transition: 'all 0.2s ease',
            }}
          >
            🚌 FOLLOW BUS
          </button>
        </div>
      </div>

      {/* 3D Perspective Isometric Canvas */}
      <div style={{ display: 'grid', gridTemplateColumns: inspectedStop ? '1fr 320px' : '1fr', gap: '16px', flex: 1, minHeight: '520px' }}>
        <div
          style={{
            position: 'relative',
            background: 'radial-gradient(ellipse at 50% 40%, #0F172A 0%, #070B14 100%)',
            borderRadius: '16px',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            overflow: 'hidden',
            boxShadow: 'inset 0 0 60px rgba(0, 0, 0, 0.6)',
          }}
        >
          {/* Depth Grid Lines */}
          <svg width="100%" height="100%" viewBox={getViewBox()} style={{ display: 'block', transition: 'viewBox 0.4s ease-out' }}>
            <defs>
              {/* Glowing Gradient Filters */}
              <linearGradient id="activeRailGrad" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#0084FF" />
                <stop offset="50%" stopColor="#00F2FE" />
                <stop offset="100%" stopColor="#38BDF8" />
              </linearGradient>
              <linearGradient id="passedRailGrad" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="rgba(100, 116, 139, 0.3)" />
                <stop offset="100%" stopColor="rgba(148, 163, 184, 0.2)" />
              </linearGradient>
              <linearGradient id="upcomingRailGrad" x1="0%" y1="100%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="rgba(56, 189, 248, 0.4)" />
                <stop offset="100%" stopColor="rgba(255, 255, 255, 0.15)" />
              </linearGradient>

              {/* Shadow Filters */}
              <filter id="shadow3D" x="-30%" y="-30%" width="160%" height="160%">
                <feDropShadow dx="0" dy="8" stdDeviation="6" floodColor="#000" floodOpacity="0.7" />
              </filter>
              <filter id="glowNeon" x="-30%" y="-30%" width="160%" height="160%">
                <feGaussianBlur stdDeviation="5" result="coloredBlur"/>
                <feMerge>
                  <feMergeNode in="coloredBlur"/>
                  <feMergeNode in="SourceGraphic"/>
                </feMerge>
              </filter>
            </defs>

            {/* Ground Plane Grid with 3D depth perspective */}
            <g opacity="0.15">
              {[120, 200, 280, 360, 440, 500].map((gy, i) => (
                <line key={`h-${i}`} x1="40" y1={gy} x2="780" y2={gy} stroke="#38BDF8" strokeWidth="1" strokeDasharray="4 8" />
              ))}
              {[100, 220, 340, 460, 580, 700].map((gx, i) => (
                <line key={`v-${i}`} x1={gx} y1="520" x2={gx + 40} y2="60" stroke="#38BDF8" strokeWidth="1" strokeDasharray="4 8" />
              ))}
            </g>

            {/* Layer 1: Ground Projected Route Shadow */}
            <path
              d={stops.map((_, i) => {
                const pt = getIsoCoords(i, stops.length);
                return `${i === 0 ? 'M' : 'L'} ${pt.x} ${pt.y + 16}`;
              }).join(' ')}
              fill="none"
              stroke="rgba(0, 0, 0, 0.5)"
              strokeWidth="14"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Layer 2: Lower Route Bed (Sub-track 3D extrusion) */}
            <path
              d={stops.map((_, i) => {
                const pt = getIsoCoords(i, stops.length);
                return `${i === 0 ? 'M' : 'L'} ${pt.x} ${pt.y + 4}`;
              }).join(' ')}
              fill="none"
              stroke="#0B132B"
              strokeWidth="10"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Layer 3: Elevated Main Route Rails */}
            {/* Passed Rail Segment */}
            <path
              d={stops.slice(0, activeStopIdx + 1).map((_, i) => {
                const pt = getIsoCoords(i, stops.length);
                return `${i === 0 ? 'M' : 'L'} ${pt.x} ${pt.y}`;
              }).join(' ')}
              fill="none"
              stroke="url(#passedRailGrad)"
              strokeWidth="6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Upcoming Rail Segment */}
            <path
              d={stops.slice(activeStopIdx).map((_, i) => {
                const pt = getIsoCoords(activeStopIdx + i, stops.length);
                return `${i === 0 ? 'M' : 'L'} ${pt.x} ${pt.y}`;
              }).join(' ')}
              fill="none"
              stroke="url(#upcomingRailGrad)"
              strokeWidth="5"
              strokeDasharray="6 4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {/* Active Highlight Rail Segment (Glowing) */}
            {stops.length > 1 && (
              <path
                d={stops.slice(Math.max(0, activeStopIdx - 1), Math.min(stops.length, activeStopIdx + 2)).map((_, i) => {
                  const idx = Math.max(0, activeStopIdx - 1) + i;
                  const pt = getIsoCoords(idx, stops.length);
                  return `${i === 0 ? 'M' : 'L'} ${pt.x} ${pt.y}`;
                }).join(' ')}
                fill="none"
                stroke="url(#activeRailGrad)"
                strokeWidth="7"
                filter="url(#glowNeon)"
                strokeLinecap="round"
              />
            )}

            {/* Layer 4: Elevated 3D Stop Nodes */}
            {stops.map((st, i) => {
              const pt = getIsoCoords(i, stops.length);
              const isPassed = i < activeStopIdx;
              const isCurrent = i === activeStopIdx;
              const isUserStop = st.stop_id === selectedUserStopId;
              const isMajor = st.is_major_stop || st.is_interchange_stop || st.is_terminal_stop || st.is_depot;
              const isSelected = inspectedStop?.stop_id === st.stop_id;

              // Node radius & color hierarchy
              const rBase = isMajor ? 9 : 6;
              let fillNode = '#64748B';
              let ringColor = 'transparent';

              if (isUserStop) {
                fillNode = '#F59E0B';
                ringColor = '#FBBF24';
              } else if (isCurrent) {
                fillNode = '#00F2FE';
                ringColor = '#0084FF';
              } else if (isPassed) {
                fillNode = '#334155';
              } else {
                fillNode = isMajor ? '#38BDF8' : '#94A3B8';
              }

              // Label visibility check for overview mode (prevents label clutter)
              const showLabel = cameraMode === 'FOLLOW_BUS' || isMajor || isUserStop || isCurrent || i === 0 || i === stops.length - 1;

              return (
                <g
                  key={st.stop_id}
                  onClick={() => {
                    setInspectedStop(st);
                    if (onSelectStop) onSelectStop(st.stop_id);
                  }}
                  style={{ cursor: 'pointer' }}
                >
                  {/* Node 3D Stilt / Pillar to Ground */}
                  <line x1={pt.x} y1={pt.y} x2={pt.x} y2={pt.y + 14} stroke="rgba(255,255,255,0.15)" strokeWidth="2" />
                  <ellipse cx={pt.x} cy={pt.y + 14} rx="5" ry="2.5" fill="rgba(0,0,0,0.5)" />

                  {/* Outer Pulsing Ring for User Stop or Selected */}
                  {(isUserStop || isSelected) && (
                    <circle
                      cx={pt.x}
                      cy={pt.y}
                      r={rBase + 7 + Math.sin(animTime * 2) * 2}
                      fill="none"
                      stroke={isUserStop ? '#F59E0B' : '#00F2FE'}
                      strokeWidth="2"
                      opacity="0.8"
                    />
                  )}

                  {/* 3D Elevated Disc */}
                  <ellipse cx={pt.x} cy={pt.y + 2} rx={rBase} ry={rBase * 0.75} fill="#0F172A" opacity="0.6" />
                  <circle
                    cx={pt.x}
                    cy={pt.y}
                    r={rBase}
                    fill={fillNode}
                    stroke="#fff"
                    strokeWidth={isMajor ? 2.5 : 1.5}
                    filter={isCurrent || isUserStop ? 'url(#glowNeon)' : undefined}
                  />

                  {/* User Stop Highlight Badge */}
                  {isUserStop && (
                    <g transform={`translate(${pt.x}, ${pt.y - 28})`}>
                      <rect x="-44" y="-12" width="88" height="20" rx="6" fill="#F59E0B" filter="url(#shadow3D)" />
                      <text x="0" y="2" textAnchor="middle" fill="#000" fontSize="9" fontWeight="900">
                        📍 YOUR STOP
                      </text>
                      <polygon points="-5,8 5,8 0,13" fill="#F59E0B" />
                    </g>
                  )}

                  {/* Stop Name Label with anti-collision staggered offsets */}
                  {showLabel && !isUserStop && (
                    <g>
                      <text
                        x={pt.x + (i % 2 === 0 ? 14 : -14)}
                        y={pt.y + (i % 2 === 0 ? -10 : 18)}
                        textAnchor={i % 2 === 0 ? 'start' : 'end'}
                        fill={isMajor ? '#FFFFFF' : '#CBD5E1'}
                        fontSize={isMajor ? 11 : 9.5}
                        fontWeight={isMajor ? 800 : 600}
                        style={{ textShadow: '0 2px 4px rgba(0,0,0,0.9)' }}
                      >
                        {st.stop_name}
                      </text>
                      {st.stop_type !== 'LOCAL' && (
                        <text
                          x={pt.x + (i % 2 === 0 ? 14 : -14)}
                          y={pt.y + (i % 2 === 0 ? 2 : 28)}
                          textAnchor={i % 2 === 0 ? 'start' : 'end'}
                          fill="#38BDF8"
                          fontSize="8"
                          fontWeight="700"
                        >
                          [{st.stop_type}]
                        </text>
                      )}
                    </g>
                  )}
                </g>
              );
            })}

            {/* Layer 5: Dynamic 3D Bus Marker with Headlight Beam */}
            <g transform={`translate(${busPos.x}, ${busPos.y})`} filter="url(#shadow3D)">
              {/* Headlight Beam Cone */}
              <polygon
                points="0,-4 40,-18 40,10"
                fill="rgba(0, 242, 254, 0.15)"
                opacity={0.6 + Math.sin(animTime * 3) * 0.2}
              />

              {/* Pulsing Target Radar Halo */}
              <circle cx="0" cy="0" r={16 + Math.sin(animTime * 2) * 2} fill="none" stroke="#00F2FE" strokeWidth="2" strokeDasharray="3 3" />

              {/* 3D Bus Body (Isometric Capsule) */}
              <rect x="-14" y="-9" width="28" height="18" rx="6" fill="#0284C7" stroke="#fff" strokeWidth="2" />
              <rect x="-10" y="-6" width="20" height="12" rx="3" fill="#0F172A" />

              {/* Bus Windshield & Lights */}
              <rect x="4" y="-5" width="4" height="10" rx="1" fill="#38BDF8" />
              <circle cx="10" cy="-4" r="1.5" fill="#FEF08A" />
              <circle cx="10" cy="4" r="1.5" fill="#FEF08A" />

              {/* Bus Route Label Banner */}
              <g transform="translate(0, -22)">
                <rect x="-32" y="-9" width="64" height="16" rx="5" fill="#0F172A" stroke="#00F2FE" strokeWidth="1.5" />
                <text x="0" y="3" textAnchor="middle" fill="#00F2FE" fontSize="9" fontWeight="900">
                  🚌 {progressionData.route_number || '101'}
                </text>
              </g>
            </g>
          </svg>
        </div>

        {/* Selected Stop Details HUD Drawer */}
        {inspectedStop && (
          <div
            style={{
              background: 'rgba(15, 23, 42, 0.85)',
              backdropFilter: 'blur(16px)',
              borderRadius: '16px',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              padding: '20px',
              display: 'flex',
              flexDirection: 'column',
              gap: '14px',
              boxShadow: '0 20px 40px rgba(0, 0, 0, 0.5)',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}>
              <div>
                <span style={{ fontSize: '10px', color: '#38BDF8', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                  STOP #{inspectedStop.sequence + 1} OF {stops.length}
                </span>
                <h4 style={{ fontSize: '17px', fontWeight: 800, color: '#fff', marginTop: '2px' }}>{inspectedStop.stop_name}</h4>
                <div style={{ fontSize: '11px', color: '#94A3B8' }}>{inspectedStop.display_name}</div>
              </div>
              <button
                onClick={() => setInspectedStop(null)}
                style={{ background: 'transparent', border: 'none', color: '#94A3B8', fontSize: '16px', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
              <span className="badge" style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38BDF8', border: '1px solid rgba(56, 189, 248, 0.3)' }}>
                {inspectedStop.stop_type}
              </span>
              {inspectedStop.is_interchange_stop && (
                <span className="badge" style={{ background: 'rgba(168, 85, 247, 0.15)', color: '#C084FC', border: '1px solid rgba(168, 85, 247, 0.3)' }}>
                  INTERCHANGE
                </span>
              )}
              {inspectedStop.is_depot && (
                <span className="badge" style={{ background: 'rgba(234, 179, 8, 0.15)', color: '#FACC15', border: '1px solid rgba(234, 179, 8, 0.3)' }}>
                  DEPOT
                </span>
              )}
              {inspectedStop.is_passed && (
                <span className="badge" style={{ background: 'rgba(100, 116, 139, 0.2)', color: '#94A3B8' }}>
                  PASSED
                </span>
              )}
              {inspectedStop.is_current && (
                <span className="badge" style={{ background: 'rgba(0, 242, 254, 0.2)', color: '#00F2FE' }}>
                  AT BUS LOCATION
                </span>
              )}
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginTop: '4px' }}>
              <div style={{ padding: '10px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '10px' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700 }}>DISTANCE FROM BUS</span>
                <div style={{ fontSize: '15px', fontWeight: 800, color: '#fff', marginTop: '2px' }}>
                  {inspectedStop.distance_from_bus_meters ? `${(inspectedStop.distance_from_bus_meters / 1000).toFixed(1)} km` : '0 km'}
                </div>
              </div>
              <div style={{ padding: '10px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '10px' }}>
                <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700 }}>ESTIMATED TIME</span>
                <div style={{ fontSize: '15px', fontWeight: 800, color: '#38BDF8', marginTop: '2px' }}>
                  {inspectedStop.estimated_arrival_seconds ? `${Math.round(inspectedStop.estimated_arrival_seconds / 60)} min` : (inspectedStop.is_passed ? 'Passed' : 'Arrived')}
                </div>
              </div>
            </div>

            <div style={{ padding: '12px', background: 'rgba(255, 255, 255, 0.03)', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontWeight: 700, textTransform: 'uppercase' }}>CROWD INTELLIGENCE</span>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 800, color: inspectedStop.predicted_crowd_level === 'HIGH' ? '#EF4444' : '#F59E0B' }}>
                    {inspectedStop.predicted_crowd_level || 'MEDIUM'} CROWD
                  </div>
                  <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>Source: PREDICTED • {Math.round((inspectedStop.crowd_confidence || 0.85) * 100)}% confidence</div>
                </div>
                <button
                  onClick={() => {
                    if (onSelectStop) onSelectStop(inspectedStop.stop_id);
                  }}
                  style={{
                    padding: '6px 10px',
                    borderRadius: '6px',
                    background: inspectedStop.stop_id === selectedUserStopId ? '#10B981' : '#0084FF',
                    border: 'none',
                    color: '#fff',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer',
                  }}
                >
                  {inspectedStop.stop_id === selectedUserStopId ? '✓ YOUR STOP' : 'SET AS MY STOP'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
