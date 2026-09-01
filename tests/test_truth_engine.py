"""
Comprehensive Tests for Transit Truth Engine.
Verifies location, crowd, and ETA resolution, source priority hierarchy,
freshness & staleness evaluation, out-of-order rejection, duplicate idempotency,
and ground-truth prediction-vs-actual tracking.
"""

import pytest
from datetime import datetime, timezone, timedelta
from services.api.app.core.database import SessionLocal, init_db
from services.api.app.core.live_state import live_state
from services.api.app.services.truth_engine import truth_engine
from services.api.app.models.transit_models import (
    Vehicle,
    Route,
    RouteDirection,
    RouteStop,
    Stop,
    ETAPrediction,
    CrowdPrediction,
)
from packages.schemas.telemetry import (
    LocationSource,
    CrowdSource,
    ETASource,
    TruthStatus,
    CrowdLevel,
)
from scripts.seed_data import seed_database


@pytest.fixture(scope="module", autouse=True)
def setup_transit_data():
    seed_database()


@pytest.mark.asyncio
async def test_truth_location_resolution_fresh_vs_stale():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # 1. Update fresh location (age = 0s)
        await live_state.update_location(
            vehicle_id="BUS_201_A",
            lat=28.6469,
            lon=77.3161,
            speed=30.0,
            heading=90.0,
            device_timestamp=now,
            server_received_timestamp=now,
            source=LocationSource.OFFICIAL_GPS.value,
        )

        res_fresh = truth_engine.resolve_location(db, "BUS_201_A", current_time=now)
        assert res_fresh["provenance"].status == TruthStatus.LIVE
        assert res_fresh["provenance"].is_live is True
        assert res_fresh["provenance"].source == LocationSource.OFFICIAL_GPS.value

        # 2. Evaluate at future time (+120 seconds) where observation becomes stale
        future_time = now + timedelta(seconds=120)
        res_stale = truth_engine.resolve_location(db, "BUS_201_A", current_time=future_time)
        assert res_stale["provenance"].status in (TruthStatus.STALE, TruthStatus.OBSERVED)
        assert res_stale["provenance"].is_live is False
    finally:
        db.close()


@pytest.mark.asyncio
async def test_truth_crowd_priority_and_fallback():
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)

        # 1. Fresh Edge Camera Observation (< 60s)
        await live_state.update_crowd(
            vehicle_id="BUS_201_A",
            occupancy_score=0.82,
            crowd_level=CrowdLevel.HIGH.value,
            confidence=0.94,
            source=CrowdSource.EDGE_CAMERA.value,
            device_timestamp=now,
            server_received_timestamp=now,
        )

        crowd_fresh = truth_engine.resolve_crowd(db, "BUS_201_A", current_time=now)
        assert crowd_fresh["crowd_level"] == CrowdLevel.HIGH
        assert crowd_fresh["provenance"].source == CrowdSource.EDGE_CAMERA.value
        assert crowd_fresh["provenance"].status == TruthStatus.LIVE

        # 2. When Camera data becomes stale (+200 seconds), fall back to ML prediction
        future_time = now + timedelta(seconds=200)
        crowd_fallback = truth_engine.resolve_crowd(db, "BUS_201_A", current_time=future_time)
        assert crowd_fallback["provenance"].source == CrowdSource.PREDICTED.value
        assert crowd_fallback["provenance"].status == TruthStatus.PREDICTED
        assert crowd_fallback["provenance"].is_live is False
    finally:
        db.close()


@pytest.mark.asyncio
async def test_out_of_order_telemetry_rejection():
    """
    Verify that an older delayed packet does NOT overwrite newer live state.
    """
    now = datetime.now(timezone.utc)
    t_new = now
    t_old = now - timedelta(minutes=5)

    # 1. Set current state at t_new
    await live_state.update_location(
        vehicle_id="BUS_102_A",
        lat=28.6700,
        lon=77.4200,
        speed=40.0,
        device_timestamp=t_new,
        server_received_timestamp=now,
    )

    # 2. Ingest late out-of-order packet with device timestamp t_old
    res_rejected = await live_state.update_location(
        vehicle_id="BUS_102_A",
        lat=28.6000,
        lon=77.3000,
        speed=10.0,
        device_timestamp=t_old,
        server_received_timestamp=now,
    )

    # Verify the live state maintained the newer coordinate (28.6700, 77.4200)
    current_state = live_state.get_vehicle_state("BUS_102_A")
    assert current_state["latitude"] == 28.6700
    assert current_state["longitude"] == 77.4200
    assert current_state["speed_kmh"] == 40.0


@pytest.mark.asyncio
async def test_duplicate_telemetry_idempotency():
    """
    Verify duplicate message_id is filtered idempotently.
    """
    msg_id = "TEST-UUID-DUPLICATE-999"
    assert live_state.is_message_processed(msg_id) is False

    live_state.mark_message_processed(msg_id)
    assert live_state.is_message_processed(msg_id) is True


def test_prediction_vs_actual_ground_truth_tracking():
    """
    Verify recording actual ground truth arrivals and crowd calculates error without corrupting original prediction.
    """
    import uuid
    db = SessionLocal()
    try:
        unique_trip = f"TRIP_TEST_{uuid.uuid4().hex[:8]}"
        pred_time = datetime.now(timezone.utc)
        target_arrival = pred_time + timedelta(minutes=10)

        # 1. Insert an ETA prediction
        eta_pred = ETAPrediction(
            id=f"PRED_ETA_{uuid.uuid4().hex[:8]}",
            trip_id=unique_trip,
            vehicle_id="BUS_201_A",
            target_stop_id="STOP_07",
            prediction_time=pred_time,
            predicted_arrival_time=target_arrival,
            confidence=0.88,
            model_version="v1.2.0",
        )
        db.add(eta_pred)

        # 2. Insert a Crowd prediction
        crowd_pred = CrowdPrediction(
            id=f"PRED_CROWD_{uuid.uuid4().hex[:8]}",
            trip_id=unique_trip,
            vehicle_id="BUS_201_A",
            route_direction_id="DIR_201_OUT",
            target_stop_id="STOP_07",
            prediction_time=pred_time,
            predicted_crowd_level=CrowdLevel.HIGH,
            predicted_occupancy_score=0.75,
            confidence=0.85,
            model_version="v1.2.0",
        )
        db.add(crowd_pred)
        db.commit()

        # 3. Bus actually arrives 2 minutes later than predicted (+12 minutes total)
        actual_arr = pred_time + timedelta(minutes=12)
        err_sec = truth_engine.record_actual_arrival(
            db=db,
            vehicle_id="BUS_201_A",
            trip_id=unique_trip,
            stop_id="STOP_07",
            actual_arrival_time=actual_arr,
        )

        assert err_sec == 120  # 2 minutes error

        # 4. Bus actually arrives with occupancy 0.80
        err_crowd = truth_engine.record_actual_crowd(
            db=db,
            vehicle_id="BUS_201_A",
            trip_id=unique_trip,
            stop_id="STOP_07",
            actual_occupancy=0.80,
            actual_crowd_level=CrowdLevel.HIGH,
        )

        assert err_crowd == 0.05

        # Verify DB records updated with ground truth
        updated_eta = db.query(ETAPrediction).filter(ETAPrediction.trip_id == unique_trip).first()
        assert updated_eta.error_seconds == 120
        res_time = updated_eta.predicted_arrival_time
        if res_time.tzinfo is None:
            res_time = res_time.replace(tzinfo=timezone.utc)
        assert res_time == target_arrival  # preserved original

        updated_crowd = db.query(CrowdPrediction).filter(CrowdPrediction.trip_id == unique_trip).first()
        assert updated_crowd.prediction_error == 0.05
        assert updated_crowd.predicted_occupancy_score == 0.75  # preserved original

    finally:
        db.close()
