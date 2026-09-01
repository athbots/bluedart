"""
Integration Tests for FastAPI Endpoints.
Verifies REST APIs, stop discovery, liveboard generation, telemetry ingestion, and simulator triggers.
"""

import pytest
from fastapi.testclient import TestClient
from services.api.app.main import app
from services.api.app.core.database import SessionLocal, init_db
from scripts.seed_data import seed_database

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    seed_database()


def test_health_endpoints():
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json()["status"] == "healthy"

    r2 = client.get("/ready")
    assert r2.status_code == 200
    assert r2.json()["status"] == "ready"


def test_nearby_stops():
    # Query near Anand Vihar (28.6469, 77.3161)
    res = client.get("/api/v1/stops/nearby?lat=28.6469&lon=77.3161&radius_meters=3000")
    assert res.status_code == 200
    stops = res.json()
    assert len(stops) > 0
    assert stops[0]["id"] == "STOP_01"  # Anand Vihar ISBT
    assert stops[0]["distance_meters"] < 50.0


def test_stop_detail():
    res = client.get("/api/v1/stops/STOP_01")
    assert res.status_code == 200
    assert "Anand Vihar" in res.json()["name"]


def test_routes_list_and_detail():
    res = client.get("/api/v1/routes")
    assert res.status_code == 200
    routes = res.json()
    assert len(routes) >= 4

    r_detail = client.get("/api/v1/routes/ROUTE_AV_MOD")
    assert r_detail.status_code == 200
    assert len(r_detail.json()["stops"]) == 21


def test_telemetry_ingestion_and_live_state():
    # 1. Ingest GPS location
    loc_payload = {
        "vehicle_id": "BUS_201_A",
        "latitude": 28.6499,
        "longitude": 77.3398,
        "speed": 30.5,
        "heading": 85.0,
        "source": "GPS_HARDWARE",
    }
    r_loc = client.post("/api/v1/device/location", json=loc_payload)
    assert r_loc.status_code == 200
    assert r_loc.json()["status"] == "SUCCESS"

    # 2. Ingest Crowd observation
    crowd_payload = {
        "vehicle_id": "BUS_201_A",
        "occupancy_score": 0.78,
        "crowd_level": "HIGH",
        "confidence": 0.94,
        "source": "EDGE_CAMERA",
    }
    r_crowd = client.post("/api/v1/device/crowd", json=crowd_payload)
    assert r_crowd.status_code == 200

    # 3. Verify Live Bus State endpoint
    r_bus = client.get("/api/v1/buses/BUS_201_A")
    assert r_bus.status_code == 200
    state = r_bus.json()
    assert state["crowd_level"] == "HIGH"
    assert state["is_live"] is True


def test_simulator_trigger_scenario_f():
    # Trigger critical 3-bus approaching stop liveboard demo
    res = client.post("/api/v1/simulator/scenario/F")
    assert res.status_code == 200
    assert res.json()["scenario"] == "F"

    # Fetch arrivals for Stop 13 (Raj Nagar)
    liveboard = client.get("/api/v1/stops/STOP_13/arrivals")
    assert liveboard.status_code == 200
    data = liveboard.json()
    assert "arrivals" in data
