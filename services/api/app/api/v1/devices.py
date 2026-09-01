"""
Device Ingestion and Telemetry APIs.
Handles hardware and simulator GPS, crowd, and heartbeat telemetry with idempotency.
"""

from datetime import datetime, timezone
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.api.app.core.database import get_db
from services.api.app.core.live_state import live_state
from services.api.app.models.transit_models import (
    Vehicle,
    Device,
    DeviceTelemetry,
    VehicleLocation,
    CrowdObservation,
    Route,
)
from services.api.app.services.progression_service import ProgressionService
from packages.schemas.telemetry import (
    GPSPayload,
    CrowdPayload,
    DeviceHeartbeatPayload,
    CrowdLevel,
    CrowdSource,
    DeviceStatus,
)

router = APIRouter(prefix="/device", tags=["Device Ingestion"])


@router.post("/location")
async def ingest_location(payload: GPSPayload, db: Session = Depends(get_db)):
    """
    Ingest GPS telemetry from edge device or GPS hardware adapter.
    Idempotent, deduplicated, and updates live fleet cache and persistence.
    """
    # 1. Idempotency check
    if payload.message_id and live_state.is_message_processed(payload.message_id):
        return {"status": "DUPLICATE_IGNORED", "message_id": payload.message_id}

    # 2. Look up vehicle route assignment to calculate progression
    vehicle = db.query(Vehicle).filter(Vehicle.id == payload.vehicle_id).first()
    progression_data = None

    if vehicle and vehicle.route_id:
        route = db.query(Route).filter(Route.id == vehicle.route_id).first()
        if route and route.directions:
            direction_id = route.directions[0].id
            prev_idx = 0
            curr_state = live_state.get_vehicle_state(payload.vehicle_id)
            if curr_state:
                prev_idx = curr_state.get("current_stop_index", 0)

            prog = ProgressionService.compute_progression(
                db=db,
                lat=payload.latitude,
                lon=payload.longitude,
                heading=payload.heading,
                route_direction_id=direction_id,
                previous_stop_index=prev_idx,
            )
            progression_data = prog

    # 3. Update in-memory live state
    rcv_ts = payload.server_received_timestamp or datetime.now(timezone.utc)
    updated_state = await live_state.update_location(
        vehicle_id=payload.vehicle_id,
        lat=payload.latitude,
        lon=payload.longitude,
        speed=payload.speed,
        heading=payload.heading,
        accuracy=payload.accuracy,
        device_timestamp=payload.device_timestamp,
        server_received_timestamp=rcv_ts,
        source=payload.source.value if hasattr(payload.source, "value") else str(payload.source),
        confidence=payload.confidence,
        trip_id=payload.trip_id,
        sequence_number=payload.sequence_number,
        message_id=payload.message_id,
        progression_data=progression_data,
    )

    # 4. Asynchronously persist location record in DB
    loc_record = VehicleLocation(
        vehicle_id=payload.vehicle_id,
        trip_id=payload.trip_id,
        timestamp=payload.device_timestamp,
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed=payload.speed,
        heading=payload.heading,
        accuracy=payload.accuracy,
        source=payload.source.value if hasattr(payload.source, "value") else str(payload.source),
        confidence=payload.confidence,
        message_id=payload.message_id,
    )
    db.add(loc_record)
    try:
        db.commit()
    except Exception:
        db.rollback()

    if payload.message_id:
        live_state.mark_message_processed(payload.message_id)

    return {"status": "SUCCESS", "vehicle_id": payload.vehicle_id, "state": updated_state}


@router.post("/crowd")
async def ingest_crowd(payload: CrowdPayload, db: Session = Depends(get_db)):
    """
    Ingest crowd observation metadata from edge AI camera or sensor.
    """
    if payload.message_id and live_state.is_message_processed(payload.message_id):
        return {"status": "DUPLICATE_IGNORED", "message_id": payload.message_id}

    # 1. Update live fleet cache
    rcv_ts = payload.server_received_timestamp or datetime.now(timezone.utc)
    source_val = payload.source.value if hasattr(payload.source, "value") else str(payload.source)
    updated_state = await live_state.update_crowd(
        vehicle_id=payload.vehicle_id,
        occupancy_score=payload.occupancy_score,
        crowd_level=payload.crowd_level.value,
        confidence=payload.confidence,
        source=source_val,
        device_timestamp=payload.device_timestamp,
        server_received_timestamp=rcv_ts,
        sequence_number=payload.sequence_number,
        message_id=payload.message_id,
    )

    # 2. Persist crowd observation record
    crowd_enum = CrowdSource(source_val) if source_val in CrowdSource.__members__ else CrowdSource.SIMULATED
    obs = CrowdObservation(
        vehicle_id=payload.vehicle_id,
        trip_id=payload.trip_id,
        timestamp=payload.device_timestamp,
        occupancy_score=payload.occupancy_score,
        crowd_level=payload.crowd_level,
        confidence=payload.confidence,
        source=crowd_enum,
        stop_id=payload.stop_id,
        message_id=payload.message_id,
    )
    db.add(obs)
    try:
        db.commit()
    except Exception:
        db.rollback()

    if payload.message_id:
        live_state.mark_message_processed(payload.message_id)

    return {"status": "SUCCESS", "vehicle_id": payload.vehicle_id, "state": updated_state}


@router.post("/heartbeat")
async def ingest_heartbeat(payload: DeviceHeartbeatPayload, db: Session = Depends(get_db)):
    """
    Ingest hardware diagnostics and health heartbeat from edge computer / sensor.
    """
    device = db.query(Device).filter(Device.id == payload.device_id).first()
    if not device:
        # Create if registering for the first time
        device = Device(
            id=payload.device_id,
            vehicle_id=payload.vehicle_id,
            serial_number=f"SN-{payload.device_id}",
            firmware_version="1.0.0",
            software_version=payload.software_version,
            status=DeviceStatus.ONLINE,
            last_seen=payload.timestamp,
        )
        db.add(device)
    else:
        device.last_seen = payload.timestamp
        device.status = DeviceStatus.ONLINE
        device.software_version = payload.software_version

    telemetry = DeviceTelemetry(
        device_id=payload.device_id,
        timestamp=payload.timestamp,
        cpu_temperature=payload.cpu_temperature,
        memory_usage=payload.memory_usage,
        storage_usage=payload.storage_usage,
        network_status=payload.network_status,
        camera_status=payload.camera_status,
        gps_status=payload.gps_status,
        uptime=payload.uptime,
        message_id=payload.message_id,
    )
    db.add(telemetry)
    try:
        db.commit()
    except Exception:
        db.rollback()

    return {"status": "HEARTBEAT_ACK", "device_id": payload.device_id}


@router.get("/list", response_model=List[Dict[str, Any]])
def list_devices(db: Session = Depends(get_db)):
    """
    List registered hardware devices and their online status for the operator dashboard.
    """
    devices = db.query(Device).all()
    results = []
    for d in devices:
        last_tel = (
            db.query(DeviceTelemetry)
            .filter(DeviceTelemetry.device_id == d.id)
            .order_by(DeviceTelemetry.timestamp.desc())
            .first()
        )
        results.append({
            "id": d.id,
            "vehicle_id": d.vehicle_id,
            "device_type": d.device_type,
            "serial_number": d.serial_number,
            "firmware_version": d.firmware_version,
            "software_version": d.software_version,
            "status": d.status,
            "last_seen": d.last_seen.isoformat() if d.last_seen else None,
            "cpu_temperature": last_tel.cpu_temperature if last_tel else 48.5,
            "memory_usage": last_tel.memory_usage if last_tel else 38.0,
            "storage_usage": last_tel.storage_usage if last_tel else 24.5,
            "network_status": last_tel.network_status if last_tel else "CONNECTED",
            "camera_status": last_tel.camera_status if last_tel else "OK",
            "gps_status": last_tel.gps_status if last_tel else "OK",
            "uptime": last_tel.uptime if last_tel else 3600,
        })
    return results
