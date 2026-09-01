"""
Telemetry & Device Payload Schemas with Transit Truth & Reliability Layer.
Pydantic v2 schemas for all device, location, crowd, health payloads, and standardized data provenance.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator


class CrowdLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class LocationSource(str, Enum):
    OFFICIAL_GPS = "OFFICIAL_GPS"
    EDGE_GPS = "EDGE_GPS"
    SIMULATED = "SIMULATED"
    PREDICTED = "PREDICTED"


class CrowdSource(str, Enum):
    EDGE_CAMERA = "EDGE_CAMERA"
    EDGE_SENSOR = "EDGE_SENSOR"
    SIMULATED = "SIMULATED"
    HISTORICAL_ESTIMATE = "HISTORICAL_ESTIMATE"
    PREDICTED = "PREDICTED"
    OPERATOR = "OPERATOR"


class ETASource(str, Enum):
    LIVE_ESTIMATE = "LIVE_ESTIMATE"
    ML_PREDICTED = "ML_PREDICTED"
    HISTORICAL_ESTIMATE = "HISTORICAL_ESTIMATE"
    FALLBACK = "FALLBACK"


class TruthStatus(str, Enum):
    LIVE = "LIVE"
    OBSERVED = "OBSERVED"
    ESTIMATED = "ESTIMATED"
    PREDICTED = "PREDICTED"
    STALE = "STALE"
    UNAVAILABLE = "UNAVAILABLE"


class DeviceType(str, Enum):
    EDGE_AI = "EDGE_AI"
    GPS = "GPS"
    CROWD_SENSOR = "CROWD_SENSOR"
    GATEWAY = "GATEWAY"


class DeviceStatus(str, Enum):
    ONLINE = "ONLINE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


class DataProvenance(BaseModel):
    """
    Authoritative data provenance attached to every resolved location, crowd, and ETA value.
    """
    source: str = Field(..., description="Origin source category, e.g., EDGE_CAMERA, OFFICIAL_GPS, ML_PREDICTED")
    status: TruthStatus = Field(TruthStatus.LIVE, description="Truth status: LIVE, OBSERVED, ESTIMATED, PREDICTED, STALE, UNAVAILABLE")
    observed_at: datetime = Field(..., description="Timestamp when measurement was physically observed on device")
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Timestamp when server received measurement")
    confidence: float = Field(1.0, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    freshness_seconds: int = Field(0, ge=0, description="Elapsed seconds since observation was taken")
    is_live: bool = Field(True, description="True if telemetry is fresh and currently live")
    is_stale: bool = Field(False, description="True if telemetry exceeded stale threshold")
    sequence_number: Optional[int] = Field(None, description="Monotonic sequence identifier from device")
    message_id: Optional[str] = Field(None, description="Idempotency message UUID")


class GPSPayload(BaseModel):
    vehicle_id: str = Field(..., description="Unique vehicle identifier, e.g., BUS_101")
    trip_id: Optional[str] = Field(None, description="Current active trip ID")
    device_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Measurement time on physical device")
    server_received_timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    speed: float = Field(0.0, ge=0.0, description="Speed in km/h")
    heading: float = Field(0.0, ge=0.0, le=360.0, description="Heading in degrees (0-360)")
    accuracy: float = Field(5.0, ge=0.0, description="Accuracy in meters")
    source: Union[LocationSource, str] = Field(LocationSource.OFFICIAL_GPS)
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    sequence_number: Optional[int] = None
    message_id: Optional[str] = Field(None, description="Idempotency message UUID")

    # Backward compatibility alias for legacy timestamp field
    @property
    def timestamp(self) -> datetime:
        return self.device_timestamp

    @field_validator("latitude", "longitude")
    @classmethod
    def validate_nonzero_coords(cls, v: float) -> float:
        if abs(v) < 1e-6:
            raise ValueError("Coordinates cannot be 0.0, 0.0 (Null Island)")
        return v


class CrowdPayload(BaseModel):
    vehicle_id: str = Field(..., description="Vehicle ID")
    trip_id: Optional[str] = None
    device_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    server_received_timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    occupancy_score: float = Field(..., ge=0.0, le=1.0, description="Normalized occupancy 0.0 - 1.0")
    crowd_level: CrowdLevel = Field(..., description="Categorized crowd level")
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    source: Union[CrowdSource, str] = Field(CrowdSource.SIMULATED)
    stop_id: Optional[str] = None
    sequence_number: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    message_id: Optional[str] = None

    @property
    def timestamp(self) -> datetime:
        return self.device_timestamp


class DeviceHeartbeatPayload(BaseModel):
    device_id: str
    vehicle_id: str
    device_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    server_received_timestamp: Optional[datetime] = Field(default_factory=lambda: datetime.now(timezone.utc))
    cpu_temperature: Optional[float] = None
    memory_usage: Optional[float] = None
    storage_usage: Optional[float] = None
    network_status: str = "CONNECTED"
    camera_status: str = "OK"
    gps_status: str = "OK"
    uptime: int = Field(0, description="Uptime in seconds")
    software_version: str = "1.0.0"
    message_id: Optional[str] = None

    @property
    def timestamp(self) -> datetime:
        return self.device_timestamp


class UnifiedTelemetryEvent(BaseModel):
    event_id: str
    vehicle_id: str
    device_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    server_received_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    location: Optional[GPSPayload] = None
    crowd: Optional[CrowdPayload] = None
    heartbeat: Optional[DeviceHeartbeatPayload] = None
