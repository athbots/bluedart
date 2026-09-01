"""
Data Provenance and Truth Freshness Layer.
Guarantees transparency, source tracking, timestamp separation, and standardized truth provenance.
Strictly prevents any contradiction between data source and truth status.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
from packages.schemas.telemetry import (
    CrowdSource,
    LocationSource,
    ETASource,
    TruthStatus,
    DataProvenance,
)

# Centralized Freshness & Stale Thresholds (in Seconds)
GPS_LIVE_THRESHOLD = 30
GPS_STALE_THRESHOLD = 60

CROWD_LIVE_THRESHOLD = 60
CROWD_STALE_THRESHOLD = 120

ETA_STALE_THRESHOLD = 180
VERY_STALE_THRESHOLD = 300

# Legacy compatibility constants
STALE_LOCATION_THRESHOLD_SECONDS = GPS_LIVE_THRESHOLD
STALE_CROWD_THRESHOLD_SECONDS = CROWD_LIVE_THRESHOLD
VERY_STALE_THRESHOLD_SECONDS = VERY_STALE_THRESHOLD


def compute_age_seconds(timestamp: datetime, current_time: Optional[datetime] = None) -> int:
    """Compute age in seconds relative to UTC now or reference current_time."""
    now = current_time or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        ts_utc = timestamp.replace(tzinfo=timezone.utc)
    else:
        ts_utc = timestamp
    if now.tzinfo is None:
        now_utc = now.replace(tzinfo=timezone.utc)
    else:
        now_utc = now
    diff = (now_utc - ts_utc).total_seconds()
    return max(0, int(diff))


def assess_freshness(
    timestamp: datetime,
    threshold_seconds: int = GPS_LIVE_THRESHOLD,
    current_time: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Returns freshness evaluation dictionary.
    """
    age = compute_age_seconds(timestamp, current_time=current_time)
    is_live = age <= threshold_seconds
    is_stale = age > threshold_seconds
    is_very_stale = age > VERY_STALE_THRESHOLD

    status_label = "LIVE"
    if is_very_stale:
        status_label = "OFFLINE"
    elif is_stale:
        status_label = "DATA DELAYED"

    return {
        "age_seconds": age,
        "is_live": is_live,
        "is_stale": is_stale,
        "is_very_stale": is_very_stale,
        "status_label": status_label,
    }


def build_data_provenance(
    source: str,
    observed_at: datetime,
    received_at: Optional[datetime] = None,
    confidence: float = 1.0,
    live_threshold_seconds: int = GPS_LIVE_THRESHOLD,
    stale_threshold_seconds: int = GPS_STALE_THRESHOLD,
    current_time: Optional[datetime] = None,
    sequence_number: Optional[int] = None,
    message_id: Optional[str] = None,
) -> DataProvenance:
    """
    Constructs an authoritative DataProvenance object.
    Strictly validates that source and status cannot contradict one another:
    - PREDICTED / ML_PREDICTED -> status PREDICTED
    - HISTORICAL_ESTIMATE / LIVE_ESTIMATE / FALLBACK -> status ESTIMATED
    - EDGE_CAMERA / OFFICIAL_GPS / EDGE_GPS / EDGE_SENSOR -> status LIVE or OBSERVED (or STALE / UNAVAILABLE if old)
    - SIMULATED -> status LIVE or OBSERVED (or STALE / UNAVAILABLE if old)
    """
    now = current_time or datetime.now(timezone.utc)
    rcv = received_at or now
    age = compute_age_seconds(observed_at, current_time=now)

    is_live = age <= live_threshold_seconds
    is_stale = age > live_threshold_seconds

    # Predicted and fallback estimates are never "live" physical sensor feeds
    if source in (
        CrowdSource.PREDICTED.value,
        ETASource.ML_PREDICTED.value,
        LocationSource.PREDICTED.value,
        CrowdSource.HISTORICAL_ESTIMATE.value,
        ETASource.HISTORICAL_ESTIMATE.value,
        ETASource.FALLBACK.value,
    ):
        is_live = False

    # Infallible Canonical Status Resolution
    if age > VERY_STALE_THRESHOLD:
        status = TruthStatus.UNAVAILABLE
    elif source in (CrowdSource.PREDICTED.value, ETASource.ML_PREDICTED.value, LocationSource.PREDICTED.value):
        # Predictions always carry PREDICTED status
        status = TruthStatus.PREDICTED
    elif source in (
        CrowdSource.HISTORICAL_ESTIMATE.value,
        ETASource.HISTORICAL_ESTIMATE.value,
        ETASource.LIVE_ESTIMATE.value,
        ETASource.FALLBACK.value,
    ):
        # Estimates always carry ESTIMATED status
        status = TruthStatus.ESTIMATED
    elif is_stale:
        status = TruthStatus.STALE
    elif source in (
        LocationSource.OFFICIAL_GPS.value,
        LocationSource.EDGE_GPS.value,
        CrowdSource.EDGE_CAMERA.value,
        CrowdSource.EDGE_SENSOR.value,
        CrowdSource.SIMULATED.value,
        LocationSource.SIMULATED.value,
    ):
        status = TruthStatus.LIVE if is_live else TruthStatus.OBSERVED
    else:
        status = TruthStatus.OBSERVED

    return DataProvenance(
        source=source,
        status=status,
        observed_at=observed_at,
        received_at=rcv,
        confidence=round(max(0.0, min(1.0, confidence)), 2),
        freshness_seconds=age,
        is_live=is_live,
        is_stale=is_stale,
        sequence_number=sequence_number,
        message_id=message_id,
    )


def resolve_crowd_provenance(
    has_edge_camera: bool,
    has_sensor: bool,
    last_observation_age_seconds: int,
    prediction_confidence: float = 0.85,
) -> Dict[str, Any]:
    """
    Resolve best crowd source and trust metadata according to the capability hierarchy:
    1. Live edge observation (< 60s) -> LIVE
    2. Live sensor observation (< 60s) -> LIVE
    3. Recent observation (< 180s) -> OBSERVED
    4. ML prediction -> PREDICTED
    5. Fallback heuristics -> ESTIMATED
    """
    if has_edge_camera and last_observation_age_seconds <= CROWD_LIVE_THRESHOLD:
        return {
            "source": CrowdSource.EDGE_CAMERA,
            "is_live": True,
            "confidence": 0.92,
            "status": TruthStatus.LIVE,
            "provenance_badge": "LIVE CCTV AI",
        }
    elif has_sensor and last_observation_age_seconds <= CROWD_LIVE_THRESHOLD:
        return {
            "source": CrowdSource.EDGE_SENSOR,
            "is_live": True,
            "confidence": 0.88,
            "status": TruthStatus.LIVE,
            "provenance_badge": "LIVE SENSOR",
        }
    elif last_observation_age_seconds <= VERY_STALE_THRESHOLD:
        return {
            "source": CrowdSource.SIMULATED,
            "is_live": False,
            "confidence": 0.70,
            "status": TruthStatus.OBSERVED,
            "provenance_badge": "RECENT OBSERVED",
        }
    else:
        return {
            "source": CrowdSource.PREDICTED,
            "is_live": False,
            "confidence": round(prediction_confidence, 2),
            "status": TruthStatus.PREDICTED,
            "provenance_badge": "AI PREDICTED",
        }
