# Edge Computing & Privacy-First Video Processing

## 1. Privacy-First Philosophy

In strict compliance with Product Rule 5:
- **No Face Recognition**: The edge software does not identify individuals or record facial biometric data.
- **No Raw Video Transmission**: Video frames remain in local RAM on the edge computer and are discarded immediately after feature extraction. Only anonymous metadata is transmitted over cellular networks.

---

## 2. Occupancy Extraction Pipeline

```
Frame Capture (30 FPS)
       ↓
Preprocessing (320x240, Gaussian Blur)
       ↓
Background Subtraction (MOG2) & Morphological Filtering
       ↓
Blob Contour Analysis & Density Ratio Calculation
       ↓
Temporal Filter & Hysteresis Smoothing (Anti-flicker)
       ↓
Anonymous Metadata Output (occupancy_score, crowd_level, confidence)
```

---

## 3. Offline Buffering & Resilient Reconnection

Edge devices operating on Indian buses experience cellular dead zones. The edge agent uses an embedded SQLite database (`edge_buffer.db`):
1. When cellular connection drops, telemetry events are queued into SQLite.
2. An exponential backoff loop continuously attempts synchronization.
3. Upon reconnection, buffered records are flushed in chronological order with unique `message_id` UUIDs to ensure backend idempotency.
4. Records are purged only after HTTP 200/201 acknowledgement.
