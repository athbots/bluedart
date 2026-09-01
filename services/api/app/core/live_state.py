"""
Live Fleet State Cache and Event Dispatcher with Transit Truth & Out-of-Order Protection.
Maintains live vehicle state, prevents out-of-order packet corruption, and dispatches real-time WebSocket events.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Set, List
from packages.schemas.telemetry import (
    CrowdLevel,
    CrowdSource,
    LocationSource,
    ETASource,
    TruthStatus,
    DataProvenance,
)
from packages.shared.provenance import (
    assess_freshness,
    build_data_provenance,
    GPS_LIVE_THRESHOLD,
    GPS_STALE_THRESHOLD,
    CROWD_LIVE_THRESHOLD,
    CROWD_STALE_THRESHOLD,
)

logger = logging.getLogger("live_state")


class LiveStateManager:
    """
    High-performance live state repository with out-of-order rejection,
    deduplication, and WebSocket broadcast dispatching.
    """
    def __init__(self):
        self._vehicles: Dict[str, Dict[str, Any]] = {}
        self._processed_messages: Set[str] = set()
        self._stop_subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._bus_subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._fleet_subscribers: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    def is_message_processed(self, message_id: Optional[str]) -> bool:
        """Check if message_id has already been processed for idempotency."""
        if not message_id:
            return False
        return message_id in self._processed_messages

    def mark_message_processed(self, message_id: Optional[str]):
        """Record message_id in deduplication set."""
        if message_id:
            if len(self._processed_messages) > 10000:
                self._processed_messages = set(list(self._processed_messages)[5000:])
            self._processed_messages.add(message_id)

    async def update_location(
        self,
        vehicle_id: str,
        lat: float,
        lon: float,
        speed: float = 0.0,
        heading: float = 0.0,
        accuracy: float = 5.0,
        device_timestamp: Optional[datetime] = None,
        server_received_timestamp: Optional[datetime] = None,
        source: str = LocationSource.OFFICIAL_GPS.value,
        confidence: float = 1.0,
        trip_id: Optional[str] = None,
        sequence_number: Optional[int] = None,
        message_id: Optional[str] = None,
        progression_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Update live vehicle location with out-of-order protection.
        Late/delayed packets will not overwrite newer live state.
        """
        async with self._lock:
            if message_id:
                if self.is_message_processed(message_id):
                    logger.info(f"Deduplicated message {message_id}")
                    return dict(self._vehicles.get(vehicle_id, {}))
                self.mark_message_processed(message_id)

            now = datetime.now(timezone.utc)
            dev_ts = device_timestamp or now
            if dev_ts.tzinfo is None:
                dev_ts = dev_ts.replace(tzinfo=timezone.utc)
            rcv_ts = server_received_timestamp or now
            if rcv_ts.tzinfo is None:
                rcv_ts = rcv_ts.replace(tzinfo=timezone.utc)

            if vehicle_id not in self._vehicles:
                self._vehicles[vehicle_id] = {
                    "vehicle_id": vehicle_id,
                    "registration_number": f"DL-01-EXP-{vehicle_id[-3:] if len(vehicle_id)>=3 else '001'}",
                    "fleet_number": vehicle_id,
                    "vehicle_type": "E_BUS",
                    "route_id": None,
                    "route_number": None,
                    "route_name": None,
                    "trip_id": trip_id,
                    "direction": "OUTBOUND",
                    "latitude": lat,
                    "longitude": lon,
                    "speed_kmh": speed,
                    "heading": heading,
                    "accuracy_m": accuracy,
                    "device_timestamp": dev_ts.isoformat(),
                    "server_received_timestamp": rcv_ts.isoformat(),
                    "location_updated_at": dev_ts.isoformat(),
                    "location_source": source,
                    "location_confidence": confidence,
                    "current_stop_index": 0,
                    "current_stop_id": None,
                    "current_stop_name": None,
                    "next_stop_id": None,
                    "next_stop_name": None,
                    "route_progress_percentage": 0.0,
                    "distance_remaining_meters": 0.0,
                    "crowd_level": CrowdLevel.MEDIUM.value,
                    "occupancy_score": 0.50,
                    "crowd_confidence": 0.85,
                    "crowd_source": CrowdSource.SIMULATED.value,
                    "crowd_updated_at": dev_ts.isoformat(),
                    "crowd_device_timestamp": dev_ts.isoformat(),
                    "is_live": True,
                    "is_stale": False,
                    "status": "ONLINE",
                }

            v = self._vehicles[vehicle_id]

            # Out-of-order check: do not overwrite newer live location
            last_dev_ts_str = v.get("device_timestamp") or v.get("location_updated_at")
            if last_dev_ts_str:
                last_dev_ts = datetime.fromisoformat(last_dev_ts_str.replace("Z", "+00:00"))
                if dev_ts < last_dev_ts:
                    logger.info(f"Ignored out-of-order packet for {vehicle_id} (packet: {dev_ts}, current: {last_dev_ts})")
                    return dict(v)

            v["latitude"] = lat
            v["longitude"] = lon
            v["speed_kmh"] = speed
            v["heading"] = heading
            v["accuracy_m"] = accuracy
            v["device_timestamp"] = dev_ts.isoformat()
            v["server_received_timestamp"] = rcv_ts.isoformat()
            v["location_updated_at"] = dev_ts.isoformat()
            v["location_source"] = source
            v["location_confidence"] = confidence
            if trip_id:
                v["trip_id"] = trip_id

            if progression_data:
                for k, val in progression_data.items():
                    v[k] = val

            freshness = assess_freshness(dev_ts, threshold_seconds=GPS_LIVE_THRESHOLD)
            v["is_live"] = freshness["is_live"]
            v["is_stale"] = freshness["is_stale"]
            v["age_seconds"] = freshness["age_seconds"]

            state_snapshot = dict(v)

        await self._dispatch_bus_update(vehicle_id, state_snapshot)
        await self._dispatch_fleet_update(state_snapshot)
        return state_snapshot

    async def update_crowd(
        self,
        vehicle_id: str,
        occupancy_score: float,
        crowd_level: str,
        confidence: float = 0.90,
        source: str = CrowdSource.EDGE_CAMERA.value,
        device_timestamp: Optional[datetime] = None,
        server_received_timestamp: Optional[datetime] = None,
        sequence_number: Optional[int] = None,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update live crowd observation with out-of-order protection.
        """
        async with self._lock:
            if message_id:
                if self.is_message_processed(message_id):
                    logger.info(f"Deduplicated crowd message {message_id}")
                    return dict(self._vehicles.get(vehicle_id, {}))
                self.mark_message_processed(message_id)

            now = datetime.now(timezone.utc)
            dev_ts = device_timestamp or now
            if dev_ts.tzinfo is None:
                dev_ts = dev_ts.replace(tzinfo=timezone.utc)
            rcv_ts = server_received_timestamp or now

            if vehicle_id not in self._vehicles:
                await self.update_location(vehicle_id, 28.6692, 77.4538, device_timestamp=dev_ts)

            v = self._vehicles[vehicle_id]

            # Out-of-order check
            last_crowd_ts_str = v.get("crowd_device_timestamp") or v.get("crowd_updated_at")
            if last_crowd_ts_str:
                last_crowd_ts = datetime.fromisoformat(last_crowd_ts_str.replace("Z", "+00:00"))
                if dev_ts < last_crowd_ts:
                    logger.info(f"Ignored out-of-order crowd packet for {vehicle_id}")
                    return dict(v)

            v["occupancy_score"] = occupancy_score
            v["crowd_level"] = crowd_level
            v["crowd_confidence"] = confidence
            v["crowd_source"] = source
            v["crowd_updated_at"] = dev_ts.isoformat()
            v["crowd_device_timestamp"] = dev_ts.isoformat()

            state_snapshot = dict(v)

        await self._dispatch_bus_update(vehicle_id, state_snapshot)
        await self._dispatch_fleet_update(state_snapshot)
        return state_snapshot

    async def set_route_context(
        self,
        vehicle_id: str,
        route_id: str,
        route_number: str,
        route_name: str,
        direction: str = "OUTBOUND",
        registration_number: Optional[str] = None,
        fleet_number: Optional[str] = None,
        vehicle_type: str = "E_BUS",
    ):
        """Bind vehicle to active route metadata."""
        async with self._lock:
            if vehicle_id not in self._vehicles:
                self._vehicles[vehicle_id] = {
                    "vehicle_id": vehicle_id,
                    "registration_number": registration_number or f"DL-01-EXP-{vehicle_id[-3:] if len(vehicle_id)>=3 else '001'}",
                    "fleet_number": fleet_number or vehicle_id,
                    "vehicle_type": vehicle_type,
                    "route_id": route_id,
                    "route_number": route_number,
                    "route_name": route_name,
                    "direction": direction,
                    "latitude": 28.6692,
                    "longitude": 77.4538,
                    "speed_kmh": 0.0,
                    "heading": 0.0,
                    "accuracy_m": 5.0,
                    "location_updated_at": datetime.now(timezone.utc).isoformat(),
                    "device_timestamp": datetime.now(timezone.utc).isoformat(),
                    "server_received_timestamp": datetime.now(timezone.utc).isoformat(),
                    "current_stop_index": 0,
                    "current_stop_id": None,
                    "current_stop_name": None,
                    "next_stop_id": None,
                    "next_stop_name": None,
                    "route_progress_percentage": 0.0,
                    "distance_remaining_meters": 0.0,
                    "crowd_level": CrowdLevel.MEDIUM.value,
                    "occupancy_score": 0.50,
                    "crowd_confidence": 0.85,
                    "crowd_source": CrowdSource.SIMULATED.value,
                    "crowd_updated_at": datetime.now(timezone.utc).isoformat(),
                    "is_live": True,
                    "is_stale": False,
                    "status": "ONLINE",
                }
            v = self._vehicles[vehicle_id]
            v["vehicle_id"] = vehicle_id
            v["route_id"] = route_id
            v["route_number"] = route_number
            v["route_name"] = route_name
            v["direction"] = direction
            if registration_number:
                v["registration_number"] = registration_number
            if fleet_number:
                v["fleet_number"] = fleet_number
            v["vehicle_type"] = vehicle_type

    def get_vehicle_state(self, vehicle_id: str, current_time: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """Retrieve live state for a specific vehicle with dynamic freshness."""
        v = self._vehicles.get(vehicle_id)
        if not v:
            return None
        res = dict(v)
        loc_ts_str = res.get("device_timestamp") or res["location_updated_at"]
        loc_ts = datetime.fromisoformat(loc_ts_str.replace("Z", "+00:00"))
        fresh = assess_freshness(loc_ts, threshold_seconds=GPS_LIVE_THRESHOLD, current_time=current_time)
        res["is_live"] = fresh["is_live"]
        res["is_stale"] = fresh["is_stale"]
        res["age_seconds"] = fresh["age_seconds"]
        return res

    def get_all_active_vehicles(self, current_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Retrieve all currently tracked vehicles."""
        results = []
        for v_id in list(self._vehicles.keys()):
            st = self.get_vehicle_state(v_id, current_time=current_time)
            if st:
                results.append(st)
        return results

    # --- WebSocket Subscription Management ---

    async def subscribe_stop(self, stop_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        if stop_id not in self._stop_subscribers:
            self._stop_subscribers[stop_id] = set()
        self._stop_subscribers[stop_id].add(q)
        return q

    async def unsubscribe_stop(self, stop_id: str, q: asyncio.Queue):
        if stop_id in self._stop_subscribers and q in self._stop_subscribers[stop_id]:
            self._stop_subscribers[stop_id].remove(q)

    async def subscribe_bus(self, vehicle_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        if vehicle_id not in self._bus_subscribers:
            self._bus_subscribers[vehicle_id] = set()
        self._bus_subscribers[vehicle_id].add(q)
        return q

    async def unsubscribe_bus(self, vehicle_id: str, q: asyncio.Queue):
        if vehicle_id in self._bus_subscribers and q in self._bus_subscribers[vehicle_id]:
            self._bus_subscribers[vehicle_id].remove(q)

    async def subscribe_fleet(self) -> asyncio.Queue:
        q = asyncio.Queue()
        self._fleet_subscribers.add(q)
        return q

    async def unsubscribe_fleet(self, q: asyncio.Queue):
        if q in self._fleet_subscribers:
            self._fleet_subscribers.remove(q)

    async def broadcast_stop_arrival(self, stop_id: str, payload: Dict[str, Any]):
        if stop_id in self._stop_subscribers:
            for q in list(self._stop_subscribers[stop_id]):
                try:
                    q.put_nowait(payload)
                except asyncio.QueueFull:
                    pass

    async def _dispatch_bus_update(self, vehicle_id: str, payload: Dict[str, Any]):
        if vehicle_id in self._bus_subscribers:
            for q in list(self._bus_subscribers[vehicle_id]):
                try:
                    q.put_nowait(payload)
                except asyncio.QueueFull:
                    pass

    async def _dispatch_fleet_update(self, payload: Dict[str, Any]):
        for q in list(self._fleet_subscribers):
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                pass


live_state = LiveStateManager()
