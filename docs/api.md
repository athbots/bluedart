# API Contract Documentation

Base URL: `/api/v1`

## 1. Stop Endpoints

### `GET /stops/nearby`
Finds nearest stops relative to commuter coordinates.
- **Parameters**: `lat` (float), `lon` (float), `radius_meters` (float, default 5000)
- **Response**: Array of `StopWithDistance`

### `GET /stops/{stop_id}`
Retrieves stop metadata.

### `GET /stops/{stop_id}/arrivals`
**Stop-Centric Liveboard**: Returns all approaching active buses serving this stop in order of arrival time.
- **Response**:
```json
{
  "stop": {
    "id": "STOP_13",
    "name": "Raj Nagar District Centre (RDC)"
  },
  "total_arrivals": 3,
  "arrivals": [
    {
      "vehicle_id": "BUS_201_A",
      "route_number": "201",
      "destination": "Raj Nagar Ext",
      "eta_minutes": 4,
      "eta_seconds": 240,
      "eta_confidence": 0.88,
      "is_fastest": true,
      "is_most_comfortable": false,
      "current_crowd_level": "HIGH",
      "crowd_source": "EDGE_CAMERA",
      "crowd_is_live": true,
      "predicted_crowd_at_stop": "VERY_HIGH",
      "prediction_confidence": 0.82
    }
  ]
}
```

---

## 2. Route Endpoints

### `GET /routes`
List all active transit routes.

### `GET /routes/{route_id}`
Full route detail with ordered sequence of stops per direction.

### `GET /routes/{route_id}/progress`
Train-style linear progression timeline for active bus:
- **Parameters**: `vehicle_id` (string), `user_stop_id` (optional string)

---

## 3. Device Ingestion Endpoints

### `POST /device/location`
Ingests GPS coordinate, speed, heading, and accuracy.

### `POST /device/crowd`
Ingests edge crowd metadata (occupancy score 0.0-1.0, crowd level, confidence).

### `POST /device/heartbeat`
Ingests hardware health diagnostics (CPU temperature, RAM, storage, camera & GPS status).

---

## 4. WebSockets

- `/ws/stops/{stop_id}`: Continuous arrival board updates for passengers.
- `/ws/buses/{bus_id}`: Real-time telemetry and progression stream for a single bus.
- `/ws/fleet`: Global fleet coordinate stream for admin radar map.
