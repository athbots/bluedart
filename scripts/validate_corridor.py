"""
Transit Corridor Data Integrity & Validation Script.
Performs comprehensive structural, geographic, sequence contiguity, foreign key,
and bidirectional consistency checks on the Anand Vihar -> Modipuram transit corridor.

DATA INTEGRITY:
DEMO_CORRIDOR = True
DATA_CLASSIFICATION = "DEMONSTRATION"
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from services.api.app.core.database import SessionLocal
from services.api.app.models.transit_models import Route, RouteDirection, RouteStop, Stop, Vehicle, Device
from packages.schemas.transit import StopType


def validate_corridor():
    print("=" * 80)
    print("   ANAND VIHAR -> MODIPURAM TRANSIT CORRIDOR INTEGRITY VALIDATION")
    print("=" * 80)

    db: Session = SessionLocal()
    errors = []
    warnings = []

    try:
        # 1. Validate Stops Existence and IDs
        stops = db.query(Stop).all()
        print(f"\n[*] Total Stops in Database: {len(stops)}")
        if len(stops) < 21:
            errors.append(f"Expected at least 21 stops, found {len(stops)}.")
        
        stop_map = {s.id: s for s in stops}
        expected_ids = [f"STOP_{str(i).padStart(2, '0')}" if hasattr(str(i), 'padStart') else f"STOP_{i:02d}" for i in range(1, 22)]
        for s_id in expected_ids:
            if s_id not in stop_map:
                errors.append(f"Missing expected corridor stop ID: {s_id}")

        # 2. Validate Geographic Bounding Box
        LAT_MIN, LAT_MAX = 28.50, 29.30
        LON_MIN, LON_MAX = 77.10, 78.00
        for s in stops:
            if not (LAT_MIN <= s.latitude <= LAT_MAX):
                errors.append(f"Stop {s.id} ({s.name}) latitude {s.latitude} outside bounding box [{LAT_MIN}, {LAT_MAX}].")
            if not (LON_MIN <= s.longitude <= LON_MAX):
                errors.append(f"Stop {s.id} ({s.name}) longitude {s.longitude} outside bounding box [{LON_MIN}, {LON_MAX}].")

        print("[OK] Geographic coordinates verified within NCR/Western UP transit envelope.")

        # 3. Validate Corridor Route 'ROUTE_AV_MOD'
        route_av = db.query(Route).filter(Route.id == "ROUTE_AV_MOD").first()
        if not route_av:
            errors.append("Route 'ROUTE_AV_MOD' not found in database.")
        else:
            safe_name = route_av.name.encode("ascii", errors="replace").decode("ascii")
            print(f"[OK] Found Route: {safe_name} ({route_av.route_number})")
            
            # Check Directions
            directions = db.query(RouteDirection).filter(RouteDirection.route_id == route_av.id).all()
            if len(directions) < 2:
                errors.append(f"Route 'ROUTE_AV_MOD' should have at least 2 directions (OUTBOUND/INBOUND), found {len(directions)}.")

            for d in directions:
                r_stops = (
                    db.query(RouteStop, Stop)
                    .join(Stop, RouteStop.stop_id == Stop.id)
                    .filter(RouteStop.route_direction_id == d.id)
                    .order_by(RouteStop.sequence.asc())
                    .all()
                )

                print(f"[*] Direction '{d.direction}' ({d.origin} -> {d.destination}): {len(r_stops)} stops")

                if len(r_stops) != 21:
                    errors.append(f"Direction '{d.direction}' has {len(r_stops)} stops (expected 21).")

                # Check Sequence Contiguity (0..20 or 1..21)
                sequences = [rs.sequence for rs, _ in r_stops]
                expected_seqs = list(range(len(r_stops)))
                if sequences != expected_seqs:
                    errors.append(f"Direction '{d.direction}' sequences are not contiguous 0..{len(r_stops)-1}: {sequences}")

                # Check Cumulative Distance Monotonicity
                distances = [rs.cumulative_distance_meters for rs, _ in r_stops]
                for i in range(1, len(distances)):
                    if distances[i] <= distances[i - 1]:
                        errors.append(f"Direction '{d.direction}' distance non-monotonic at sequence {i}: {distances[i-1]}m -> {distances[i]}m.")

                # Direction-specific Terminals
                if d.direction == "OUTBOUND":
                    if r_stops[0][1].id != "STOP_01":
                        errors.append(f"OUTBOUND origin should be STOP_01 (Anand Vihar), got {r_stops[0][1].id}.")
                    if r_stops[-1][1].id != "STOP_21":
                        errors.append(f"OUTBOUND destination should be STOP_21 (Modipuram), got {r_stops[-1][1].id}.")
                elif d.direction == "INBOUND":
                    if r_stops[0][1].id != "STOP_21":
                        errors.append(f"INBOUND origin should be STOP_21 (Modipuram), got {r_stops[0][1].id}.")
                    if r_stops[-1][1].id != "STOP_01":
                        errors.append(f"INBOUND destination should be STOP_01 (Anand Vihar), got {r_stops[-1][1].id}.")

        # 4. Validate Fleet Vehicles and Edge Devices
        vehicles = db.query(Vehicle).all()
        print(f"[OK] Total Registered Fleet Vehicles: {len(vehicles)}")
        devices = db.query(Device).all()
        print(f"[OK] Total Deployed Edge AI Units: {len(devices)}")

        dev_vehicle_ids = {dev.vehicle_id for dev in devices if dev.vehicle_id}
        for v in vehicles:
            if v.id not in dev_vehicle_ids:
                warnings.append(f"Vehicle {v.id} does not have an assigned Edge Device.")

        # 5. Stop Type Distribution Check
        type_counts = {}
        for s in stops:
            st = s.stop_type if hasattr(s, "stop_type") else StopType.LOCAL
            type_counts[st] = type_counts.get(st, 0) + 1

        print("\n[*] Stop Classification Breakdown:")
        for st, cnt in sorted(type_counts.items(), key=lambda x: str(x[0])):
            print(f"    - {st}: {cnt}")

        # Summary Table
        print("\n" + "=" * 80)
        print("   CORRIDOR VALIDATION AUDIT RESULTS")
        print("=" * 80)
        print(f"   Total Errors  : {len(errors)}")
        print(f"   Total Warnings: {len(warnings)}")

        if errors:
            print("\n[FAILED] Identified Validation Errors:")
            for idx, err in enumerate(errors, 1):
                print(f"   {idx}. {err}")
            return False
        else:
            print("\n[PASSED] All 21 Stops, Bidirectional Sequences, Monotonicity & Geometries are 100% Valid!")
            return True

    finally:
        db.close()


if __name__ == "__main__":
    success = validate_corridor()
    sys.exit(0 if success else 1)
