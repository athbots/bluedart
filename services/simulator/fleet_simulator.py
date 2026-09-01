"""
Multi-Bus Physics and Fleet Simulator with Deterministic Seed & Failure Scenarios.
Simulates realistic vehicle motion, dwell times, crowd dynamics, GPS noise, out-of-order packets,
and telemetry publishing across the Anand Vihar → Modipuram transit corridor.

DATA INTEGRITY:
DEMO_CORRIDOR = True
DATA_CLASSIFICATION = "DEMONSTRATION"
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import asyncio
import random
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional
import uuid
import httpx

from services.api.app.core.database import SessionLocal
from services.api.app.models.transit_models import Route, RouteDirection, RouteStop, Stop, Vehicle
from services.api.app.core.live_state import live_state
from packages.schemas.telemetry import CrowdLevel, CrowdSource, LocationSource
from packages.shared.geo import calculate_bearing, haversine_distance_meters
from packages.shared.crowd_config import CrowdConfig

logger = logging.getLogger("fleet_simulator")


class SimulatedBusState:
    def __init__(
        self,
        vehicle_id: str,
        route_id: str,
        direction_id: str,
        direction_name: str,
        route_number: str,
        route_name: str,
        stops: List[Dict[str, Any]],
        speed_kmh: float = 28.0,
        initial_occupancy: float = 0.35,
    ):
        self.vehicle_id = vehicle_id
        self.route_id = route_id
        self.direction_id = direction_id
        self.direction_name = direction_name
        self.route_number = route_number
        self.route_name = route_name
        self.stops = stops
        self.target_speed_kmh = speed_kmh
        self.current_speed_kmh = speed_kmh

        # Position State
        self.current_segment_idx = 0
        self.segment_fraction = 0.0
        self.dwell_timer_seconds = 0
        self.is_dwelling = False

        # Start position at first stop
        self.lat = stops[0]["latitude"]
        self.lon = stops[0]["longitude"]
        self.heading = 0.0

        # Crowd dynamics
        self.occupancy_score = initial_occupancy
        self.crowd_config = CrowdConfig()
        self.crowd_level = self.crowd_config.classify_raw(self.occupancy_score)
        self.is_camera_healthy = True
        self.is_network_healthy = True
        self.is_stale_gps = False
        self.out_of_order_mode = False

    def tick(self, delta_seconds: float = 1.0, speed_multiplier: float = 1.0, gps_noise_meters: float = 0.0):
        """Advance simulated physics by delta_seconds with speed multiplier."""
        effective_delta = delta_seconds * speed_multiplier
        if len(self.stops) < 2:
            return

        if self.is_dwelling:
            self.dwell_timer_seconds -= effective_delta
            self.current_speed_kmh = 0.0
            if self.dwell_timer_seconds <= 0:
                self.is_dwelling = False
                self.current_speed_kmh = self.target_speed_kmh * random.uniform(0.85, 1.15)
            return

        curr_stop = self.stops[self.current_segment_idx]
        next_stop = self.stops[min(self.current_segment_idx + 1, len(self.stops) - 1)]

        seg_dist = haversine_distance_meters(
            curr_stop["latitude"], curr_stop["longitude"], next_stop["latitude"], next_stop["longitude"]
        )

        speed_mps = (self.current_speed_kmh * 1000.0) / 3600.0
        distance_moved = speed_mps * effective_delta

        if seg_dist > 0:
            fraction_step = distance_moved / seg_dist
            self.segment_fraction += fraction_step

        if self.segment_fraction >= 1.0:
            # Arrived at next stop
            self.current_segment_idx += 1
            self.segment_fraction = 0.0

            if self.current_segment_idx >= len(self.stops) - 1:
                # Loop / Terminal reached: Reset to beginning
                self.current_segment_idx = 0
                self.segment_fraction = 0.0

            curr_stop = self.stops[self.current_segment_idx]
            self.is_dwelling = True
            self.dwell_timer_seconds = 20.0 if curr_stop.get("is_major_stop", False) else 10.0

            # Dynamic crowd delta at stop
            delta_occ = random.uniform(-0.15, 0.25)
            self.occupancy_score = max(0.05, min(0.98, self.occupancy_score + delta_occ))
            self.crowd_level = self.crowd_config.classify_raw(self.occupancy_score)

        # Interpolate coordinates along segment
        s_from = self.stops[self.current_segment_idx]
        s_to = self.stops[min(self.current_segment_idx + 1, len(self.stops) - 1)]

        self.lat = s_from["latitude"] + (s_to["latitude"] - s_from["latitude"]) * self.segment_fraction
        self.lon = s_from["longitude"] + (s_to["longitude"] - s_from["longitude"]) * self.segment_fraction

        # Calculate heading
        self.heading = calculate_bearing(s_from["latitude"], s_from["longitude"], s_to["latitude"], s_to["longitude"])

        # Inject noise if requested
        if gps_noise_meters > 0.0:
            lat_deg_noise = (gps_noise_meters / 111320.0) * random.uniform(-1, 1)
            lon_deg_noise = (gps_noise_meters / (111320.0 * 0.87)) * random.uniform(-1, 1)
            self.lat += lat_deg_noise
            self.lon += lon_deg_noise


class FleetSimulator:
    def __init__(self):
        self.buses: Dict[str, SimulatedBusState] = {}
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.gps_noise_meters = 0.0
        self.speed_multiplier = 1.0
        self.tick_interval_seconds = 2.0
        self.random_seed: Optional[int] = None

    def initialize_fleet(self, seed: Optional[int] = None, speed: float = 1.0):
        """Load seeded Anand Vihar -> Modipuram routes and initialize fleet."""
        if seed is not None:
            self.random_seed = seed
            random.seed(seed)
        self.speed_multiplier = speed

        db = SessionLocal()
        try:
            self.buses.clear()
            routes = db.query(Route).all()
            for r in routes:
                if not r.directions:
                    continue

                for d in r.directions:
                    route_stops = (
                        db.query(RouteStop, Stop)
                        .join(Stop, RouteStop.stop_id == Stop.id)
                        .filter(RouteStop.route_direction_id == d.id)
                        .order_by(RouteStop.sequence.asc())
                        .all()
                    )
                    if len(route_stops) < 2:
                        continue

                    stops_list = [
                        {
                            "stop_id": s.id,
                            "name": s.name,
                            "latitude": s.latitude,
                            "longitude": s.longitude,
                            "is_major_stop": s.is_major_stop,
                            "sequence": rs.sequence,
                        }
                        for rs, s in route_stops
                    ]

                    # Assign specific buses per direction
                    if d.direction == "OUTBOUND":
                        if r.id == "ROUTE_AV_MOD":
                            # Primary corridor forward buses
                            configs = [
                                ("BUS_102_A", 3, 0.40, 0.76, CrowdLevel.HIGH),    # Near Ghaziabad / Guldhar
                                ("BUS_108_B", 7, 0.60, 0.38, CrowdLevel.LOW),     # Near Muradnagar
                                ("BUS_115_C", 10, 0.20, 0.55, CrowdLevel.MEDIUM), # Near Meerut South
                            ]
                            for b_id, seg_idx, seg_frac, occ, c_level in configs:
                                bus = SimulatedBusState(
                                    vehicle_id=b_id,
                                    route_id=r.id,
                                    direction_id=d.id,
                                    direction_name=d.direction,
                                    route_number=r.route_number,
                                    route_name=r.name,
                                    stops=list(stops_list),
                                    speed_kmh=random.uniform(26.0, 34.0),
                                    initial_occupancy=occ,
                                )
                                bus.current_segment_idx = min(seg_idx, len(stops_list) - 2)
                                bus.segment_fraction = seg_frac
                                bus.crowd_level = c_level
                                self.buses[b_id] = bus
                        elif r.id == "ROUTE_201":
                            bus = SimulatedBusState(
                                vehicle_id="BUS_201_A",
                                route_id=r.id,
                                direction_id=d.id,
                                direction_name=d.direction,
                                route_number=r.route_number,
                                route_name=r.name,
                                stops=list(stops_list),
                                speed_kmh=28.0,
                                initial_occupancy=0.68,
                            )
                            bus.current_segment_idx = 2
                            self.buses["BUS_201_A"] = bus
                        elif r.id == "ROUTE_415":
                            bus = SimulatedBusState(
                                vehicle_id="BUS_415_A",
                                route_id=r.id,
                                direction_id=d.id,
                                direction_name=d.direction,
                                route_number=r.route_number,
                                route_name=r.name,
                                stops=list(stops_list),
                                speed_kmh=30.0,
                                initial_occupancy=0.45,
                            )
                            bus.current_segment_idx = 1
                            self.buses["BUS_415_A"] = bus
                    else:
                        # INBOUND (Reverse direction buses)
                        if r.id == "ROUTE_AV_MOD":
                            b_in = SimulatedBusState(
                                vehicle_id="BUS_505_A",
                                route_id=r.id,
                                direction_id=d.id,
                                direction_name=d.direction,
                                route_number=r.route_number,
                                route_name=r.name,
                                stops=list(stops_list),
                                speed_kmh=30.0,
                                initial_occupancy=0.52,
                            )
                            b_in.current_segment_idx = 4
                            self.buses["BUS_505_A"] = b_in

            print(f"[OK] Simulator initialized {len(self.buses)} active buses (Seed: {seed}, Speed: {speed}x).")
        finally:
            db.close()

    async def start(self):
        if self.is_running:
            return
        if not self.buses:
            self.initialize_fleet()
        self.is_running = True
        self._task = asyncio.create_task(self._simulation_loop())
        logger.info("Fleet simulator started successfully.")

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Fleet simulator stopped.")

    async def _simulation_loop(self):
        """Continuous physics and telemetry push loop."""
        while self.is_running:
            now = datetime.now(timezone.utc)
            for bus_id, bus in self.buses.items():
                bus.tick(
                    delta_seconds=self.tick_interval_seconds,
                    speed_multiplier=self.speed_multiplier,
                    gps_noise_meters=self.gps_noise_meters,
                )

                if not bus.is_network_healthy:
                    continue

                await live_state.set_route_context(
                    vehicle_id=bus.vehicle_id,
                    route_id=bus.route_id,
                    route_number=bus.route_number,
                    route_name=bus.route_name,
                    direction=bus.direction_name,
                )

                curr_stop = bus.stops[bus.current_segment_idx]
                next_stop = bus.stops[min(bus.current_segment_idx + 1, len(bus.stops) - 1)]

                prog_data = {
                    "current_stop_index": bus.current_segment_idx,
                    "current_stop_id": curr_stop["stop_id"],
                    "current_stop_name": curr_stop["name"],
                    "next_stop_id": next_stop["stop_id"],
                    "next_stop_name": next_stop["name"],
                    "route_progress_percentage": round(
                        ((bus.current_segment_idx + bus.segment_fraction) / max(1, len(bus.stops) - 1)) * 100.0, 1
                    ),
                    "distance_remaining_meters": round(
                        (len(bus.stops) - 1 - bus.current_segment_idx) * 2600.0, 1
                    ),
                }

                # Device timestamp
                dev_ts = now
                if bus.is_stale_gps:
                    dev_ts = now - timedelta(seconds=240)

                await live_state.update_location(
                    vehicle_id=bus.vehicle_id,
                    lat=bus.lat,
                    lon=bus.lon,
                    speed=bus.current_speed_kmh,
                    heading=bus.heading,
                    accuracy=5.0,
                    device_timestamp=dev_ts,
                    server_received_timestamp=now,
                    source=LocationSource.OFFICIAL_GPS.value,
                    trip_id=f"TRIP-{bus.vehicle_id}",
                    progression_data=prog_data,
                )

                crowd_source = CrowdSource.EDGE_CAMERA.value if bus.is_camera_healthy else CrowdSource.PREDICTED.value
                await live_state.update_crowd(
                    vehicle_id=bus.vehicle_id,
                    occupancy_score=bus.occupancy_score,
                    crowd_level=bus.crowd_level.value,
                    confidence=0.92 if bus.is_camera_healthy else 0.82,
                    source=crowd_source,
                    device_timestamp=dev_ts,
                    server_received_timestamp=now,
                )

            await asyncio.sleep(self.tick_interval_seconds)


fleet_simulator = FleetSimulator()
