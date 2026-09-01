# System Architecture & Transit Truth Layer
### *Smart Transit Intelligence System*

DATA INTEGRITY:
DEMO_CORRIDOR = True
DATA_CLASSIFICATION = "DEMONSTRATION"

## 1. Core Operating Principle: TRACK → ESTIMATE → PREDICT → INFORM

```
                               ┌───────────────────────────┐
                               │        BUS FLEET          │
                               └─────────────┬─────────────┘
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       │                                           │
                GPS / ITS Feed                               CCTV / Sensor
            (device_timestamp)                           (device_timestamp)
                       │                                           │
                       ▼                                           ▼
            GPS Telemetry Provider                       Edge Agent Pipeline
                       │                               (Frame Preprocess → OpenCV
                       │                                Occupancy → Temporal Filter
                       │                                → SQLite Offline Buffer)
                       │                                           │
                       └─────────────────────┬─────────────────────┘
                                             │
                                   REST / MQTT Ingestion
                               (server_received_timestamp)
                                             │
                                             ▼
                               ┌───────────────────────────┐
                               │   TRANSIT TRUTH ENGINE    │
                               │  - Authoritative Decision │
                               │  - Monotonic Timestamping │
                               │  - Out-of-Order Rejection │
                               │  - Capability Resolution  │
                               │  - Hybrid ETA & Progress  │
                               │  - Data Provenance Builder│
                               └──────┬─────────────┬──────┘
                                      │             │
                    ┌─────────────────┴────┐   ┌────┴────────────────┐
                    ▼                      ▼   ▼                     ▼
             PostgreSQL / SQLite      Live State Store          ML Registry
             - Historical Trips       (In-Memory / Redis)      (Random Forest,
             - Predictions vs Actual  - Monotonic Ordering      Gradient Boosting,
             - Ground Truth Logs      - WebSocket Dispatch      Deterministic Base)
                    │                      │                         │
                    └─────────────────┬────┴─────────────────────────┘
                                      │
                                WebSocket / REST
                               (Standardized Provenance)
                                      │
                        ┌─────────────┴─────────────┐
                        ▼                           ▼
              Passenger Mobile App          Admin Dashboard
             (Flutter / Dart Android)     (React + TypeScript)
              - Nearest Stop                 - 3D Transit Corridor Radar
              - Truth-Resolved Liveboard     - 2D GIS Radar Map
              - 3D Route Progression         - Transit Truth Drawer
              - Fastest vs Comfortable       - Model Drift Health
```

---

## 2. Transit Truth Engine: Single Source of Truth

No frontend or external service independently determines whether data is "live", "predicted", "stale", or "unavailable". The **Transit Truth Engine** (`services/api/app/services/truth_engine.py`) serves as the single authoritative decision layer.

### Location Truth Hierarchy:
1. Fresh trusted `OFFICIAL_GPS` (< 30s)
2. Fresh trusted `EDGE_GPS` (< 30s)
3. Validated recent observation (30s – 60s, `OBSERVED`)
4. Stale location (60s – 300s, `STALE`)
5. Fallback / `UNAVAILABLE` (> 300s)

*A prediction never overwrites a fresh live observation.*

### Crowd Truth Hierarchy:
1. Fresh validated `EDGE_CAMERA` observation (< 60s, `LIVE`)
2. Fresh `EDGE_SENSOR` hardware observation (< 60s, `LIVE`)
3. Recent trusted observation (60s – 120s, `OBSERVED`)
4. ML Prediction (`PREDICTED`, `is_live=False`)
5. Deterministic Historical Baseline
6. `UNAVAILABLE`

### ETA Truth Rules:
- Combines current route segment progress, live vehicle speed, historical median segment travel times, dwell times, and peak-hour traffic multipliers.
- Old predictions are strictly prohibited from overriding newer live progress.

---

## 3. Telemetry Timestamps & Out-of-Order Rejection

All telemetry records maintain two explicit timestamps:
- `device_timestamp`: Time when the physical sensor took the measurement.
- `server_received_timestamp`: Time when the backend received the packet.

### Replay & Out-of-Order Protection:
When a packet arrives with `device_timestamp < last_recorded_device_timestamp`, it is classified as out-of-order and **will not overwrite** the active live state in the cache.

---

## 4. 3D Transit Corridor Progression Engine

The progression service (`services/api/app/services/progression_service.py`) calculates:
- Isometric perspective coordinates for 21 stops along the Anand Vihar → Modipuram corridor.
- Dynamic distance from the active vehicle to every upcoming stop in meters and kilometers.
- Commuter stop targeting (`is_user_stop=True`) with arrival ETAs.
- Forward (`OUTBOUND`) and Reverse (`INBOUND`) directional sequence modeling.
