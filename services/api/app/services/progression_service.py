"""
Route Progression Service for Smart Transit Intelligence System.
Derives current stop index, 3D transit progression timeline, next stop,
and remaining distance along the route supporting forward and reverse directions.

DATA INTEGRITY:
DEMO_CORRIDOR = True
DATA_CLASSIFICATION = "DEMONSTRATION"
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from services.api.app.models.transit_models import Route, RouteDirection, RouteStop, Stop
from packages.schemas.transit import RouteProgressionNode, RouteProgressionView, StopType
from packages.shared.geo import match_position_to_route, haversine_distance_meters
from packages.shared.provenance import build_data_provenance, GPS_LIVE_THRESHOLD, GPS_STALE_THRESHOLD
from packages.schemas.telemetry import LocationSource, TruthStatus, CrowdLevel


class ProgressionService:
    @staticmethod
    def get_ordered_stops_for_direction(
        db: Session, route_direction_id: str
    ) -> List[Dict[str, Any]]:
        """Fetch ordered stops for a route direction with full classifications."""
        route_stops = (
            db.query(RouteStop, Stop)
            .join(Stop, RouteStop.stop_id == Stop.id)
            .filter(RouteStop.route_direction_id == route_direction_id)
            .order_by(RouteStop.sequence.asc())
            .all()
        )

        ordered = []
        for rs, stop in route_stops:
            ordered.append({
                "route_stop_id": rs.id,
                "stop_id": stop.id,
                "name": stop.name,
                "display_name": stop.display_name or stop.name,
                "sequence": rs.sequence,
                "latitude": stop.latitude,
                "longitude": stop.longitude,
                "scheduled_offset_seconds": rs.scheduled_offset_seconds,
                "cumulative_distance_meters": rs.cumulative_distance_meters,
                "stop_type": stop.stop_type if hasattr(stop, "stop_type") else StopType.LOCAL,
                "is_major_stop": stop.is_major_stop,
                "is_intercity_stop": stop.is_intercity_stop,
                "is_interchange_stop": getattr(stop, "is_interchange_stop", False),
                "is_terminal_stop": getattr(stop, "is_terminal_stop", False),
                "is_depot": getattr(stop, "is_depot", False),
            })
        return ordered

    @staticmethod
    def compute_progression(
        db: Session,
        lat: float,
        lon: float,
        heading: float,
        route_direction_id: str,
        previous_stop_index: int = 0,
    ) -> Dict[str, Any]:
        """
        Map-matches the vehicle's coordinate to the route direction and extracts progression data.
        """
        ordered_stops = ProgressionService.get_ordered_stops_for_direction(db, route_direction_id)
        if not ordered_stops:
            return {
                "current_stop_index": 0,
                "current_stop_id": None,
                "current_stop_name": None,
                "next_stop_id": None,
                "next_stop_name": None,
                "route_progress_percentage": 0.0,
                "distance_remaining_meters": 0.0,
            }

        match = match_position_to_route(
            lat=lat,
            lon=lon,
            heading=heading,
            ordered_stops=ordered_stops,
            previous_stop_index=previous_stop_index,
        )

        curr_idx = match["current_stop_index"]
        next_idx = match["next_stop_index"]

        curr_stop = ordered_stops[curr_idx]
        next_stop = ordered_stops[next_idx] if next_idx < len(ordered_stops) else curr_stop

        # Calculate remaining distance from current position to end of route
        dist_to_next = match["distance_to_next_stop_meters"]
        remaining_meters = dist_to_next
        for i in range(next_idx, len(ordered_stops) - 1):
            s1 = ordered_stops[i]
            s2 = ordered_stops[i + 1]
            remaining_meters += haversine_distance_meters(
                s1["latitude"], s1["longitude"], s2["latitude"], s2["longitude"]
            )

        return {
            "current_stop_index": curr_idx,
            "current_stop_id": curr_stop["stop_id"],
            "current_stop_name": curr_stop["name"],
            "next_stop_id": next_stop["stop_id"],
            "next_stop_name": next_stop["name"],
            "route_progress_percentage": match["progress_percentage"],
            "distance_remaining_meters": round(remaining_meters, 1),
            "cross_track_error_meters": match["cross_track_error_meters"],
            "is_on_route": match["is_on_route"],
        }

    @staticmethod
    def get_route_progression_view(
        db: Session,
        vehicle_id: str,
        live_bus: Dict[str, Any],
        user_stop_id: Optional[str] = None,
    ) -> Optional[RouteProgressionView]:
        """
        Build 3D transit progression timeline view with truth provenance and relative distances.
        """
        route_id = live_bus.get("route_id")
        direction_name = live_bus.get("direction", "OUTBOUND")

        if not route_id:
            return None

        route = db.query(Route).filter(Route.id == route_id).first()
        if not route:
            return None

        direction = (
            db.query(RouteDirection)
            .filter(RouteDirection.route_id == route_id, RouteDirection.direction == direction_name)
            .first()
        )
        if not direction:
            direction = db.query(RouteDirection).filter(RouteDirection.route_id == route_id).first()

        if not direction:
            return None

        ordered_stops = ProgressionService.get_ordered_stops_for_direction(db, direction.id)
        current_idx = live_bus.get("current_stop_index", 0)
        bus_lat = live_bus.get("latitude", 0.0)
        bus_lon = live_bus.get("longitude", 0.0)

        nodes: List[RouteProgressionNode] = []
        user_eta_seconds = None
        user_stop_name = None
        next_major_stop_name = None

        # Find next major stop ahead
        for idx in range(current_idx + 1, len(ordered_stops)):
            if ordered_stops[idx].get("is_major_stop") or ordered_stops[idx].get("is_interchange_stop") or ordered_stops[idx].get("is_terminal_stop"):
                next_major_stop_name = ordered_stops[idx]["name"]
                break

        for idx, stop in enumerate(ordered_stops):
            is_passed = idx < current_idx
            is_current = idx == current_idx
            is_next = idx == (current_idx + 1)
            is_user = (user_stop_id is not None) and (stop["stop_id"] == user_stop_id)
            is_terminal = (idx == 0 or idx == len(ordered_stops) - 1)

            if is_user:
                user_stop_name = stop["name"]

            # Calculate distance from bus to this stop
            dist_from_bus = None
            if bus_lat and bus_lon:
                dist_from_bus = round(haversine_distance_meters(bus_lat, bus_lon, stop["latitude"], stop["longitude"]), 1)

            # Relative ETA estimate per node
            eta_secs = None
            if not is_passed:
                stops_away = max(0, idx - current_idx)
                speed_mps = max(5.0, live_bus.get("speed_kmh", 25.0) / 3.6)
                travel_dist = abs(stop["cumulative_distance_meters"] - ordered_stops[current_idx]["cumulative_distance_meters"])
                eta_secs = int(stops_away * 60 + (travel_dist / speed_mps))
                if is_user:
                    user_eta_seconds = eta_secs

            nodes.append(
                RouteProgressionNode(
                    stop_id=stop["stop_id"],
                    stop_name=stop["name"],
                    display_name=stop.get("display_name", stop["name"]),
                    sequence=stop["sequence"],
                    latitude=stop["latitude"],
                    longitude=stop["longitude"],
                    cumulative_distance_meters=stop["cumulative_distance_meters"],
                    stop_type=stop.get("stop_type", StopType.LOCAL),
                    is_major_stop=stop["is_major_stop"],
                    is_interchange_stop=stop.get("is_interchange_stop", False),
                    is_terminal_stop=is_terminal or stop.get("is_terminal_stop", False),
                    is_depot=stop.get("is_depot", False),
                    is_passed=is_passed,
                    is_current=is_current,
                    is_next=is_next,
                    is_user_stop=is_user,
                    distance_from_bus_meters=dist_from_bus,
                    estimated_arrival_seconds=eta_secs,
                    predicted_crowd_level=live_bus.get("crowd_level", CrowdLevel.MEDIUM),
                    crowd_confidence=live_bus.get("crowd_confidence", 0.88),
                )
            )

        prov = build_data_provenance(
            source=live_bus.get("location_source", LocationSource.OFFICIAL_GPS.value),
            observed_at=datetime.fromisoformat(live_bus.get("device_timestamp", live_bus.get("location_updated_at", "2026-09-01T00:00:00+00:00")).replace("Z", "+00:00")),
            confidence=0.92,
            live_threshold_seconds=GPS_LIVE_THRESHOLD,
            stale_threshold_seconds=GPS_STALE_THRESHOLD,
        )

        curr_stop_name = ordered_stops[current_idx]["name"] if current_idx < len(ordered_stops) else direction.origin

        return RouteProgressionView(
            vehicle_id=vehicle_id,
            registration_number=live_bus.get("registration_number", vehicle_id),
            route_id=route.id,
            route_number=route.route_number,
            route_name=route.name,
            direction=direction.direction,
            origin=direction.origin,
            destination=direction.destination,
            current_speed_kmh=live_bus.get("speed_kmh", 0.0),
            route_progress_percentage=live_bus.get("route_progress_percentage", 0.0),
            stops_passed_count=current_idx,
            total_stops_count=len(ordered_stops),
            current_stop_name=curr_stop_name,
            next_major_stop_name=next_major_stop_name or ordered_stops[-1]["name"],
            current_bus_latitude=bus_lat,
            current_bus_longitude=bus_lon,
            stops=nodes,
            user_stop_id=user_stop_id,
            user_stop_name=user_stop_name,
            eta_to_user_stop_seconds=user_eta_seconds,
            crowd_at_user_stop=live_bus.get("crowd_level", CrowdLevel.MEDIUM),
            provenance=prov,
            demo_corridor=True,
            data_classification="DEMONSTRATION",
        )
