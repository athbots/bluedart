"""
Transit Truth Engine.
Authoritative single source of truth for all bus location, crowd density, and arrival ETA states.
Fuses sensor observations, capabilities, timestamps, and ML predictions using strict provenance and freshness rules.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, Tuple, List
from sqlalchemy.orm import Session
from services.api.app.core.live_state import live_state
from services.api.app.models.transit_models import (
    Vehicle,
    Route,
    RouteDirection,
    RouteStop,
    Stop,
    ETAPrediction,
    CrowdPrediction,
)
from services.api.app.services.capability_resolver import CapabilityResolver
from services.api.app.services.eta_service import ETAService
from ml.inference.predictor import ml_predictor
from packages.schemas.telemetry import (
    CrowdLevel,
    CrowdSource,
    LocationSource,
    ETASource,
    TruthStatus,
    DataProvenance,
)
from packages.shared.provenance import (
    build_data_provenance,
    compute_age_seconds,
    GPS_LIVE_THRESHOLD,
    GPS_STALE_THRESHOLD,
    CROWD_LIVE_THRESHOLD,
    CROWD_STALE_THRESHOLD,
    ETA_STALE_THRESHOLD,
    VERY_STALE_THRESHOLD,
)
from packages.shared.crowd_config import CrowdConfig


class TransitTruthEngine:
    """
    Central Authoritative Truth Engine.
    """
    def __init__(self):
        self.crowd_config = CrowdConfig()

    @classmethod
    def resolve_location(
        cls,
        db: Session,
        vehicle_id: str,
        current_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Resolve authoritative location of a vehicle using the strict location truth hierarchy:
        1. Fresh trusted official GPS
        2. Fresh trusted edge GPS
        3. Validated recent observation
        4. Stale / Unavailable
        A prediction MUST NOT overwrite a valid fresh observation.
        """
        now = current_time or datetime.now(timezone.utc)
        v_state = live_state.get_vehicle_state(vehicle_id, current_time=now)
        caps = CapabilityResolver.resolve_capabilities_for_vehicle(db, vehicle_id)

        if not v_state:
            # Fallback to DB record
            v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
            if not v:
                prov = DataProvenance(
                    source=LocationSource.SIMULATED.value,
                    status=TruthStatus.UNAVAILABLE,
                    observed_at=now,
                    received_at=now,
                    confidence=0.0,
                    freshness_seconds=9999,
                    is_live=False,
                    is_stale=True,
                )
                return {"latitude": 0.0, "longitude": 0.0, "speed_kmh": 0.0, "heading": 0.0, "provenance": prov}

            prov = DataProvenance(
                source=LocationSource.OFFICIAL_GPS.value,
                status=TruthStatus.UNAVAILABLE,
                observed_at=v.updated_at or now,
                received_at=now,
                confidence=0.0,
                freshness_seconds=9999,
                is_live=False,
                is_stale=True,
            )
            return {"latitude": 28.6692, "longitude": 77.4538, "speed_kmh": 0.0, "heading": 0.0, "provenance": prov}

        # Parse timestamps
        dev_ts_str = v_state.get("device_timestamp") or v_state["location_updated_at"]
        dev_ts = datetime.fromisoformat(dev_ts_str.replace("Z", "+00:00"))
        rcv_ts_str = v_state.get("server_received_timestamp") or dev_ts_str
        rcv_ts = datetime.fromisoformat(rcv_ts_str.replace("Z", "+00:00"))

        age = compute_age_seconds(dev_ts, current_time=now)
        raw_source = v_state.get("location_source", LocationSource.OFFICIAL_GPS.value)

        # Apply Location Hierarchy
        if age <= GPS_LIVE_THRESHOLD and caps.get("gps_available", True):
            source = raw_source
            status = TruthStatus.LIVE
            confidence = float(v_state.get("location_confidence", 0.98))
        elif age <= GPS_STALE_THRESHOLD:
            source = raw_source
            status = TruthStatus.OBSERVED
            confidence = 0.85
        elif age <= VERY_STALE_THRESHOLD:
            source = raw_source
            status = TruthStatus.STALE
            confidence = 0.50
        else:
            source = raw_source
            status = TruthStatus.UNAVAILABLE
            confidence = 0.0

        prov = build_data_provenance(
            source=source,
            observed_at=dev_ts,
            received_at=rcv_ts,
            confidence=confidence,
            live_threshold_seconds=GPS_LIVE_THRESHOLD,
            stale_threshold_seconds=GPS_STALE_THRESHOLD,
            current_time=now,
        )

        return {
            "latitude": v_state["latitude"],
            "longitude": v_state["longitude"],
            "speed_kmh": v_state.get("speed_kmh", 0.0),
            "heading": v_state.get("heading", 0.0),
            "accuracy_m": v_state.get("accuracy_m", 5.0),
            "current_stop_index": v_state.get("current_stop_index", 0),
            "current_stop_name": v_state.get("current_stop_name"),
            "route_progress_percentage": v_state.get("route_progress_percentage", 0.0),
            "provenance": prov,
        }

    @classmethod
    def resolve_crowd(
        cls,
        db: Session,
        vehicle_id: str,
        trip_id: Optional[str] = None,
        current_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Resolve authoritative crowd density using the strict crowd truth priority:
        1. Fresh validated edge camera observation (< 60s)
        2. Fresh hardware sensor observation (< 60s)
        3. Recent trusted observation (< 180s)
        4. ML Prediction
        5. Historical baseline heuristic
        6. Unavailable
        """
        now = current_time or datetime.now(timezone.utc)
        v_state = live_state.get_vehicle_state(vehicle_id, current_time=now)
        caps = CapabilityResolver.resolve_capabilities_for_vehicle(db, vehicle_id)
        config = CrowdConfig()

        if not v_state:
            # Fallback to ML / Baseline prior
            pred_level, pred_occ, conf = ml_predictor.predict_crowd(
                hour=now.hour, day_of_week=now.weekday(), is_major_stop=False, direction=0, stops_away=1, current_occupancy=0.40
            )
            prov = DataProvenance(
                source=CrowdSource.PREDICTED.value,
                status=TruthStatus.PREDICTED,
                observed_at=now,
                received_at=now,
                confidence=conf,
                freshness_seconds=0,
                is_live=False,
                is_stale=False,
            )
            return {"occupancy_score": pred_occ, "crowd_level": pred_level, "provenance": prov}

        crowd_ts_str = v_state.get("crowd_device_timestamp") or v_state.get("crowd_updated_at")
        crowd_ts = datetime.fromisoformat(crowd_ts_str.replace("Z", "+00:00"))
        age = compute_age_seconds(crowd_ts, current_time=now)

        raw_source = v_state.get("crowd_source", CrowdSource.EDGE_CAMERA.value)
        raw_occupancy = float(v_state.get("occupancy_score", 0.50))
        raw_level_str = v_state.get("crowd_level", CrowdLevel.MEDIUM.value)

        # 1. Direct PREDICTED source in live state
        if raw_source in (CrowdSource.PREDICTED.value, "PREDICTED"):
            source = CrowdSource.PREDICTED.value
            status = TruthStatus.PREDICTED
            confidence = float(v_state.get("crowd_confidence", 0.84))
            occupancy = raw_occupancy
            level = CrowdLevel(raw_level_str)

        # 2. Fresh Edge Camera
        elif raw_source == CrowdSource.EDGE_CAMERA.value and age <= CROWD_LIVE_THRESHOLD and caps.get("edge_camera_available", True):
            source = CrowdSource.EDGE_CAMERA.value
            status = TruthStatus.LIVE
            confidence = float(v_state.get("crowd_confidence", 0.93))
            occupancy = raw_occupancy
            level = CrowdLevel(raw_level_str)

        # 3. Fresh Edge Sensor
        elif raw_source == CrowdSource.EDGE_SENSOR.value and age <= CROWD_LIVE_THRESHOLD and caps.get("crowd_sensor_available", False):
            source = CrowdSource.EDGE_SENSOR.value
            status = TruthStatus.LIVE
            confidence = float(v_state.get("crowd_confidence", 0.88))
            occupancy = raw_occupancy
            level = CrowdLevel(raw_level_str)

        # 4. Recent Physical Observation (< 120s)
        elif age <= CROWD_STALE_THRESHOLD and raw_source not in (CrowdSource.PREDICTED.value, "PREDICTED"):
            source = raw_source
            status = TruthStatus.OBSERVED
            confidence = 0.72
            occupancy = raw_occupancy
            level = CrowdLevel(raw_level_str)

        # 5. Fallback to ML / Historical Prediction when observation is stale or unavailable
        else:
            pred_level, pred_occ, conf = ml_predictor.predict_crowd(
                hour=now.hour,
                day_of_week=now.weekday(),
                is_major_stop=False,
                direction=0,
                stops_away=1,
                current_occupancy=raw_occupancy,
            )
            source = CrowdSource.PREDICTED.value
            status = TruthStatus.PREDICTED
            confidence = conf
            occupancy = pred_occ
            level = pred_level

        prov = build_data_provenance(
            source=source,
            observed_at=crowd_ts if status != TruthStatus.PREDICTED else now,
            received_at=now,
            confidence=confidence,
            live_threshold_seconds=CROWD_LIVE_THRESHOLD,
            stale_threshold_seconds=CROWD_STALE_THRESHOLD,
            current_time=now,
        )

        return {
            "occupancy_score": round(occupancy, 2),
            "crowd_level": level,
            "provenance": prov,
        }

    @classmethod
    def resolve_eta(
        cls,
        db: Session,
        vehicle_id: str,
        target_stop_id: str,
        route_direction_id: Optional[str] = None,
        current_time: Optional[datetime] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve authoritative arrival ETA.
        Fuses real-time progress, live speed, segment regression model, and dwell assumptions.
        Never allows old predictions to overwrite newer live progress.
        """
        now = current_time or datetime.now(timezone.utc)
        v_state = live_state.get_vehicle_state(vehicle_id, current_time=now)
        if not v_state:
            return None

        # Determine route direction if not supplied
        if not route_direction_id:
            route_id = v_state.get("route_id")
            if not route_id:
                return None
            route = db.query(Route).filter(Route.id == route_id).first()
            if not route or not route.directions:
                return None
            direction_name = v_state.get("direction", "OUTBOUND")
            r_dir = next((d for d in route.directions if d.direction == direction_name), route.directions[0])
            route_direction_id = r_dir.id

        # Calculate hybrid ETA
        eta_raw = ETAService.calculate_eta_to_stop(
            db=db,
            live_bus=v_state,
            target_stop_id=target_stop_id,
            route_direction_id=route_direction_id,
        )
        if not eta_raw:
            return None

        loc_prov = cls.resolve_location(db, vehicle_id, current_time=now)["provenance"]
        source = ETASource.LIVE_ESTIMATE.value if loc_prov.is_live else ETASource.HISTORICAL_ESTIMATE.value

        prov = build_data_provenance(
            source=source,
            observed_at=loc_prov.observed_at,
            received_at=now,
            confidence=eta_raw["confidence"],
            live_threshold_seconds=GPS_LIVE_THRESHOLD,
            stale_threshold_seconds=ETA_STALE_THRESHOLD,
            current_time=now,
        )

        pred_arrival = now + timedelta(seconds=eta_raw["eta_seconds"])

        return {
            "predicted_arrival_time": pred_arrival,
            "eta_seconds": eta_raw["eta_seconds"],
            "eta_minutes": eta_raw["eta_minutes"],
            "stops_away": eta_raw["stops_away"],
            "distance_meters": eta_raw["distance_meters"],
            "provenance": prov,
        }

    @classmethod
    def record_actual_arrival(
        cls,
        db: Session,
        vehicle_id: str,
        trip_id: str,
        stop_id: str,
        actual_arrival_time: datetime,
    ) -> Optional[int]:
        """
        Matches prior ETA prediction and computes ground truth variance in seconds without overwriting prediction.
        """
        pred = (
            db.query(ETAPrediction)
            .filter(
                ETAPrediction.vehicle_id == vehicle_id,
                ETAPrediction.trip_id == trip_id,
                ETAPrediction.target_stop_id == stop_id,
                ETAPrediction.actual_arrival_time.is_(None),
            )
            .order_by(ETAPrediction.prediction_time.desc())
            .first()
        )

        if not pred:
            return None

        pred.actual_arrival_time = actual_arrival_time
        t_actual = actual_arrival_time.replace(tzinfo=timezone.utc) if actual_arrival_time.tzinfo is None else actual_arrival_time
        t_pred = pred.predicted_arrival_time.replace(tzinfo=timezone.utc) if pred.predicted_arrival_time.tzinfo is None else pred.predicted_arrival_time
        error_sec = int(abs((t_actual - t_pred).total_seconds()))
        pred.error_seconds = error_sec
        try:
            db.commit()
            db.refresh(pred)
        except Exception as e:
            logger.error(f"Failed to commit actual arrival: {e}")
            db.rollback()

        return error_sec

    @classmethod
    def record_actual_crowd(
        cls,
        db: Session,
        vehicle_id: str,
        trip_id: str,
        stop_id: str,
        actual_occupancy: float,
        actual_crowd_level: CrowdLevel,
    ) -> Optional[float]:
        """
        Matches prior crowd prediction and computes occupancy error.
        """
        pred = (
            db.query(CrowdPrediction)
            .filter(
                CrowdPrediction.vehicle_id == vehicle_id,
                CrowdPrediction.trip_id == trip_id,
                CrowdPrediction.target_stop_id == stop_id,
                CrowdPrediction.actual_occupancy_score.is_(None),
            )
            .order_by(CrowdPrediction.prediction_time.desc())
            .first()
        )

        if not pred:
            return None

        pred.actual_occupancy_score = actual_occupancy
        error = round(abs(actual_occupancy - pred.predicted_occupancy_score), 3)
        pred.prediction_error = error
        try:
            db.commit()
        except Exception:
            db.rollback()

        return error


# Truth Engine Singleton
truth_engine = TransitTruthEngine()
