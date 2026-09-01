# Production Hardware Integration Guide

The Smart Transit Intelligence System is completely **hardware-agnostic**. Physical hardware devices interact with the platform through standardized, decoupled interfaces without modifying core backend business logic.

---

## 1. Hardware Architecture Models

```
Option A: Smart Bus with Existing NVR / RTSP IP Cameras
┌──────────────┐      RTSP Stream      ┌─────────────────┐      MQTT / REST      ┌─────────────────┐
│ Bus IP CCTV  ├──────────────────────►│ Jetson / Pi 5   ├──────────────────────►│ Transit Backend │
└──────────────┘                       │ Edge Agent      │                       └─────────────────┘
                                       └─────────────────┘

Option B: Low-Cost Fleet Retrofit (ESP32-CAM / Sensor Node)
┌──────────────┐      HTTP Metadata    ┌─────────────────┐      MQTT Telemetry   ┌─────────────────┐
│ ESP32-CAM    ├──────────────────────►│ Cellular 4G     ├──────────────────────►│ Transit Backend │
│ Crowd Sensor │                       │ Gateway         │                       └─────────────────┘
└──────────────┘                       └─────────────────┘

Option C: AIS-140 / VLTD Standard GPS Devices (Indian Transport Standard)
┌──────────────┐      TCP / NMEA 0183  ┌─────────────────┐      REST Ingestion   ┌─────────────────┐
│ AIS-140 GPS  ├──────────────────────►│ Ingestion       ├──────────────────────►│ Transit Backend │
│ VLTD Box     │                       │ Adapter Proxy   │                       └─────────────────┘
└──────────────┘                       └─────────────────┘
```

---

## 2. Implementing New Hardware Adapters

To integrate a new camera or GPS vendor, implement the standard Python interface in `edge/camera_adapter/base.py`:

```python
class CustomHardwareCameraProvider(CameraProvider):
    async def start(self) -> bool:
        # Initialize vendor SDK / connection
        return True

    async def get_frame(self) -> Optional[np.ndarray]:
        # Return frame as BGR numpy array
        return frame

    async def stop(self):
        # Cleanup
        pass

    def get_status(self) -> Dict[str, Any]:
        return {"status": "ONLINE", "provider_type": "VENDOR_CUSTOM"}
```

---

## 3. MQTT Topic and Payload Contract

Topics:
- `transit/{vehicle_id}/location`
- `transit/{vehicle_id}/crowd`
- `transit/{vehicle_id}/health`

Example Crowd Metadata Payload:
```json
{
  "vehicle_id": "BUS_201_A",
  "timestamp": "2026-09-01T10:30:00Z",
  "occupancy_score": 0.76,
  "crowd_level": "HIGH",
  "confidence": 0.94,
  "source": "EDGE_CAMERA",
  "message_id": "8f3b2e7a-9a84-46b5-9f5a-c603b5a1b321"
}
```
