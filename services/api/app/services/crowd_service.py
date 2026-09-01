"""
Crowd Evaluation and Arrival Liveboard Engine.
Builds the stop-centric liveboard using the Transit Truth Engine, formats live vs predicted data,
evaluates crowd transitions, and annotates commuter decision tags (Fastest vs Most Comfortable).
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from services.api.app.models.transit_models import Route, RouteDirection, RouteStop, Stop, Vehicle
from services.api.app.core.live_state import live_state
from services.api.app.services.eta_service import ETAService
from services.api.app.services.truth_engine import truth_engine
from packages.schemas.transit import StopArrival, StopArrivalBoard, StopBase, StopType, VehicleType
from packages.schemas.telemetry import CrowdLevel, CrowdSource, TruthStatus
from packages.shared.crowd_config import CrowdConfig, TemporalCrowdSmoother
from packages.shared.provenance import resolve_crowd_provenance


class CrowdService:
    def __init__(self):
        self.crowd_config = CrowdConfig()
        self.smoothers: Dict[str, TemporalCrowdSmoother] = {}

    def get_smoother(self, vehicle_id: str) -> TemporalCrowdSmoother:
        if vehicle_id not in self.smoothers:
            self.smoothers[vehicle_id] = TemporalCrowdSmoother(config=self.crowd_config)
        return self.smoothers[vehicle_id]

    def process_raw_occupancy(
        self, vehicle_id: str, raw_occupancy: float
    ) -> Tuple[float, CrowdLevel]:
        """Pass raw occupancy through temporal filter with hysteresis."""
        smoother = self.get_smoother(vehicle_id)
        return smoother.add_observation(raw_occupancy)

    @classmethod
    def predict_crowd_at_stop(
        cls,
        current_crowd_level: CrowdLevel,
        current_occupancy: float,
        stops_away: int,
        is_major_stop: bool = False,
    ) -> Tuple[CrowdLevel, float, float]:
        """
        Prior crowd prediction when advancing along stops.
        Returns: (predicted_level, predicted_occupancy, confidence)
        """
        delta = (0.05 * stops_away)
        if is_major_stop:
            delta += 0.18

        pred_occupancy = max(0.05, min(0.98, current_occupancy + delta))
        config = CrowdConfig()
        pred_level = config.classify_raw(pred_occupancy)
        confidence = max(0.65, round(0.90 - (stops_away * 0.03), 2))

        return pred_level, round(pred_occupancy, 2), confidence

    @classmethod
    def get_stop_liveboard(cls, db: Session, stop_id: str) -> Optional[StopArrivalBoard]:
        """
        Build the stop-centric liveboard of all buses currently approaching the selected stop using Truth Engine.
        """
        target_stop = db.query(Stop).filter(Stop.id == stop_id).first()
        if not target_stop:
            return None

        # Find all routes passing through this stop
        route_stops = (
            db.query(RouteStop, RouteDirection, Route)
            .join(RouteDirection, RouteStop.route_direction_id == RouteDirection.id)
            .join(Route, RouteDirection.route_id == Route.id)
            .filter(RouteStop.stop_id == stop_id)
            .all()
        )

        active_vehicles = live_state.get_all_active_vehicles()
        arrivals: List[StopArrival] = []

        for rs, r_dir, route in route_stops:
            for v_state in active_vehicles:
                if v_state.get("route_id") == route.id and v_state.get("direction") == r_dir.direction:
                    v_id = v_state["vehicle_id"]

                    # 1. Resolve authoritative location and progress via Truth Engine
                    loc_truth = truth_engine.resolve_location(db, v_id)

                    # 2. Resolve authoritative arrival ETA via Truth Engine
                    eta_truth = truth_engine.resolve_eta(
                        db=db,
                        vehicle_id=v_id,
                        target_stop_id=stop_id,
                        route_direction_id=r_dir.id,
                    )

                    if not eta_truth:
                        # Bus has already passed or is not on route segment
                        continue

                    # 3. Resolve authoritative crowd density via Truth Engine
                    crowd_truth = truth_engine.resolve_crowd(db, v_id)

                    curr_crowd_level = crowd_truth["crowd_level"]
                    curr_occupancy = crowd_truth["occupancy_score"]
                    crowd_prov = crowd_truth["provenance"]

                    # 4. Predict crowd level at target commuter stop
                    pred_level, pred_occupancy, pred_conf = cls.predict_crowd_at_stop(
                        current_crowd_level=curr_crowd_level,
                        current_occupancy=curr_occupancy,
                        stops_away=eta_truth["stops_away"],
                        is_major_stop=target_stop.is_major_stop,
                    )

                    arrival = StopArrival(
                        vehicle_id=v_id,
                        trip_id=v_state.get("trip_id") or f"TRIP-{v_id}",
                        registration_number=v_state.get("registration_number", v_id),
                        fleet_number=v_state.get("fleet_number", "EV-100"),
                        vehicle_type=VehicleType.E_BUS,
                        route_id=route.id,
                        route_number=route.route_number,
                        route_name=route.name,
                        direction=r_dir.direction,
                        destination=r_dir.destination,
                        current_latitude=loc_truth["latitude"],
                        current_longitude=loc_truth["longitude"],
                        current_stop_name=loc_truth.get("current_stop_name") or "On Route",
                        stops_away=eta_truth["stops_away"],
                        distance_to_stop_meters=eta_truth["distance_meters"],
                        eta_seconds=eta_truth["eta_seconds"],
                        eta_minutes=eta_truth["eta_minutes"],
                        eta_confidence=eta_truth["provenance"].confidence,
                        eta_source=eta_truth["provenance"].source,
                        eta_status=eta_truth["provenance"].status,
                        is_fastest=False,
                        is_most_comfortable=False,
                        current_crowd_level=curr_crowd_level,
                        current_occupancy_score=curr_occupancy,
                        crowd_source=CrowdSource(crowd_prov.source) if crowd_prov.source in CrowdSource.__members__ else CrowdSource.SIMULATED,
                        crowd_status=crowd_prov.status,
                        crowd_is_live=crowd_prov.is_live,
                        predicted_crowd_at_stop=pred_level,
                        predicted_occupancy_at_stop=pred_occupancy,
                        prediction_confidence=pred_conf,
                        provenance=crowd_prov,
                        is_stale=crowd_prov.is_stale,
                        last_updated_seconds_ago=crowd_prov.freshness_seconds,
                    )
                    arrivals.append(arrival)

        # Sort primarily by ETA
        arrivals.sort(key=lambda x: x.eta_seconds)

        # Apply Commuter Decision Rules (Fastest vs Most Comfortable)
        if arrivals:
            arrivals[0].is_fastest = True
            if arrivals[0].current_crowd_level == CrowdLevel.LOW:
                arrivals[0].is_most_comfortable = True
            else:
                comfortable_candidates = [
                    a for a in arrivals if a.current_crowd_level in (CrowdLevel.LOW, CrowdLevel.MEDIUM)
                ]
                if comfortable_candidates:
                    comfortable_candidates.sort(key=lambda x: (x.current_occupancy_score, x.eta_seconds))
                    comfortable_candidates[0].is_most_comfortable = True

        stop_type = getattr(target_stop, "stop_type", None)
        if not stop_type or isinstance(stop_type, str):
            stop_type_val = StopType.MAJOR if target_stop.is_major_stop else (StopType.INTERCITY if target_stop.is_intercity_stop else StopType.LOCAL)
        else:
            stop_type_val = stop_type

        stop_base = StopBase(
            id=target_stop.id,
            name=target_stop.name,
            city=target_stop.city,
            state=target_stop.state,
            latitude=target_stop.latitude,
            longitude=target_stop.longitude,
            is_major_stop=target_stop.is_major_stop,
            is_intercity_stop=target_stop.is_intercity_stop,
            stop_type=stop_type_val,
            address=target_stop.address,
        )

        return StopArrivalBoard(
            stop=stop_base,
            total_arrivals=len(arrivals),
            arrivals=arrivals,
        )
