"""
Transit Domain Schemas with Transit Truth & Reliability Layer.
Pydantic v2 schemas for stops, routes, vehicles, trips, live arrival board, and predictions.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from packages.schemas.telemetry import (
    CrowdLevel,
    CrowdSource,
    LocationSource,
    ETASource,
    TruthStatus,
    DataProvenance,
)


class StopType(str, Enum):
    LOCAL = "LOCAL"
    MAJOR = "MAJOR"
    INTERCHANGE = "INTERCHANGE"
    TERMINAL = "TERMINAL"
    DEPOT = "DEPOT"
    RAIL = "RAIL"
    RAILWAY = "RAILWAY"
    METRO = "METRO"
    METRO_RRTS = "METRO_RRTS"
    INTERCITY = "INTERCITY"
    AIRPORT = "AIRPORT"


class VehicleType(str, Enum):
    E_BUS = "E_BUS"
    DIESEL = "DIESEL"
    CNG = "CNG"
    OTHER = "OTHER"


class TripStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class UserRole(str, Enum):
    PASSENGER = "PASSENGER"
    OPERATOR = "OPERATOR"
    ADMIN = "ADMIN"


class VehicleCapability(BaseModel):
    gps_available: bool = True
    cctv_available: bool = True
    edge_camera_available: bool = True
    crowd_sensor_available: bool = False
    edge_processing_available: bool = True
    prediction_available: bool = True

    # Legacy aliases
    @property
    def gps(self) -> bool:
        return self.gps_available

    @property
    def cctv(self) -> bool:
        return self.cctv_available

    @property
    def edge_crowd_ai(self) -> bool:
        return self.edge_camera_available

    @property
    def crowd_sensor(self) -> bool:
        return self.crowd_sensor_available


class StopBase(BaseModel):
    id: str
    name: str
    city: str = "Ghaziabad"
    state: str = "Uttar Pradesh"
    latitude: float
    longitude: float
    is_major_stop: bool = False
    is_intercity_stop: bool = False
    stop_type: StopType = StopType.LOCAL
    address: Optional[str] = None


class StopWithDistance(StopBase):
    distance_meters: float = Field(..., description="Distance in meters from commuter's location")


class RouteDirectionBase(BaseModel):
    id: str
    route_id: str
    direction: str = "OUTBOUND"  # OUTBOUND or INBOUND
    origin: str
    destination: str


class RouteStopBase(BaseModel):
    id: str
    route_direction_id: str
    stop_id: str
    sequence: int
    scheduled_offset_seconds: int
    cumulative_distance_meters: float
    stop: Optional[StopBase] = None


class RouteBase(BaseModel):
    id: str
    route_number: str
    name: str
    origin: str
    destination: str
    city: str = "Ghaziabad"
    active: bool = True
    directions: List[RouteDirectionBase] = Field(default_factory=list)


class RouteDetail(RouteBase):
    stops: List[RouteStopBase] = Field(default_factory=list)


class VehicleBase(BaseModel):
    id: str
    registration_number: str
    fleet_number: str
    vehicle_type: VehicleType = VehicleType.E_BUS
    capacity: int = 60
    operator_id: str = "DTC_CORP"
    route_id: Optional[str] = None
    status: str = "ACTIVE"
    capabilities: VehicleCapability = Field(default_factory=VehicleCapability)


class LiveBusState(BaseModel):
    vehicle_id: str
    registration_number: str
    fleet_number: str
    vehicle_type: VehicleType = VehicleType.E_BUS
    route_id: Optional[str] = None
    route_number: Optional[str] = None
    route_name: Optional[str] = None
    trip_id: Optional[str] = None
    direction: str = "OUTBOUND"
    
    # Location
    latitude: float
    longitude: float
    speed_kmh: float = 0.0
    heading: float = 0.0
    accuracy_m: float = 5.0
    location_updated_at: datetime
    location_source: LocationSource = LocationSource.OFFICIAL_GPS
    location_status: TruthStatus = TruthStatus.LIVE
    
    # Progression
    current_stop_index: int = 0
    current_stop_id: Optional[str] = None
    current_stop_name: Optional[str] = None
    next_stop_id: Optional[str] = None
    next_stop_name: Optional[str] = None
    route_progress_percentage: float = 0.0
    distance_remaining_meters: float = 0.0
    
    # Crowd
    crowd_level: CrowdLevel = CrowdLevel.MEDIUM
    occupancy_score: float = 0.50
    crowd_confidence: float = 0.90
    crowd_source: CrowdSource = CrowdSource.EDGE_CAMERA
    crowd_status: TruthStatus = TruthStatus.OBSERVED
    crowd_updated_at: datetime
    
    # Standardized Provenance & Trust
    location_provenance: Optional[DataProvenance] = None
    crowd_provenance: Optional[DataProvenance] = None
    is_live: bool = True
    is_stale: bool = False
    age_seconds: int = 0


class StopArrival(BaseModel):
    model_config = {"populate_by_name": True}

    vehicle_id: str
    trip_id: Optional[str] = None
    registration_number: str = Field(default="DL-01-EV-1000")
    fleet_number: str = Field(default="EV-100")
    vehicle_type: VehicleType = Field(default=VehicleType.E_BUS)
    route_id: str
    route_number: str
    route_name: str
    direction: str
    destination: str
    
    # Progress & Relative Position
    current_stop_name: str = "On Route"
    stops_away: int = 0
    distance_meters: float = Field(default=0.0, alias="distance_to_stop_meters")
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    
    # ETA & Decision
    eta_seconds: int
    eta_minutes: int
    eta_confidence: float
    eta_source: str = "LIVE_ESTIMATE"
    eta_status: TruthStatus = TruthStatus.ESTIMATED
    is_fastest: bool = False
    is_most_comfortable: bool = False
    
    # Crowd
    current_crowd_level: CrowdLevel
    current_occupancy_score: float
    crowd_source: CrowdSource
    crowd_status: TruthStatus = TruthStatus.OBSERVED
    crowd_is_live: bool
    
    # Predicted crowd at user stop
    predicted_crowd_at_stop: CrowdLevel
    predicted_occupancy_at_stop: float
    prediction_confidence: float
    
    # Standardized Provenance
    provenance: Optional[DataProvenance] = None
    is_stale: bool = False
    last_updated_seconds_ago: int = 0


class StopArrivalBoard(BaseModel):
    stop: StopBase
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    total_arrivals: int
    arrivals: List[StopArrival] = Field(default_factory=list)


class RouteProgressionNode(BaseModel):
    stop_id: str
    stop_name: str
    display_name: Optional[str] = None
    sequence: int
    latitude: float = 0.0
    longitude: float = 0.0
    cumulative_distance_meters: float
    stop_type: StopType = StopType.LOCAL
    is_major_stop: bool = False
    is_interchange_stop: bool = False
    is_terminal_stop: bool = False
    is_depot: bool = False
    is_passed: bool = False
    is_current: bool = False
    is_next: bool = False
    is_user_stop: bool = False
    distance_from_bus_meters: Optional[float] = None
    estimated_arrival_seconds: Optional[int] = None
    predicted_crowd_level: Optional[CrowdLevel] = None
    crowd_confidence: Optional[float] = None


class RouteProgressionView(BaseModel):
    vehicle_id: str
    registration_number: Optional[str] = None
    route_id: str
    route_number: str
    route_name: str
    direction: str
    origin: str
    destination: str
    current_speed_kmh: float
    route_progress_percentage: float
    stops_passed_count: int = 0
    total_stops_count: int = 21
    current_stop_name: Optional[str] = None
    next_major_stop_name: Optional[str] = None
    current_bus_latitude: Optional[float] = None
    current_bus_longitude: Optional[float] = None
    stops: List[RouteProgressionNode] = Field(default_factory=list)
    user_stop_id: Optional[str] = None
    user_stop_name: Optional[str] = None
    eta_to_user_stop_seconds: Optional[int] = None
    crowd_at_user_stop: Optional[CrowdLevel] = None
    provenance: Optional[DataProvenance] = None
    demo_corridor: bool = True
    data_classification: str = "DEMONSTRATION"
