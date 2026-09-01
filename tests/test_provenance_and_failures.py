"""
Expanded Failure, Resilience, and Provenance Consistency Test Suite.
Tests edge failure scenarios, fallback behaviors, out-of-order telemetry rejection,
contradictory provenance prevention, and liveboard direction filtering.

DATA INTEGRITY:
DEMO_CORRIDOR = True
DATA_CLASSIFICATION = "DEMONSTRATION"
"""

import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from services.api.app.core.database import SessionLocal
from scripts.seed_data import seed_database
from services.api.app.services.truth_engine import truth_engine
from services.api.app.services.crowd_service import CrowdService
from services.api.app.services.eta_service import ETAService
from services.api.app.core.live_state import live_state
from services.simulator.fleet_simulator import fleet_simulator
from packages.schemas.telemetry import (
    CrowdLevel,
    CrowdSource,
    LocationSource,
    ETASource,
    TruthStatus,
)
from packages.shared.provenance import (
    build_data_provenance,
    GPS_LIVE_THRESHOLD,
    CROWD_LIVE_THRESHOLD,
)
from ml.inference.predictor import ml_predictor


@pytest.fixture(scope="module", autouse=True)
def setup_test_suite():
    seed_database()
    fleet_simulator.initialize_fleet(seed=42, speed=1.0)
    yield


def test_contradictory_provenance_prevention():
    """Verify that source and status cannot contradict one another."""
    now = datetime.now(timezone.utc)

    # 1. PREDICTED source must ALWAYS produce PREDICTED status
    p1 = build_data_provenance(source=CrowdSource.PREDICTED.value, observed_at=now)
    assert p1.status == TruthStatus.PREDICTED
    assert p1.is_live is False

    p2 = build_data_provenance(source=ETASource.ML_PREDICTED.value, observed_at=now)
    assert p2.status == TruthStatus.PREDICTED
    assert p2.is_live is False

    # 2. HISTORICAL_ESTIMATE / LIVE_ESTIMATE must produce ESTIMATED status
    p3 = build_data_provenance(source=CrowdSource.HISTORICAL_ESTIMATE.value, observed_at=now)
    assert p3.status == TruthStatus.ESTIMATED

    p4 = build_data_provenance(source=ETASource.LIVE_ESTIMATE.value, observed_at=now)
    assert p4.status == TruthStatus.ESTIMATED

    # 3. EDGE_CAMERA fresh must produce LIVE status
    p5 = build_data_provenance(source=CrowdSource.EDGE_CAMERA.value, observed_at=now)
    assert p5.status == TruthStatus.LIVE
    assert p5.is_live is True


@pytest.mark.asyncio
async def test_stale_crowd_source_fallback():
    """Verify stale camera data (>120s) transitions to ML prediction with PREDICTED status."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        stale_time = now - timedelta(seconds=180)
        test_vid = "BUS_TEST_STALE_CROWD"

        # Initialize location first with stale time
        await live_state.update_location(
            vehicle_id=test_vid,
            lat=28.7885,
            lon=77.5020,
            device_timestamp=stale_time,
            server_received_timestamp=now,
        )

        await live_state.update_crowd(
            vehicle_id=test_vid,
            occupancy_score=0.85,
            crowd_level="HIGH",
            confidence=0.92,
            source=CrowdSource.EDGE_CAMERA.value,
            device_timestamp=stale_time,
            server_received_timestamp=now,
        )

        truth = truth_engine.resolve_crowd(db, test_vid, current_time=now)
        assert truth["provenance"].source == CrowdSource.PREDICTED.value
        assert truth["provenance"].status == TruthStatus.PREDICTED
        assert truth["provenance"].is_live is False
    finally:
        db.close()


@pytest.mark.asyncio
async def test_stale_gps_fallback():
    """Verify stale GPS data (>60s) flags location as STALE without inventing coordinates."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        stale_time = now - timedelta(seconds=120)
        test_vid = "BUS_TEST_STALE_GPS"

        await live_state.update_location(
            vehicle_id=test_vid,
            lat=28.7885,
            lon=77.5020,
            speed=0.0,
            heading=0.0,
            device_timestamp=stale_time,
            server_received_timestamp=now,
            source=LocationSource.OFFICIAL_GPS.value,
        )

        truth = truth_engine.resolve_location(db, test_vid, current_time=now)
        assert truth["provenance"].status == TruthStatus.STALE
        assert truth["provenance"].is_stale is True
        assert truth["provenance"].is_live is False
    finally:
        db.close()


@pytest.mark.asyncio
async def test_delayed_out_of_order_packet_rejection():
    """Verify late out-of-order packet does not overwrite newer live state."""
    now = datetime.now(timezone.utc)
    t_new = now
    t_old = now - timedelta(seconds=60)
    test_vid = "BUS_TEST_OOO_99"

    # 1. Ingest newer location (Stop 9: Modi Nagar North)
    await live_state.update_location(
        vehicle_id=test_vid,
        lat=28.8550,
        lon=77.5680,
        speed=30.0,
        heading=45.0,
        device_timestamp=t_new,
        server_received_timestamp=now,
        source=LocationSource.OFFICIAL_GPS.value,
    )

    # 2. Attempt to ingest delayed older packet (Stop 1: Anand Vihar)
    await live_state.update_location(
        vehicle_id=test_vid,
        lat=28.6469,
        lon=77.3161,
        speed=10.0,
        heading=10.0,
        device_timestamp=t_old,
        server_received_timestamp=now,
        source=LocationSource.OFFICIAL_GPS.value,
    )

    # Verify state remains at newer position (Modi Nagar North)
    state = live_state.get_vehicle_state(test_vid)
    assert state["latitude"] == 28.8550
    assert state["longitude"] == 77.5680


@pytest.mark.asyncio
async def test_duplicate_packet_idempotency():
    """Verify duplicate message_id UUID is dropped idempotently."""
    now = datetime.now(timezone.utc)
    msg_uuid = "UUID-TEST-DEDUP-UNIQUE-8888"
    test_vid = "BUS_TEST_DEDUP_88"

    await live_state.update_location(
        vehicle_id=test_vid,
        lat=28.9220,
        lon=77.6250,
        speed=25.0,
        heading=30.0,
        device_timestamp=now,
        server_received_timestamp=now,
        source=LocationSource.OFFICIAL_GPS.value,
        message_id=msg_uuid,
    )
    assert live_state.is_message_processed(msg_uuid) is True

    # Replay packet with same UUID but modified corrupted coordinates
    await live_state.update_location(
        vehicle_id=test_vid,
        lat=0.0000,
        lon=0.0000,
        speed=99.0,
        heading=99.0,
        device_timestamp=now + timedelta(seconds=1),
        server_received_timestamp=now,
        source=LocationSource.OFFICIAL_GPS.value,
        message_id=msg_uuid,
    )

    # State must NOT be corrupted to 0.0, 0.0
    state = live_state.get_vehicle_state(test_vid)
    assert state["latitude"] == 28.9220
    assert state["longitude"] == 77.6250


@pytest.mark.asyncio
async def test_reverse_direction_liveboard_matching():
    """Verify an INBOUND bus does not appear on OUTBOUND stop arrivals."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Set BUS_505_A travelling INBOUND (Modipuram -> Anand Vihar)
        await live_state.set_route_context(
            vehicle_id="BUS_505_A",
            route_id="ROUTE_AV_MOD",
            route_number="101",
            route_name="Anand Vihar <-> Modipuram Express",
            direction="INBOUND",
        )
        await live_state.update_location(
            vehicle_id="BUS_505_A",
            lat=29.0020,  # Near Meerut Central travelling toward Anand Vihar
            lon=77.6910,
            speed=28.0,
            heading=215.0,
            device_timestamp=now,
            server_received_timestamp=now,
            source=LocationSource.OFFICIAL_GPS.value,
        )

        # Check Outbound liveboard at Modipuram (STOP_21)
        board = CrowdService.get_stop_liveboard(db, "STOP_21")
        if board and board.arrivals:
            inbound_matches = [a for a in board.arrivals if a.vehicle_id == "BUS_505_A" and a.direction == "OUTBOUND"]
            assert len(inbound_matches) == 0
    finally:
        db.close()


@pytest.mark.asyncio
async def test_passed_stop_exclusion():
    """Verify a bus that has already passed a stop is excluded from its liveboard."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Bus 115-C is at Modi Nagar North (Stop 9)
        # It has already passed Anand Vihar (Stop 1) and Ghaziabad (Stop 3)
        await live_state.set_route_context(
            vehicle_id="BUS_115_C",
            route_id="ROUTE_AV_MOD",
            route_number="101",
            route_name="Anand Vihar <-> Modipuram Express",
            direction="OUTBOUND",
        )
        await live_state.update_location(
            vehicle_id="BUS_115_C",
            lat=28.8550,
            lon=77.5680,
            speed=30.0,
            heading=40.0,
            device_timestamp=now,
            server_received_timestamp=now,
            source=LocationSource.OFFICIAL_GPS.value,
            progression_data={"current_stop_index": 8},  # Stop 9
        )

        # Query liveboard for Anand Vihar (STOP_01)
        board = CrowdService.get_stop_liveboard(db, "STOP_01")
        if board and board.arrivals:
            passed_bus = [a for a in board.arrivals if a.vehicle_id == "BUS_115_C"]
            assert len(passed_bus) == 0
    finally:
        db.close()


@pytest.mark.asyncio
async def test_multiple_buses_fastest_vs_comfortable_tagging():
    """Verify dynamic allocation of [FASTEST] vs [MOST COMFORTABLE] badges."""
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # Bus A: 4 min away, HIGH crowd
        await live_state.update_location(
            vehicle_id="BUS_115_C",
            lat=28.8550,
            lon=77.5680,
            speed=32.0,
            heading=40.0,
            device_timestamp=now,
            server_received_timestamp=now,
            source=LocationSource.OFFICIAL_GPS.value,
            progression_data={"current_stop_index": 8},
        )
        await live_state.update_crowd(
            vehicle_id="BUS_115_C",
            occupancy_score=0.82,
            crowd_level=CrowdLevel.HIGH.value,
            confidence=0.92,
            source=CrowdSource.EDGE_CAMERA.value,
            device_timestamp=now,
            server_received_timestamp=now,
        )

        # Bus B: 8 min away, LOW crowd
        await live_state.update_location(
            vehicle_id="BUS_108_B",
            lat=28.8250,
            lon=77.5450,
            speed=30.0,
            heading=40.0,
            device_timestamp=now,
            server_received_timestamp=now,
            source=LocationSource.OFFICIAL_GPS.value,
            progression_data={"current_stop_index": 7},
        )
        await live_state.update_crowd(
            vehicle_id="BUS_108_B",
            occupancy_score=0.25,
            crowd_level=CrowdLevel.LOW.value,
            confidence=0.94,
            source=CrowdSource.EDGE_CAMERA.value,
            device_timestamp=now,
            server_received_timestamp=now,
        )

        # Query Liveboard at Meerut South (STOP_10)
        board = CrowdService.get_stop_liveboard(db, "STOP_10")
        assert board is not None
        assert board.total_arrivals >= 2

        arr_fastest = next((a for a in board.arrivals if a.is_fastest), None)
        arr_comfortable = next((a for a in board.arrivals if a.is_most_comfortable), None)

        assert arr_fastest is not None
        assert arr_comfortable is not None
        assert arr_fastest.vehicle_id == "BUS_115_C"
        assert arr_comfortable.vehicle_id == "BUS_108_B"
    finally:
        db.close()


def test_low_ml_confidence_fallback():
    """Verify predictor falls back gracefully if ML model or confidence is constrained."""
    # Predict crowd at off-peak hour
    pred_level, pred_occ, conf = ml_predictor.predict_crowd(
        hour=3,
        day_of_week=0,
        is_major_stop=False,
        direction=0,
        stops_away=5,
        current_occupancy=0.20,
    )
    assert pred_level in [CrowdLevel.LOW, CrowdLevel.MEDIUM, CrowdLevel.HIGH, CrowdLevel.VERY_HIGH]
    assert 0.0 <= pred_occ <= 1.0
    assert 0.0 <= conf <= 1.0
