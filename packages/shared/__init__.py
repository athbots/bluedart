"""
Shared Utilities Package
"""
from packages.shared.geo import (
    haversine_distance_meters,
    calculate_bearing,
    bearing_difference,
    project_point_to_segment,
    find_nearest_stop,
    match_position_to_route,
)
from packages.shared.crowd_config import CrowdConfig, TemporalCrowdSmoother
from packages.shared.provenance import (
    assess_freshness,
    resolve_crowd_provenance,
    STALE_LOCATION_THRESHOLD_SECONDS,
    STALE_CROWD_THRESHOLD_SECONDS,
)

__all__ = [
    "haversine_distance_meters",
    "calculate_bearing",
    "bearing_difference",
    "project_point_to_segment",
    "find_nearest_stop",
    "match_position_to_route",
    "CrowdConfig",
    "TemporalCrowdSmoother",
    "assess_freshness",
    "resolve_crowd_provenance",
    "STALE_LOCATION_THRESHOLD_SECONDS",
    "STALE_CROWD_THRESHOLD_SECONDS",
]
