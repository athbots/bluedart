"""
Tests for Geospatial Calculations and Nearest Stop Matching.
"""

import pytest
from packages.shared.geo import (
    haversine_distance_meters,
    calculate_bearing,
    project_point_to_segment,
    find_nearest_stop,
)


def test_haversine_distance():
    # Distance between Anand Vihar (28.6469, 77.3161) and Kaushambi (28.6433, 77.3235) is ~820m
    dist = haversine_distance_meters(28.6469, 77.3161, 28.6433, 77.3235)
    assert 750.0 < dist < 950.0


def test_calculate_bearing():
    # Point directly north
    bearing = calculate_bearing(28.60, 77.30, 28.70, 77.30)
    assert abs(bearing - 0.0) < 1.0 or abs(bearing - 360.0) < 1.0

    # Point directly east
    bearing_east = calculate_bearing(28.60, 77.30, 28.60, 77.40)
    assert abs(bearing_east - 90.0) < 1.0


def test_project_point_to_segment():
    # Segment from (0,0) to (0,2). Point at (1, 1). Projection should be at (0,1), fraction 0.5
    a_lat, a_lon = 28.6000, 77.3000
    b_lat, b_lon = 28.6000, 77.3200
    p_lat, p_lon = 28.6050, 77.3100  # slightly north of midpoint

    proj_lat, proj_lon, frac, dist = project_point_to_segment(
        p_lat, p_lon, a_lat, a_lon, b_lat, b_lon
    )
    assert 0.45 < frac < 0.55
    assert dist > 0.0
    assert abs(proj_lat - a_lat) < 0.001


def test_find_nearest_stop():
    stops = [
        {"id": "STOP_A", "latitude": 28.6469, "longitude": 77.3161},
        {"id": "STOP_B", "latitude": 28.7115, "longitude": 77.4425},
    ]
    # Query point near STOP_A
    match, dist = find_nearest_stop(28.6470, 77.3165, stops)
    assert match["id"] == "STOP_A"
    assert dist < 100.0
