"""
Vehicle Capability Resolver.
Dynamically resolves which telemetry and prediction strategies should be employed
based on physical hardware capabilities and current device operating health.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from services.api.app.models.transit_models import Vehicle, Device
from packages.schemas.telemetry import (
    CrowdSource,
    LocationSource,
    ETASource,
    DeviceStatus,
)


class CapabilityResolver:
    @staticmethod
    def resolve_capabilities_for_vehicle(
        db: Session, vehicle_id: str
    ) -> Dict[str, Any]:
        """
        Query vehicle capabilities and active edge device status.
        """
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        device = db.query(Device).filter(Device.vehicle_id == vehicle_id).first()

        # Defaults
        caps = {
            "gps_available": True,
            "cctv_available": True,
            "edge_camera_available": True,
            "crowd_sensor_available": False,
            "edge_processing_available": True,
            "prediction_available": True,
            "device_status": DeviceStatus.ONLINE.value,
        }

        if vehicle:
            caps["gps_available"] = getattr(vehicle, "tracking_capability", True)
            caps["cctv_available"] = getattr(vehicle, "camera_capability", True)
            caps["edge_camera_available"] = getattr(vehicle, "camera_capability", True)
            caps["crowd_sensor_available"] = getattr(vehicle, "crowd_sensor_capability", False)
            caps["prediction_available"] = getattr(vehicle, "prediction_capability", True)

        if device:
            caps["device_status"] = device.status.value if hasattr(device.status, "value") else str(device.status)

        return caps

    @classmethod
    def get_preferred_crowd_source(cls, capabilities: Dict[str, Any], is_camera_stream_healthy: bool = True) -> CrowdSource:
        """
        Determine preferred crowd source based on capability hierarchy:
        1. Live edge camera AI (if CCTV available and device online)
        2. Hardware crowd sensor (if sensor available)
        3. ML Prediction (if prediction capability available)
        4. Historical Estimate fallback
        """
        is_online = capabilities.get("device_status") == DeviceStatus.ONLINE.value
        has_edge_cam = capabilities.get("edge_camera_available", True) and capabilities.get("cctv_available", True)

        if has_edge_cam and is_online and is_camera_stream_healthy:
            return CrowdSource.EDGE_CAMERA
        elif capabilities.get("crowd_sensor_available", False) and is_online:
            return CrowdSource.EDGE_SENSOR
        elif capabilities.get("prediction_available", True):
            return CrowdSource.PREDICTED
        else:
            return CrowdSource.HISTORICAL_ESTIMATE

    @classmethod
    def get_preferred_location_source(cls, capabilities: Dict[str, Any]) -> LocationSource:
        """
        Determine preferred GPS location source.
        """
        if capabilities.get("gps_available", True):
            return LocationSource.OFFICIAL_GPS
        return LocationSource.SIMULATED
