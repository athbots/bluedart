"""
Tests for Route Matching and Progression Engine.
Verifies GPS noise tolerance, heading consistency, and stop sequence progression.
"""

import pytest
from packages.shared.geo import match_position_to_route


def test_match_position_along_ordered_stops():
    stops = [
        {"stop_id": "S1", "latitude": 28.6400, "longitude": 77.3000, "name": "Stop 1"},
        {"stop_id": "S2", "latitude": 28.6500, "longitude": 77.3100, "name": "Stop 2"},
        {"stop_id": "S3", "latitude": 28.6600, "longitude": 77.3200, "name": "Stop 3"},
        {"stop_id": "S4", "latitude": 28.6700, "longitude": 77.3300, "name": "Stop 4"},
    ]

    # Test position on segment S1 -> S2 with slight GPS jitter (15 meters off)
    jitter_lat = 28.6450 + 0.0001
    jitter_lon = 77.3050 - 0.0001

    res = match_position_to_route(
        lat=jitter_lat,
        lon=jitter_lon,
        heading=45.0,
        ordered_stops=stops,
        previous_stop_index=0,
    )

    assert res["is_on_route"] is True
    assert res["current_stop_index"] == 0  # between S1 and S2
    assert res["next_stop_index"] == 1     # heading toward S2
    assert 10.0 < res["progress_percentage"] < 30.0
    assert res["cross_track_error_meters"] < 50.0


def test_route_progression_advancement():
    stops = [
        {"stop_id": "S1", "latitude": 28.6400, "longitude": 77.3000, "name": "Stop 1"},
        {"stop_id": "S2", "latitude": 28.6500, "longitude": 77.3100, "name": "Stop 2"},
        {"stop_id": "S3", "latitude": 28.6600, "longitude": 77.3200, "name": "Stop 3"},
    ]

    # Test position past S2 heading toward S3
    res = match_position_to_route(
        lat=28.6550,
        lon=77.3150,
        heading=45.0,
        ordered_stops=stops,
        previous_stop_index=1,
    )

    assert res["current_stop_index"] == 1
    assert res["next_stop_index"] == 2
    assert res["progress_percentage"] > 50.0
