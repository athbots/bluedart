"""
Tests for Vehicle Capability Resolution.
Verifies dynamic source strategy selection based on vehicle hardware and operating state.
"""

import pytest
from services.api.app.core.database import SessionLocal
from services.api.app.services.capability_resolver import CapabilityResolver
from packages.schemas.telemetry import CrowdSource, LocationSource, DeviceStatus
from scripts.seed_data import seed_database


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    seed_database()


def test_capability_resolver_ebus_with_cctv():
    db = SessionLocal()
    try:
        # Modern E-Bus (BUS_201_A) has CCTV and GPS
        caps = CapabilityResolver.resolve_capabilities_for_vehicle(db, "BUS_201_A")
        assert caps["gps_available"] is True
        assert caps["cctv_available"] is True

        source = CapabilityResolver.get_preferred_crowd_source(caps, is_camera_stream_healthy=True)
        assert source == CrowdSource.EDGE_CAMERA

        loc_source = CapabilityResolver.get_preferred_location_source(caps)
        assert loc_source == LocationSource.OFFICIAL_GPS
    finally:
        db.close()


def test_capability_resolver_traditional_or_degraded_bus():
    db = SessionLocal()
    try:
        # Simulate traditional bus without CCTV
        traditional_caps = {
            "gps_available": True,
            "cctv_available": False,
            "edge_camera_available": False,
            "crowd_sensor_available": False,
            "prediction_available": True,
            "device_status": DeviceStatus.ONLINE.value,
        }

        source = CapabilityResolver.get_preferred_crowd_source(traditional_caps)
        assert source == CrowdSource.PREDICTED

        # Simulate degraded camera stream on e-bus
        ebus_caps = {
            "gps_available": True,
            "cctv_available": True,
            "edge_camera_available": True,
            "crowd_sensor_available": False,
            "prediction_available": True,
            "device_status": DeviceStatus.ONLINE.value,
        }
        source_degraded = CapabilityResolver.get_preferred_crowd_source(ebus_caps, is_camera_stream_healthy=False)
        assert source_degraded == CrowdSource.PREDICTED
    finally:
        db.close()
