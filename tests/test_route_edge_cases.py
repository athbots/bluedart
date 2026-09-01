"""
Tests for Route Progression Edge Cases: Reverse Directions, Circular Loops, and Stop Types.
"""

import pytest
from services.api.app.core.database import SessionLocal
from services.api.app.services.progression_service import ProgressionService
from services.api.app.models.transit_models import Route, RouteDirection, Stop
from packages.schemas.transit import StopType
from scripts.seed_data import seed_database


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    seed_database()


def test_reverse_direction_route_progression():
    db = SessionLocal()
    try:
        # Route 201 has OUTBOUND (Anand Vihar -> Meerut South) and INBOUND (Meerut South -> Anand Vihar)
        inbound_dir = (
            db.query(RouteDirection)
            .filter(RouteDirection.route_id == "ROUTE_201", RouteDirection.direction == "INBOUND")
            .first()
        )
        assert inbound_dir is not None

        stops = ProgressionService.get_ordered_stops_for_direction(db, inbound_dir.id)
        assert len(stops) >= 5
        # Inbound origin should be Meerut South and destination Anand Vihar
        assert "Meerut South" in stops[0]["name"]
        assert "Anand Vihar" in stops[-1]["name"]
    finally:
        db.close()


def test_stop_type_support():
    db = SessionLocal()
    try:
        anand_vihar = db.query(Stop).filter(Stop.id == "STOP_01").first()
        assert anand_vihar.is_major_stop is True
    finally:
        db.close()
