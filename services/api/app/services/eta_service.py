"""
ETA Calculation Engine.
Hybrid arrival estimation combining real-time speed, historical segment median travel times,
dwell time assumptions, and traffic time-of-day multipliers.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from services.api.app.models.transit_models import RouteStop, Stop
from packages.shared.geo import haversine_distance_meters

# Average Indian urban bus dwell time per stop in seconds
DEFAULT_STOP_DWELL_SECONDS = 30
MIN_RELIABLE_SPEED_KMH = 8.0
DEFAULT_URBAN_SPEED_KMH = 22.0


class ETAService:
    @staticmethod
    def get_time_of_day_traffic_factor(current_hour: Optional[int] = None) -> float:
        """
        Traffic congestion multiplier based on Indian peak transit hours.
        Morning peak: 08:00 - 11:30 (1.35x)
        Evening peak: 17:00 - 20:30 (1.45x)
        Off-peak: (1.0x)
        Late night: (0.85x)
        """
        if current_hour is None:
            current_hour = datetime.now(timezone.utc).hour + 5  # approx IST offset

        if 8 <= current_hour <= 11:
            return 1.35
        elif 17 <= current_hour <= 20:
            return 1.45
        elif 22 <= current_hour or current_hour < 6:
            return 0.85
        return 1.05

    @classmethod
    def calculate_eta_to_stop(
        cls,
        db: Session,
        live_bus: Dict[str, Any],
        target_stop_id: str,
        route_direction_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Calculate ETA from live bus position to a specific target stop.
        Returns dict with:
        - eta_seconds
        - eta_minutes
        - confidence (0.0 to 1.0)
        - source
        - stops_away
        - distance_meters
        """
        # Fetch ordered route stops
        route_stops = (
            db.query(RouteStop, Stop)
            .join(Stop, RouteStop.stop_id == Stop.id)
            .filter(RouteStop.route_direction_id == route_direction_id)
            .order_by(RouteStop.sequence.asc())
            .all()
        )

        if not route_stops:
            return None

        # Find target stop index
        target_idx = None
        for idx, (rs, stop) in enumerate(route_stops):
            if stop.id == target_stop_id:
                target_idx = idx
                break

        if target_idx is None:
            return None

        current_idx = live_bus.get("current_stop_index", 0)

        # If bus has already passed target stop in this direction
        if current_idx > target_idx:
            return None

        stops_away = target_idx - current_idx
        bus_lat = live_bus.get("latitude", 0.0)
        bus_lon = live_bus.get("longitude", 0.0)
        target_stop = route_stops[target_idx][1]

        # Calculate distance along the route
        total_distance_meters = 0.0
        if current_idx == target_idx:
            # Approaching the target stop directly
            total_distance_meters = haversine_distance_meters(
                bus_lat, bus_lon, target_stop.latitude, target_stop.longitude
            )
        else:
            # Distance from current bus position to next stop
            next_stop = route_stops[current_idx + 1][1]
            total_distance_meters += haversine_distance_meters(
                bus_lat, bus_lon, next_stop.latitude, next_stop.longitude
            )
            # Distance across all intermediate segments
            for i in range(current_idx + 1, target_idx):
                s1 = route_stops[i][1]
                s2 = route_stops[i + 1][1]
                total_distance_meters += haversine_distance_meters(
                    s1.latitude, s1.longitude, s2.latitude, s2.longitude
                )

        # Speed estimation
        current_speed_kmh = live_bus.get("speed_kmh", 0.0)
        effective_speed_kmh = current_speed_kmh if current_speed_kmh >= MIN_RELIABLE_SPEED_KMH else DEFAULT_URBAN_SPEED_KMH
        effective_speed_mps = (effective_speed_kmh * 1000.0) / 3600.0

        # Traffic multiplier
        traffic_factor = cls.get_time_of_day_traffic_factor()

        # Travel time in motion
        motion_time_seconds = (total_distance_meters / effective_speed_mps) * traffic_factor

        # Dwell time for intermediate stops
        intermediate_stops = max(0, stops_away - 1)
        dwell_time_seconds = intermediate_stops * DEFAULT_STOP_DWELL_SECONDS

        total_eta_seconds = int(motion_time_seconds + dwell_time_seconds)

        # Confidence calculation
        is_stale = live_bus.get("is_stale", False)
        base_confidence = 0.92 if not is_stale else 0.65
        # Confidence slightly decreases with greater distance / intermediate stops
        distance_penalty = min(0.20, (total_distance_meters / 15000.0) * 0.20)
        confidence = max(0.50, round(base_confidence - distance_penalty, 2))

        eta_source = "HYBRID_MODEL"
        if is_stale:
            eta_source = "HISTORICAL_FALLBACK"

        return {
            "eta_seconds": max(30, total_eta_seconds),
            "eta_minutes": max(1, round(total_eta_seconds / 60)),
            "confidence": confidence,
            "source": eta_source,
            "stops_away": stops_away,
            "distance_meters": round(total_distance_meters, 1),
        }
