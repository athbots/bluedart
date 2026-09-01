"""
Geolocation Service.
Handles nearest stop discovery, spatial distance filtering, and stop search.
"""

from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from services.api.app.models.transit_models import Stop
from packages.schemas.transit import StopWithDistance, StopBase
from packages.shared.geo import haversine_distance_meters


class GeoService:
    @staticmethod
    def get_nearby_stops(
        db: Session,
        lat: float,
        lon: float,
        radius_meters: float = 5000.0,
        limit: int = 10,
    ) -> List[StopWithDistance]:
        """
        Find bus stops within radius_meters from (lat, lon), sorted by distance.
        """
        all_stops = db.query(Stop).all()
        stops_with_dist: List[Tuple[Stop, float]] = []

        for stop in all_stops:
            dist = haversine_distance_meters(lat, lon, stop.latitude, stop.longitude)
            if dist <= radius_meters:
                stops_with_dist.append((stop, dist))

        # Sort ascending by distance
        stops_with_dist.sort(key=lambda x: x[1])

        results: List[StopWithDistance] = []
        for stop, dist in stops_with_dist[:limit]:
            results.append(
                StopWithDistance(
                    id=stop.id,
                    name=stop.name,
                    city=stop.city,
                    state=stop.state,
                    latitude=stop.latitude,
                    longitude=stop.longitude,
                    is_major_stop=stop.is_major_stop,
                    is_intercity_stop=stop.is_intercity_stop,
                    address=stop.address,
                    distance_meters=round(dist, 1),
                )
            )

        # If no stops within radius, return closest available stop so app never crashes
        if not results and all_stops:
            all_with_dist = [
                (stop, haversine_distance_meters(lat, lon, stop.latitude, stop.longitude))
                for stop in all_stops
            ]
            all_with_dist.sort(key=lambda x: x[1])
            closest_stop, dist = all_with_dist[0]
            results.append(
                StopWithDistance(
                    id=closest_stop.id,
                    name=closest_stop.name,
                    city=closest_stop.city,
                    state=closest_stop.state,
                    latitude=closest_stop.latitude,
                    longitude=closest_stop.longitude,
                    is_major_stop=closest_stop.is_major_stop,
                    is_intercity_stop=closest_stop.is_intercity_stop,
                    address=closest_stop.address,
                    distance_meters=round(dist, 1),
                )
            )

        return results

    @staticmethod
    def get_stop_by_id(db: Session, stop_id: str) -> Optional[StopBase]:
        stop = db.query(Stop).filter(Stop.id == stop_id).first()
        if not stop:
            return None
        return StopBase(
            id=stop.id,
            name=stop.name,
            city=stop.city,
            state=stop.state,
            latitude=stop.latitude,
            longitude=stop.longitude,
            is_major_stop=stop.is_major_stop,
            is_intercity_stop=stop.is_intercity_stop,
            address=stop.address,
        )
