"""
Geospatial Calculations and Route Matching Engine.
Production-grade spatial operations for bus tracking, nearest stop detection, and route projection.
"""

import math
from typing import List, Tuple, Optional, Dict, Any

EARTH_RADIUS_METERS = 6371000.0


def haversine_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the Earth in meters.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return EARTH_RADIUS_METERS * c


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate initial compass bearing from point 1 to point 2 in degrees (0..360).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    bearing = math.degrees(math.atan2(y, x))
    return (bearing + 360.0) % 360.0


def bearing_difference(b1: float, b2: float) -> float:
    """
    Compute minimal angular difference between two bearings in degrees (0..180).
    """
    diff = abs(b1 - b2) % 360.0
    return 360.0 - diff if diff > 180.0 else diff


def project_point_to_segment(
    p_lat: float, p_lon: float, a_lat: float, a_lon: float, b_lat: float, b_lon: float
) -> Tuple[float, float, float, float]:
    """
    Project point P onto segment AB.
    Returns:
        (proj_lat, proj_lon, fraction_along_segment, distance_to_segment_meters)
    """
    # Use equirectangular approximation for high performance on local street segments
    lat_mid = math.radians((a_lat + b_lat) / 2.0)
    cos_lat = math.cos(lat_mid)

    # Convert coordinates to planar meters relative to point A
    ax, ay = 0.0, 0.0
    bx = math.radians(b_lon - a_lon) * EARTH_RADIUS_METERS * cos_lat
    by = math.radians(b_lat - a_lat) * EARTH_RADIUS_METERS
    px = math.radians(p_lon - a_lon) * EARTH_RADIUS_METERS * cos_lat
    py = math.radians(p_lat - a_lat) * EARTH_RADIUS_METERS

    ab_dx = bx - ax
    ab_dy = by - ay
    ab_len_sq = ab_dx * ab_dx + ab_dy * ab_dy

    if ab_len_sq < 1e-6:
        # Segment A and B are identical
        dist = math.sqrt(px * px + py * py)
        return a_lat, a_lon, 0.0, dist

    # Projection scalar t clamped to [0, 1]
    t = max(0.0, min(1.0, (px * ab_dx + py * ab_dy) / ab_len_sq))

    proj_x = ax + t * ab_dx
    proj_y = ay + t * ab_dy

    dist = math.sqrt((px - proj_x) ** 2 + (py - proj_y) ** 2)

    # Convert back to lat/lon
    proj_lat = a_lat + math.degrees(proj_y / EARTH_RADIUS_METERS)
    proj_lon = a_lon + math.degrees(proj_x / (EARTH_RADIUS_METERS * cos_lat))

    return proj_lat, proj_lon, t, dist


def find_nearest_stop(
    lat: float, lon: float, stops: List[Dict[str, Any]], max_distance_meters: float = 10000.0
) -> Optional[Tuple[Dict[str, Any], float]]:
    """
    Find the closest stop from a list of stop dicts/objects.
    Returns (stop, distance_meters) or None.
    """
    if not stops:
        return None

    best_stop = None
    min_dist = float("inf")

    for stop in stops:
        s_lat = getattr(stop, "latitude", None) if not isinstance(stop, dict) else stop.get("latitude")
        s_lon = getattr(stop, "longitude", None) if not isinstance(stop, dict) else stop.get("longitude")

        if s_lat is None or s_lon is None:
            continue

        dist = haversine_distance_meters(lat, lon, float(s_lat), float(s_lon))
        if dist < min_dist and dist <= max_distance_meters:
            min_dist = dist
            best_stop = stop

    if best_stop is None:
        return None

    return best_stop, min_dist


def match_position_to_route(
    lat: float,
    lon: float,
    heading: float,
    ordered_stops: List[Dict[str, Any]],
    previous_stop_index: int = 0,
    max_snap_distance_meters: float = 500.0,
) -> Dict[str, Any]:
    """
    Robust route matching engine.
    Determines current segment index, progress along segment, current stop,
    next stop, and upcoming stops while tolerating GPS jitter and heading variation.
    """
    if not ordered_stops or len(ordered_stops) < 2:
        return {
            "matched_lat": lat,
            "matched_lon": lon,
            "current_stop_index": 0,
            "next_stop_index": 0,
            "progress_percentage": 0.0,
            "distance_to_next_stop_meters": 0.0,
            "cross_track_error_meters": 0.0,
            "is_on_route": False,
        }

    n_stops = len(ordered_stops)
    best_segment_idx = max(0, min(previous_stop_index, n_stops - 2))
    min_score = float("inf")
    best_proj_lat, best_proj_lon = lat, lon
    best_fraction = 0.0
    best_dist = float("inf")

    # Search window: prioritize segments near previous_stop_index but allow forward scanning
    search_start = max(0, previous_stop_index - 1)
    search_end = min(n_stops - 1, previous_stop_index + 4)

    # If window is small, check all segments to handle initial detection
    if previous_stop_index == 0:
        search_start = 0
        search_end = n_stops - 1

    for i in range(search_start, search_end):
        stop_a = ordered_stops[i]
        stop_b = ordered_stops[i + 1]

        a_lat = getattr(stop_a, "latitude", None) or (stop_a.get("latitude") if isinstance(stop_a, dict) else 0.0)
        a_lon = getattr(stop_a, "longitude", None) or (stop_a.get("longitude") if isinstance(stop_a, dict) else 0.0)
        b_lat = getattr(stop_b, "latitude", None) or (stop_b.get("latitude") if isinstance(stop_b, dict) else 0.0)
        b_lon = getattr(stop_b, "longitude", None) or (stop_b.get("longitude") if isinstance(stop_b, dict) else 0.0)

        proj_lat, proj_lon, t, dist = project_point_to_segment(lat, lon, a_lat, a_lon, b_lat, b_lon)

        # Segment bearing check
        seg_bearing = calculate_bearing(a_lat, a_lon, b_lat, b_lon)
        bearing_diff = bearing_difference(heading, seg_bearing) if heading > 0 else 0.0

        # Score balances distance penalty and heading alignment penalty
        heading_penalty = (bearing_diff / 180.0) * 150.0 if heading > 0 else 0.0
        sequence_penalty = abs(i - previous_stop_index) * 20.0  # gentle bias toward forward progression
        score = dist + heading_penalty + sequence_penalty

        if score < min_score:
            min_score = score
            best_segment_idx = i
            best_proj_lat = proj_lat
            best_proj_lon = proj_lon
            best_fraction = t
            best_dist = dist

    # Calculate cumulative distance to next stop
    next_stop_idx = min(best_segment_idx + 1, n_stops - 1)
    next_stop = ordered_stops[next_stop_idx]
    next_lat = getattr(next_stop, "latitude", None) or (next_stop.get("latitude") if isinstance(next_stop, dict) else 0.0)
    next_lon = getattr(next_stop, "longitude", None) or (next_stop.get("longitude") if isinstance(next_stop, dict) else 0.0)

    dist_to_next_stop = haversine_distance_meters(best_proj_lat, best_proj_lon, next_lat, next_lon)

    # Compute overall route progress percentage
    total_segments = n_stops - 1
    progress_percentage = min(100.0, max(0.0, ((best_segment_idx + best_fraction) / total_segments) * 100.0))

    is_on_route = best_dist <= max_snap_distance_meters

    return {
        "matched_lat": best_proj_lat,
        "matched_lon": best_proj_lon,
        "current_stop_index": best_segment_idx,
        "next_stop_index": next_stop_idx,
        "segment_fraction": best_fraction,
        "progress_percentage": round(progress_percentage, 1),
        "distance_to_next_stop_meters": round(dist_to_next_stop, 1),
        "cross_track_error_meters": round(best_dist, 1),
        "is_on_route": is_on_route,
    }
