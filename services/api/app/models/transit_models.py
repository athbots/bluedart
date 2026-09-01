"""
SQLAlchemy ORM Models for Smart Transit Intelligence System.
Defines tables, relationships, constraints, and indices for all core domain entities.
"""

import uuid
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Index,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from services.api.app.core.database import Base
from packages.schemas.telemetry import CrowdLevel, CrowdSource, DeviceType, DeviceStatus
from packages.schemas.transit import VehicleType, TripStatus, UserRole, StopType


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    registration_number = Column(String(32), unique=True, nullable=False, index=True)
    fleet_number = Column(String(32), unique=True, nullable=False, index=True)
    vehicle_type = Column(SQLEnum(VehicleType), default=VehicleType.E_BUS, nullable=False)
    capacity = Column(Integer, default=60, nullable=False)
    operator_id = Column(String(64), default="DTC_OPERATOR", nullable=False)
    route_id = Column(String(64), ForeignKey("routes.id"), nullable=True)
    status = Column(String(32), default="ACTIVE", nullable=False)
    
    # Capabilities
    tracking_capability = Column(Boolean, default=True)
    camera_capability = Column(Boolean, default=True)
    crowd_sensor_capability = Column(Boolean, default=False)
    prediction_capability = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    route = relationship("Route", back_populates="vehicles")
    trips = relationship("Trip", back_populates="vehicle")
    devices = relationship("Device", back_populates="vehicle")
    locations = relationship("VehicleLocation", back_populates="vehicle")
    crowd_observations = relationship("CrowdObservation", back_populates="vehicle")


class Route(Base):
    __tablename__ = "routes"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    route_number = Column(String(32), unique=True, nullable=False, index=True)
    name = Column(String(128), nullable=False)
    origin = Column(String(128), nullable=False)
    destination = Column(String(128), nullable=False)
    city = Column(String(64), default="Ghaziabad", nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vehicles = relationship("Vehicle", back_populates="route")
    directions = relationship("RouteDirection", back_populates="route", cascade="all, delete-orphan")


class RouteDirection(Base):
    __tablename__ = "route_directions"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    route_id = Column(String(64), ForeignKey("routes.id"), nullable=False, index=True)
    direction = Column(String(32), default="OUTBOUND", nullable=False)  # OUTBOUND / INBOUND
    origin = Column(String(128), nullable=False)
    destination = Column(String(128), nullable=False)

    # Relationships
    route = relationship("Route", back_populates="directions")
    route_stops = relationship("RouteStop", back_populates="route_direction", cascade="all, delete-orphan", order_by="RouteStop.sequence")
    trips = relationship("Trip", back_populates="route_direction")


class Stop(Base):
    __tablename__ = "stops"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    name = Column(String(128), nullable=False, index=True)
    display_name = Column(String(128), nullable=True)
    city = Column(String(64), default="Ghaziabad", nullable=False)
    state = Column(String(64), default="Uttar Pradesh", nullable=False)
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    is_major_stop = Column(Boolean, default=False)
    is_intercity_stop = Column(Boolean, default=False)
    is_interchange_stop = Column(Boolean, default=False)
    is_terminal_stop = Column(Boolean, default=False)
    is_depot = Column(Boolean, default=False)
    stop_type = Column(SQLEnum(StopType), default=StopType.LOCAL, nullable=False)
    address = Column(String(256), nullable=True)
    demo_data = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    route_stops = relationship("RouteStop", back_populates="stop")


class RouteStop(Base):
    __tablename__ = "route_stops"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    route_direction_id = Column(String(64), ForeignKey("route_directions.id"), nullable=False, index=True)
    stop_id = Column(String(64), ForeignKey("stops.id"), nullable=False, index=True)
    sequence = Column(Integer, nullable=False)
    scheduled_offset_seconds = Column(Integer, default=0, nullable=False)
    cumulative_distance_meters = Column(Float, default=0.0, nullable=False)

    # Relationships
    route_direction = relationship("RouteDirection", back_populates="route_stops")
    stop = relationship("Stop", back_populates="route_stops")

    __table_args__ = (
        Index("idx_route_dir_sequence", "route_direction_id", "sequence"),
    )


class Trip(Base):
    __tablename__ = "trips"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    vehicle_id = Column(String(64), ForeignKey("vehicles.id"), nullable=False, index=True)
    route_direction_id = Column(String(64), ForeignKey("route_directions.id"), nullable=False, index=True)
    service_date = Column(String(16), nullable=False)  # YYYY-MM-DD
    scheduled_start = Column(DateTime, nullable=True)
    actual_start = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    status = Column(SQLEnum(TripStatus), default=TripStatus.SCHEDULED, nullable=False)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="trips")
    route_direction = relationship("RouteDirection", back_populates="trips")
    locations = relationship("VehicleLocation", back_populates="trip")
    crowd_observations = relationship("CrowdObservation", back_populates="trip")


class VehicleLocation(Base):
    __tablename__ = "vehicle_locations"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    vehicle_id = Column(String(64), ForeignKey("vehicles.id"), nullable=False, index=True)
    trip_id = Column(String(64), ForeignKey("trips.id"), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed = Column(Float, default=0.0)
    heading = Column(Float, default=0.0)
    accuracy = Column(Float, default=5.0)
    source = Column(String(32), default="GPS_HARDWARE")
    confidence = Column(Float, default=1.0)
    message_id = Column(String(64), unique=True, nullable=True, index=True)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="locations")
    trip = relationship("Trip", back_populates="locations")

    __table_args__ = (
        Index("idx_vehicle_loc_time", "vehicle_id", "timestamp"),
    )


class CrowdObservation(Base):
    __tablename__ = "crowd_observations"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    vehicle_id = Column(String(64), ForeignKey("vehicles.id"), nullable=False, index=True)
    trip_id = Column(String(64), ForeignKey("trips.id"), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    occupancy_score = Column(Float, nullable=False)
    crowd_level = Column(SQLEnum(CrowdLevel), nullable=False)
    confidence = Column(Float, default=1.0)
    source = Column(SQLEnum(CrowdSource), default=CrowdSource.SIMULATED)
    stop_id = Column(String(64), ForeignKey("stops.id"), nullable=True)
    metadata_json = Column(Text, nullable=True)
    message_id = Column(String(64), unique=True, nullable=True, index=True)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="crowd_observations")
    trip = relationship("Trip", back_populates="crowd_observations")

    __table_args__ = (
        Index("idx_vehicle_crowd_time", "vehicle_id", "timestamp"),
    )


class CrowdPrediction(Base):
    __tablename__ = "crowd_predictions"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    vehicle_id = Column(String(64), ForeignKey("vehicles.id"), nullable=False, index=True)
    trip_id = Column(String(64), ForeignKey("trips.id"), nullable=True, index=True)
    route_direction_id = Column(String(64), ForeignKey("route_directions.id"), nullable=False)
    target_stop_id = Column(String(64), ForeignKey("stops.id"), nullable=False, index=True)
    prediction_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    predicted_occupancy_score = Column(Float, nullable=False)
    predicted_crowd_level = Column(SQLEnum(CrowdLevel), nullable=False)
    confidence = Column(Float, default=0.85)
    model_version = Column(String(32), default="v1.0.0")
    actual_occupancy_score = Column(Float, nullable=True)
    prediction_error = Column(Float, nullable=True)


class ETAPrediction(Base):
    __tablename__ = "eta_predictions"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    vehicle_id = Column(String(64), ForeignKey("vehicles.id"), nullable=False, index=True)
    trip_id = Column(String(64), ForeignKey("trips.id"), nullable=True, index=True)
    target_stop_id = Column(String(64), ForeignKey("stops.id"), nullable=False, index=True)
    prediction_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    predicted_arrival_time = Column(DateTime, nullable=False)
    confidence = Column(Float, default=0.85)
    model_version = Column(String(32), default="v1.0.0")
    actual_arrival_time = Column(DateTime, nullable=True)
    error_seconds = Column(Integer, nullable=True)


class Device(Base):
    __tablename__ = "devices"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    vehicle_id = Column(String(64), ForeignKey("vehicles.id"), nullable=True, index=True)
    device_type = Column(SQLEnum(DeviceType), default=DeviceType.EDGE_AI, nullable=False)
    serial_number = Column(String(64), unique=True, nullable=False, index=True)
    firmware_version = Column(String(32), default="1.0.0")
    software_version = Column(String(32), default="1.0.0")
    status = Column(SQLEnum(DeviceStatus), default=DeviceStatus.ONLINE, nullable=False)
    last_seen = Column(DateTime, default=datetime.utcnow)

    # Relationships
    vehicle = relationship("Vehicle", back_populates="devices")
    telemetry_logs = relationship("DeviceTelemetry", back_populates="device")


class DeviceTelemetry(Base):
    __tablename__ = "device_telemetry"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    device_id = Column(String(64), ForeignKey("devices.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    cpu_temperature = Column(Float, nullable=True)
    memory_usage = Column(Float, nullable=True)
    storage_usage = Column(Float, nullable=True)
    network_status = Column(String(32), default="CONNECTED")
    camera_status = Column(String(32), default="OK")
    gps_status = Column(String(32), default="OK")
    uptime = Column(Integer, default=0)
    message_id = Column(String(64), unique=True, nullable=True, index=True)

    # Relationships
    device = relationship("Device", back_populates="telemetry_logs")


class User(Base):
    __tablename__ = "users"

    id = Column(String(64), primary_key=True, default=generate_uuid)
    email = Column(String(128), unique=True, nullable=False, index=True)
    password_hash = Column(String(256), nullable=False)
    full_name = Column(String(128), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.OPERATOR, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
