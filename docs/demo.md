# Presentation & Demo Scenario Guide
### *Anand Vihar -> Modipuram Transit Corridor & 3D Progression*

This guide details the step-by-step procedure to demonstrate the full capabilities of the Smart Transit Intelligence System and its Transit Truth & Reliability Layer.

DATA INTEGRITY:
DEMO_CORRIDOR = True
DATA_CLASSIFICATION = "DEMONSTRATION"

---

## 1. Key Automated Scenario: Scenario F (Liveboard Decision Engine)

Run the reproducible demonstration:
```bash
python scripts/demo_runner.py --scenario ANAND_VIHAR_MODIPURAM --seed 42 --speed 1.0
```

### What It Demonstrates:
1. Seeds 21 Anand Vihar -> Modipuram transit stops and 4 bidirectional routes.
2. Initializes the physics fleet simulator deterministically with seed `42`.
3. Positions 3 buses approaching **Meerut South (`STOP_10`)**:
   - **Bus 115-C**: ETA ~4 min, **MEDIUM** crowd (Source: `PREDICTED` | Status: `OBSERVED`) -> Tagged `[FASTEST]`
   - **Bus 108-B**: ETA ~8 min, **LOW** crowd (Source: `EDGE_CAMERA` | Status: `LIVE`) -> Tagged `[MOST COMFORTABLE]`
   - **Bus 102-A**: ETA ~18 min, **HIGH** crowd (Source: `EDGE_CAMERA` | Status: `LIVE`)
4. The Transit Truth Engine dynamically computes:
   - `[FASTEST]` for Bus 115-C.
   - `[MOST COMFORTABLE]` for Bus 108-B.
5. Displays the 3D-style transit route progression with 21 stops, distance to each stop in meters/km, and commuter's target stop highlighted as `[YOUR STOP]`.

---

## 2. Interactive Scenarios Triggerable from Admin Dashboard

Access `http://localhost:3000` -> **Fleet Simulator** tab:
- **Scenario F**: Anand Vihar -> Modipuram Liveboard Decision Engine
- **Scenario A**: Normal Traffic & Steady Flow across corridor
- **Scenario B**: Peak-Hour Crowd Surge (>85% occupancy)
- **Scenario C**: Cellular Network Outage & Offline SQLite Buffer Replay
- **Scenario D**: Bus Gridlock Delay near Muradnagar & Dynamic Recalibration
- **Scenario G**: Camera Hardware Disconnect & Graceful Fallback to ML Prediction
- **Scenario H**: GPS Jitter (55m) & Map-Matching Polyline Snapping
- **Scenario I**: Stale GPS Telemetry Injection (Tags data as `DATA DELAYED` / `STALE`)
- **Scenario J**: Out-of-Order Packet Injection (Rejects late packet overwrite)
- **Scenario K**: Duplicate Telemetry Packet Replay (Verifies idempotency deduplication)
