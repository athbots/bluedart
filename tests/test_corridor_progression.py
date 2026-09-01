"""
Unit and Integration Tests for the Anand Vihar -> Modipuram 21-Stop Transit Corridor,
3D Transit Progression, Transit Truth Engine, and Stop-Centric Liveboards.

DATA INTEGRITY:
DEMO_CORRIDOR = True
DATA_CLASSIFICATION = "DEMONSTRATION"
"""

import pytest
import asyncio
from datetime import datetime, timezone
from services.api.app.core.database import init_db, SessionLocal
from scripts.seed_data import seed_database
from services.api.app.models.transit_models import Route, RouteDirection, RouteStop, Stop, Vehicle
from services.api.app.services.progression_service import ProgressionService
from services.api.app.services.crowd_service import CrowdService
from services.api.app.services.truth_engine import truth_engine
from services.simulator.fleet_simulator import fleet_simulator
from services.simulator.scenario_runner import ScenarioRunner
from packages.schemas.transit import StopType, RouteProgressionView
from packages.schemas.telemetry import CrowdLevel, LocationSource, CrowdSource
from services.api.app.core.live_state import live_state


@pytest.fixture(scope="module", autouse=True)
def setup_test_corridor():
    """Seed database once for all corridor tests."""
    seed_database()
    fleet_simulator.initialize_fleet(seed=42, speed=1.0)
    yield


def test_corridor_21_stops_seeded():
    """Verify all 21 Anand Vihar -> Modipuram stops exist in database."""
    db = SessionLocal()
    try:
        stops = db.query(Stop).all()
        assert len(stops) >= 21
        
        # Verify first and last stop IDs
        stop_01 = db.query(Stop).filter(Stop.id == "STOP_01").first()
        stop_21 = db.query(Stop).filter(Stop.id == "STOP_21").first()
        assert stop_01 is not None
        assert "Anand Vihar" in stop_01.name
        assert stop_21 is not None
        assert "Modipuram" in stop_21.name
    finally:
        db.close()


def test_forward_direction_sequence():
    """Verify OUTBOUND direction has 21 stops contiguous 0..20."""
    db = SessionLocal()
    try:
        direction = db.query(RouteDirection).filter(
            RouteDirection.route_id == "ROUTE_AV_MOD",
            RouteDirection.direction == "OUTBOUND"
        ).first()
        assert direction is not None

        ordered = ProgressionService.get_ordered_stops_for_direction(db, direction.id)
        assert len(ordered) == 21
        assert ordered[0]["stop_id"] == "STOP_01"
        assert ordered[20]["stop_id"] == "STOP_21"

        # Check contiguous sequences
        for idx, st in enumerate(ordered):
            assert st["sequence"] == idx
    finally:
        db.close()


def test_reverse_direction_sequence():
    """Verify INBOUND direction has 21 stops in reverse (Modipuram -> Anand Vihar)."""
    db = SessionLocal()
    try:
        direction = db.query(RouteDirection).filter(
            RouteDirection.route_id == "ROUTE_AV_MOD",
            RouteDirection.direction == "INBOUND"
        ).first()
        assert direction is not None

        ordered = ProgressionService.get_ordered_stops_for_direction(db, direction.id)
        assert len(ordered) == 21
        assert ordered[0]["stop_id"] == "STOP_21"
        assert ordered[20]["stop_id"] == "STOP_01"

        # Check sequences
        for idx, st in enumerate(ordered):
            assert st["sequence"] == idx
    finally:
        db.close()


def test_stop_classifications():
    """Verify stop types: TERMINAL, DEPOT, MAJOR, LOCAL."""
    db = SessionLocal()
    try:
        av = db.query(Stop).filter(Stop.id == "STOP_01").first()
        assert av.stop_type == StopType.TERMINAL
        assert av.is_terminal_stop is True

        duhai_depot = db.query(Stop).filter(Stop.id == "STOP_06").first()
        assert duhai_depot.stop_type == StopType.DEPOT
        assert duhai_depot.is_depot is True

        meerut_south = db.query(Stop).filter(Stop.id == "STOP_10").first()
        assert meerut_south.stop_type == StopType.MAJOR
        assert meerut_south.is_major_stop is True

        guldhar = db.query(Stop).filter(Stop.id == "STOP_04").first()
        assert guldhar.stop_type == StopType.LOCAL
    finally:
        db.close()


@pytest.mark.asyncio
async def test_3d_corridor_progression_view():
    """Verify 3D transit progression view calculation."""
    db = SessionLocal()
    try:
        # Simulate bus state near Modi Nagar North (Stop 9)
        mock_bus_state = {
            "vehicle_id": "BUS_115_C",
            "registration_number": "DL-01-EXP-5_C",
            "route_id": "ROUTE_AV_MOD",
            "direction": "OUTBOUND",
            "latitude": 28.9300,
            "longitude": 77.5850,
            "speed_kmh": 32.0,
            "current_stop_index": 8,
            "route_progress_percentage": 42.5,
            "crowd_level": "MEDIUM",
            "crowd_confidence": 0.88,
            "location_source": "OFFICIAL_GPS",
            "device_timestamp": datetime.now(timezone.utc).isoformat(),
        }

        prog = ProgressionService.get_route_progression_view(
            db=db,
            vehicle_id="BUS_115_C",
            live_bus=mock_bus_state,
            user_stop_id="STOP_10"  # Meerut South
        )

        assert prog is not None
        assert isinstance(prog, RouteProgressionView)
        assert prog.total_stops_count == 21
        assert prog.stops_passed_count == 8
        assert len(prog.stops) == 21
        assert prog.demo_corridor is True
        assert prog.data_classification == "DEMONSTRATION"
        assert prog.user_stop_name == "Meerut South"
        assert prog.eta_to_user_stop_seconds is not None
        assert prog.eta_to_user_stop_seconds > 0

        # Check node distance from bus calculation
        user_node = [n for n in prog.stops if n.stop_id == "STOP_10"][0]
        assert user_node.is_user_stop is True
        assert user_node.distance_from_bus_meters is not None
        assert user_node.distance_from_bus_meters > 0
    finally:
        db.close()


@pytest.mark.asyncio
async def test_liveboard_fastest_and_comfortable_resolution():
    """Verify liveboard resolves arrivals and tags FASTEST and MOST COMFORTABLE."""
    db = SessionLocal()
    try:
        # Run Scenario F
        await ScenarioRunner.run_scenario("F")

        # Update live state for the 3 demo buses
        now = datetime.now(timezone.utc)
        for b_id in ["BUS_115_C", "BUS_108_B", "BUS_102_A"]:
            bus = fleet_simulator.buses[b_id]
            bus.tick(delta_seconds=1.0)
            await live_state.set_route_context(
                vehicle_id=bus.vehicle_id,
                route_id=bus.route_id,
                route_number=bus.route_number,
                route_name=bus.route_name,
                direction=bus.direction_name,
            )
            await live_state.update_location(
                vehicle_id=bus.vehicle_id,
                lat=bus.lat,
                lon=bus.lon,
                speed=bus.current_speed_kmh,
                heading=bus.heading,
                device_timestamp=now,
                server_received_timestamp=now,
                source=LocationSource.OFFICIAL_GPS.value,
            )
            c_src = CrowdSource.EDGE_CAMERA.value if bus.is_camera_healthy else CrowdSource.PREDICTED.value
            await live_state.update_crowd(
                vehicle_id=bus.vehicle_id,
                occupancy_score=bus.occupancy_score,
                crowd_level=bus.crowd_level.value,
                confidence=0.92 if bus.is_camera_healthy else 0.81,
                source=c_src,
                device_timestamp=now,
                server_received_timestamp=now,
            )

        # Query liveboard for Meerut South (STOP_10)
        board = CrowdService.get_stop_liveboard(db, "STOP_10")
        assert board is not None
        assert board.total_arrivals >= 2

        # Check for FASTEST and MOST COMFORTABLE tags
        fastest = [a for a in board.arrivals if a.is_fastest]
        comfortable = [a for a in board.arrivals if a.is_most_comfortable]
        assert len(fastest) == 1
        assert len(comfortable) >= 1
    finally:
        db.close()
