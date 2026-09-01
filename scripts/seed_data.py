"""
Seed Script for Smart Transit Intelligence System.
Populates the Anand Vihar → Modipuram Demonstration Corridor:
21 Ordered Transit Stops, Bidirectional Routes (Anand Vihar ⇄ Modipuram), 12 Fleet Buses,
Edge AI Devices, Operator Accounts, and Seed Telemetry.

DATA INTEGRITY NOTICE:
DEMO_CORRIDOR = True
DATA_CLASSIFICATION = "DEMONSTRATION"
Coordinates and stop sequences follow the published Delhi-Meerut reference corridor for bus transit demonstration.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timezone, timedelta
import random
from services.api.app.core.database import SessionLocal, init_db
from services.api.app.models.transit_models import (
    Stop,
    Route,
    RouteDirection,
    RouteStop,
    Vehicle,
    Device,
    CrowdObservation,
    VehicleLocation,
    User,
)
from packages.schemas.transit import VehicleType, UserRole, StopType
from packages.schemas.telemetry import CrowdLevel, CrowdSource, DeviceType, DeviceStatus, LocationSource
from packages.shared.geo import haversine_distance_meters

DEMO_CORRIDOR = True
DATA_CLASSIFICATION = "DEMONSTRATION"

# 21 Stops: Anand Vihar -> Modipuram Corridor
STOPS_DATA = [
    {
        "id": "STOP_01",
        "name": "Anand Vihar",
        "display_name": "Anand Vihar ISBT / Metro / RRTS",
        "city": "Delhi",
        "state": "Delhi",
        "lat": 28.6469,
        "lon": 77.3161,
        "stop_type": StopType.TERMINAL,
        "is_major": True,
        "is_interchange": True,
        "is_terminal": True,
        "is_depot": False,
        "addr": "ISBT Complex & Metro Transit Hub, Anand Vihar",
    },
    {
        "id": "STOP_02",
        "name": "Sahibabad",
        "display_name": "Sahibabad RRTS / Industrial Area",
        "city": "Ghaziabad",
        "state": "Uttar Pradesh",
        "lat": 28.6738,
        "lon": 77.3565,
        "stop_type": StopType.MAJOR,
        "is_major": True,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Link Road & Sahibabad Station Complex",
    },
    {
        "id": "STOP_03",
        "name": "Ghaziabad",
        "display_name": "Ghaziabad Central / Old Bus Stand",
        "city": "Ghaziabad",
        "state": "Uttar Pradesh",
        "lat": 28.6655,
        "lon": 77.4415,
        "stop_type": StopType.TERMINAL,
        "is_major": True,
        "is_interchange": True,
        "is_terminal": True,
        "is_depot": False,
        "addr": "Ambedkar Road, Old Bus Stand & Central Junction",
    },
    {
        "id": "STOP_04",
        "name": "Guldhar",
        "display_name": "Guldhar Station",
        "city": "Ghaziabad",
        "state": "Uttar Pradesh",
        "lat": 28.6975,
        "lon": 77.4580,
        "stop_type": StopType.LOCAL,
        "is_major": False,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Meerut Road, Guldhar",
    },
    {
        "id": "STOP_05",
        "name": "Duhai",
        "display_name": "Duhai Interchange",
        "city": "Ghaziabad",
        "state": "Uttar Pradesh",
        "lat": 28.7360,
        "lon": 77.4880,
        "stop_type": StopType.MAJOR,
        "is_major": True,
        "is_interchange": True,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Eastern Peripheral Expressway Junction, Duhai",
    },
    {
        "id": "STOP_06",
        "name": "Duhai Depot",
        "display_name": "Duhai Depot Operations Hub",
        "city": "Ghaziabad",
        "state": "Uttar Pradesh",
        "lat": 28.7490,
        "lon": 77.4990,
        "stop_type": StopType.DEPOT,
        "is_major": True,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": True,
        "addr": "Transit Maintenance & Fleet Operations Depot, Duhai",
    },
    {
        "id": "STOP_07",
        "name": "Muradnagar",
        "display_name": "Muradnagar Bus Station",
        "city": "Ghaziabad",
        "state": "Uttar Pradesh",
        "lat": 28.7830,
        "lon": 77.5080,
        "stop_type": StopType.MAJOR,
        "is_major": True,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Ordnance Factory Road, Muradnagar",
    },
    {
        "id": "STOP_08",
        "name": "Modi Nagar South",
        "display_name": "Modi Nagar South",
        "city": "Ghaziabad",
        "state": "Uttar Pradesh",
        "lat": 28.8180,
        "lon": 77.5620,
        "stop_type": StopType.LOCAL,
        "is_major": False,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Delhi-Meerut Road, Modinagar South",
    },
    {
        "id": "STOP_09",
        "name": "Modi Nagar North",
        "display_name": "Modi Nagar North Bus Stand",
        "city": "Ghaziabad",
        "state": "Uttar Pradesh",
        "lat": 28.8520,
        "lon": 77.5890,
        "stop_type": StopType.LOCAL,
        "is_major": False,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Modi Complex, Modinagar North",
    },
    {
        "id": "STOP_10",
        "name": "Meerut South",
        "display_name": "Meerut South Interchange (Mohiuddinpur)",
        "city": "Meerut",
        "state": "Uttar Pradesh",
        "lat": 28.9050,
        "lon": 77.6320,
        "stop_type": StopType.MAJOR,
        "is_major": True,
        "is_interchange": True,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Bypass Junction, Meerut South",
    },
    {
        "id": "STOP_11",
        "name": "Partapur",
        "display_name": "Partapur Industrial",
        "city": "Meerut",
        "state": "Uttar Pradesh",
        "lat": 28.9310,
        "lon": 77.6530,
        "stop_type": StopType.LOCAL,
        "is_major": False,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Partapur Flyover & Industrial Estate",
    },
    {
        "id": "STOP_12",
        "name": "Rithani",
        "display_name": "Rithani Stop",
        "city": "Meerut",
        "state": "Uttar Pradesh",
        "lat": 28.9480,
        "lon": 77.6680,
        "stop_type": StopType.LOCAL,
        "is_major": False,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Delhi Road, Rithani",
    },
    {
        "id": "STOP_13",
        "name": "Shatabdi Nagar",
        "display_name": "Shatabdi Nagar Hub",
        "city": "Meerut",
        "state": "Uttar Pradesh",
        "lat": 28.9650,
        "lon": 77.6820,
        "stop_type": StopType.MAJOR,
        "is_major": True,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Sector 2, Shatabdi Nagar Transit Area",
    },
    {
        "id": "STOP_14",
        "name": "Brahmpuri",
        "display_name": "Brahmpuri City",
        "city": "Meerut",
        "state": "Uttar Pradesh",
        "lat": 28.9780,
        "lon": 77.6950,
        "stop_type": StopType.LOCAL,
        "is_major": False,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Brahmpuri Junction, Meerut",
    },
    {
        "id": "STOP_15",
        "name": "Meerut Central",
        "display_name": "Meerut Central Railway & Bus Terminal",
        "city": "Meerut",
        "state": "Uttar Pradesh",
        "lat": 28.9890,
        "lon": 77.7060,
        "stop_type": StopType.TERMINAL,
        "is_major": True,
        "is_interchange": True,
        "is_terminal": True,
        "is_depot": False,
        "addr": "City Railway Station Road, Meerut Central",
    },
    {
        "id": "STOP_16",
        "name": "Bhaisali",
        "display_name": "Bhaisali Bus Terminal",
        "city": "Meerut",
        "state": "Uttar Pradesh",
        "lat": 29.0010,
        "lon": 77.7120,
        "stop_type": StopType.MAJOR,
        "is_major": True,
        "is_interchange": True,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Bhaisali Ground & Bus Depot, Meerut Cantt",
    },
    {
        "id": "STOP_17",
        "name": "Begumpul",
        "display_name": "Begumpul Commercial Center",
        "city": "Meerut",
        "state": "Uttar Pradesh",
        "lat": 29.0120,
        "lon": 77.7180,
        "stop_type": StopType.MAJOR,
        "is_major": True,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Begumpul Chowk & Mall Road, Meerut",
    },
    {
        "id": "STOP_18",
        "name": "MES Colony",
        "display_name": "MES Colony Cantt",
        "city": "Meerut",
        "state": "Uttar Pradesh",
        "lat": 29.0290,
        "lon": 77.7210,
        "stop_type": StopType.LOCAL,
        "is_major": False,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Cantt Area, MES Colony",
    },
    {
        "id": "STOP_19",
        "name": "Daurli",
        "display_name": "Daurli Bypass",
        "city": "Meerut",
        "state": "Uttar Pradesh",
        "lat": 29.0490,
        "lon": 77.7240,
        "stop_type": StopType.LOCAL,
        "is_major": False,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": False,
        "addr": "NH 58 Bypass, Daurli",
    },
    {
        "id": "STOP_20",
        "name": "Meerut North",
        "display_name": "Meerut North Transit Point",
        "city": "Meerut",
        "state": "Uttar Pradesh",
        "lat": 29.0680,
        "lon": 77.7220,
        "stop_type": StopType.MAJOR,
        "is_major": True,
        "is_interchange": False,
        "is_terminal": False,
        "is_depot": False,
        "addr": "Pallavpuram Phase 1, Meerut North",
    },
    {
        "id": "STOP_21",
        "name": "Modipuram",
        "display_name": "Modipuram Terminal & Depot",
        "city": "Meerut",
        "state": "Uttar Pradesh",
        "lat": 29.0880,
        "lon": 77.7180,
        "stop_type": StopType.TERMINAL,
        "is_major": True,
        "is_interchange": True,
        "is_terminal": True,
        "is_depot": True,
        "addr": "Modipuram Flyover Terminal & Depot Complex, Meerut",
    },
]

# Primary Corridor Route + Feeder Expresses
ALL_STOP_IDS = [f"STOP_{i:02d}" for i in range(1, 22)]

ROUTES_DATA = [
    {
        "id": "ROUTE_AV_MOD",
        "number": "101",
        "name": "Anand Vihar ⇄ Modipuram Express",
        "origin": "Anand Vihar",
        "destination": "Modipuram",
        "city": "NCR / Meerut",
        "stop_ids": ALL_STOP_IDS,
    },
    {
        "id": "ROUTE_201",
        "number": "201",
        "name": "Anand Vihar ⇄ Meerut South Intercity",
        "origin": "Anand Vihar",
        "destination": "Meerut South",
        "city": "NCR",
        "stop_ids": [f"STOP_{i:02d}" for i in range(1, 11)],
    },
    {
        "id": "ROUTE_415",
        "number": "415",
        "name": "Ghaziabad ⇄ Meerut Central Shuttle",
        "origin": "Ghaziabad",
        "destination": "Meerut Central",
        "city": "NCR / Meerut",
        "stop_ids": [f"STOP_{i:02d}" for i in range(3, 16)],
    },
    {
        "id": "ROUTE_102",
        "number": "102",
        "name": "Muradnagar ⇄ Modipuram Local",
        "origin": "Muradnagar",
        "destination": "Modipuram",
        "city": "Meerut",
        "stop_ids": [f"STOP_{i:02d}" for i in range(7, 22)],
    },
]

VEHICLES_DATA = [
    {"id": "BUS_102_A", "reg": "DL-01-EV-1021", "fleet": "EV-102A", "type": VehicleType.E_BUS, "route": "ROUTE_AV_MOD", "capacity": 65},
    {"id": "BUS_108_B", "reg": "UP-14-EV-1082", "fleet": "EV-108B", "type": VehicleType.E_BUS, "route": "ROUTE_AV_MOD", "capacity": 65},
    {"id": "BUS_115_C", "reg": "UP-15-BT-1153", "fleet": "CNG-115C", "type": VehicleType.CNG, "route": "ROUTE_AV_MOD", "capacity": 60},
    {"id": "BUS_201_A", "reg": "DL-01-EV-2011", "fleet": "EV-201A", "type": VehicleType.E_BUS, "route": "ROUTE_201", "capacity": 65},
    {"id": "BUS_201_B", "reg": "DL-01-EV-2012", "fleet": "EV-201B", "type": VehicleType.E_BUS, "route": "ROUTE_201", "capacity": 65},
    {"id": "BUS_201_C", "reg": "UP-14-BT-2013", "fleet": "CNG-201C", "type": VehicleType.CNG, "route": "ROUTE_201", "capacity": 60},
    {"id": "BUS_415_A", "reg": "UP-14-EV-4151", "fleet": "EV-415A", "type": VehicleType.E_BUS, "route": "ROUTE_415", "capacity": 55},
    {"id": "BUS_415_B", "reg": "UP-14-BT-4152", "fleet": "CNG-415B", "type": VehicleType.CNG, "route": "ROUTE_415", "capacity": 60},
    {"id": "BUS_102_B", "reg": "UP-15-DT-1022", "fleet": "DSL-102B", "type": VehicleType.DIESEL, "route": "ROUTE_102", "capacity": 60},
    {"id": "BUS_102_C", "reg": "UP-15-EV-1023", "fleet": "EV-102C", "type": VehicleType.E_BUS, "route": "ROUTE_102", "capacity": 55},
    {"id": "BUS_505_A", "reg": "DL-01-EV-5051", "fleet": "EV-505A", "type": VehicleType.E_BUS, "route": "ROUTE_AV_MOD", "capacity": 65},
    {"id": "BUS_505_B", "reg": "UP-15-EV-5052", "fleet": "EV-505B", "type": VehicleType.E_BUS, "route": "ROUTE_AV_MOD", "capacity": 65},
]


def seed_database():
    print("Initializing database and seeding Anand Vihar -> Modipuram transit corridor...")
    init_db(drop_all=True)
    db = SessionLocal()

    try:
        # Clear existing transit tables in proper dependency order
        db.query(CrowdObservation).delete()
        db.query(VehicleLocation).delete()
        db.query(Device).delete()
        db.query(RouteStop).delete()
        db.query(RouteDirection).delete()
        db.query(Vehicle).delete()
        db.query(Route).delete()
        db.query(Stop).delete()
        db.query(User).delete()
        db.commit()

        # 1. Seed Stops
        stop_dict = {}
        for s in STOPS_DATA:
            stop = Stop(
                id=s["id"],
                name=s["name"],
                display_name=s.get("display_name", s["name"]),
                city=s["city"],
                state=s["state"],
                latitude=s["lat"],
                longitude=s["lon"],
                stop_type=s.get("stop_type", StopType.LOCAL),
                is_major_stop=s["is_major"],
                is_intercity_stop=s.get("is_interchange", False) or s.get("is_terminal", False),
                is_interchange_stop=s.get("is_interchange", False),
                is_terminal_stop=s.get("is_terminal", False),
                is_depot=s.get("is_depot", False),
                address=s["addr"],
                demo_data=True,
            )
            db.add(stop)
            stop_dict[s["id"]] = stop
        db.commit()
        print(f"[OK] Seeded {len(STOPS_DATA)} Transit Stops along Anand Vihar -> Modipuram Corridor")

        # 2. Seed Routes & Directions
        for r_info in ROUTES_DATA:
            route = Route(
                id=r_info["id"],
                route_number=r_info["number"],
                name=r_info["name"],
                origin=r_info["origin"],
                destination=r_info["destination"],
                city=r_info.get("city", "NCR"),
                active=True,
            )
            db.add(route)
            db.commit()

            # Direction A (OUTBOUND)
            dir_out = RouteDirection(
                id=f"DIR_{r_info['id']}_OUT",
                route_id=route.id,
                direction="OUTBOUND",
                origin=r_info["origin"],
                destination=r_info["destination"],
            )
            db.add(dir_out)

            # Direction B (INBOUND / REVERSE)
            dir_in = RouteDirection(
                id=f"DIR_{r_info['id']}_IN",
                route_id=route.id,
                direction="INBOUND",
                origin=r_info["destination"],
                destination=r_info["origin"],
            )
            db.add(dir_in)
            db.commit()

            # Add Route Stops for Direction A (Forward)
            cum_dist = 0.0
            for seq, s_id in enumerate(r_info["stop_ids"]):
                if seq > 0:
                    prev_id = r_info["stop_ids"][seq - 1]
                    s_prev = stop_dict[prev_id]
                    s_curr = stop_dict[s_id]
                    cum_dist += haversine_distance_meters(s_prev.latitude, s_prev.longitude, s_curr.latitude, s_curr.longitude)

                rs = RouteStop(
                    id=f"RS_{dir_out.id}_{seq:02d}",
                    route_direction_id=dir_out.id,
                    stop_id=s_id,
                    sequence=seq,
                    scheduled_offset_seconds=seq * 180,
                    cumulative_distance_meters=round(cum_dist, 1),
                )
                db.add(rs)

            # Add Route Stops for Direction B (Reverse sequence)
            rev_stop_ids = list(reversed(r_info["stop_ids"]))
            cum_dist_rev = 0.0
            for seq, s_id in enumerate(rev_stop_ids):
                if seq > 0:
                    prev_id = rev_stop_ids[seq - 1]
                    s_prev = stop_dict[prev_id]
                    s_curr = stop_dict[s_id]
                    cum_dist_rev += haversine_distance_meters(s_prev.latitude, s_prev.longitude, s_curr.latitude, s_curr.longitude)

                rs_rev = RouteStop(
                    id=f"RS_{dir_in.id}_{seq:02d}",
                    route_direction_id=dir_in.id,
                    stop_id=s_id,
                    sequence=seq,
                    scheduled_offset_seconds=seq * 180,
                    cumulative_distance_meters=round(cum_dist_rev, 1),
                )
                db.add(rs_rev)

        db.commit()
        print(f"[OK] Seeded {len(ROUTES_DATA)} Bidirectional Routes & Sequences")

        # 3. Seed Vehicles & Edge Devices
        for v_data in VEHICLES_DATA:
            v = Vehicle(
                id=v_data["id"],
                registration_number=v_data["reg"],
                fleet_number=v_data["fleet"],
                vehicle_type=v_data["type"],
                capacity=v_data["capacity"],
                operator_id="DTC_UPSTRC_NCR",
                route_id=v_data["route"],
                status="ACTIVE",
                tracking_capability=True,
                camera_capability=True if v_data["type"] == VehicleType.E_BUS else False,
                crowd_sensor_capability=False,
                prediction_capability=True,
            )
            db.add(v)

            # Assign Edge AI Device
            dev = Device(
                id=f"DEV_{v_data['id']}",
                vehicle_id=v_data["id"],
                device_type=DeviceType.EDGE_AI if v_data["type"] == VehicleType.E_BUS else DeviceType.GPS,
                serial_number=f"SN-AGY-{v_data['id']}-99",
                firmware_version="v2.4.1",
                software_version="1.2.0",
                status=DeviceStatus.ONLINE,
                last_seen=datetime.now(timezone.utc),
            )
            db.add(dev)

        db.commit()
        print(f"[OK] Seeded {len(VEHICLES_DATA)} Fleet Vehicles & Edge AI Units")

        # 4. Seed Admin / Operator User
        admin_user = User(
            id="USER_ADMIN_01",
            email="admin@smarttransit.in",
            password_hash="argon2:$argon2id$v=19$m=65536,t=3,p=4$fakehash",
            full_name="NCR Transit Command Operator",
            role=UserRole.ADMIN,
            active=True,
        )
        db.add(admin_user)
        db.commit()
        print("[OK] Seeded Admin and Command Center Accounts")

        print("\nDatabase Seeding Complete! Ready for Anand Vihar -> Modipuram Real-Time Operations.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
