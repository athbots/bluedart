"""
Automated CLI Demonstration Script for Anand Vihar -> Modipuram Corridor.
Usage: python scripts/demo_runner.py [--scenario ANAND_VIHAR_MODIPURAM] [--seed 42] [--speed 1.0]

DATA INTEGRITY:
DEMO_CORRIDOR = True
DATA_CLASSIFICATION = "DEMONSTRATION"
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import argparse
import asyncio
from datetime import datetime, timezone
from services.simulator.scenario_runner import ScenarioRunner
from scripts.seed_data import seed_database
from services.api.app.core.database import SessionLocal
from services.api.app.services.crowd_service import CrowdService
from services.api.app.services.progression_service import ProgressionService
from services.api.app.services.truth_engine import truth_engine
from services.simulator.fleet_simulator import fleet_simulator
from packages.schemas.telemetry import LocationSource, CrowdSource
from services.api.app.core.live_state import live_state


async def run_demo(scenario: str = "F", seed: int = 42, speed: float = 1.0):
    print("=" * 80)
    print("   SMART TRANSIT INTELLIGENCE SYSTEM - CORRIDOR DEMO")
    print(f"   Corridor: Anand Vihar -> Modipuram (21 Stops)")
    print(f"   Scenario: {scenario} | Seed: {seed} | Speed: {speed}x")
    print("=" * 80)

    print("\n[Step 1] Seeding transit database with Anand Vihar -> Modipuram corridor...")
    seed_database()

    print("\n[Step 2] Initializing Simulator with Seed & Triggering Scenario...")
    fleet_simulator.initialize_fleet(seed=seed, speed=speed)
    res = await ScenarioRunner.run_scenario(scenario)
    print(f"  Result: {res.get('title', scenario)}")
    print(f"  Description: {res.get('description', '')}")

    # Tick physics and push telemetry
    now = datetime.now(timezone.utc)
    target_buses = ["BUS_115_C", "BUS_108_B", "BUS_102_A"]
    for b_id in target_buses:
        if b_id in fleet_simulator.buses:
            bus = fleet_simulator.buses[b_id]
            bus.tick(delta_seconds=1.0)
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
            await live_state.update_location(
                vehicle_id=bus.vehicle_id,
                lat=bus.lat,
                lon=bus.lon,
                speed=bus.current_speed_kmh,
                heading=bus.heading,
                device_timestamp=now,
                server_received_timestamp=now,
                source=LocationSource.OFFICIAL_GPS.value,
                progression_data=prog_data,
            )
            c_src = CrowdSource.EDGE_CAMERA.value if bus.is_camera_healthy else CrowdSource.PREDICTED.value
            await live_state.update_crowd(
                vehicle_id=bus.vehicle_id,
                occupancy_score=bus.occupancy_score,
                crowd_level=bus.crowd_level.value,
                confidence=0.92 if bus.is_camera_healthy else 0.81,
                source=c_src,
                device_timestamp=now,
                server_received_timestamp=now,
            )

    selected_stop = "STOP_10"  # Meerut South
    print(f"\n[Step 3] Fetching Truth-Resolved Liveboard for '{selected_stop}' (Meerut South)...")
    db = SessionLocal()
    try:
        board = CrowdService.get_stop_liveboard(db, selected_stop)
        if board:
            print(f"\n  --- AUTHORITATIVE LIVEBOARD: {board.stop.name.upper()} ---")
            print(f"  Classification: {board.stop.stop_type.value} | Total Approaching: {board.total_arrivals}\n")

            for idx, arr in enumerate(board.arrivals, start=1):
                badge = ""
                if arr.is_fastest:
                    badge = "[FASTEST]"
                elif arr.is_most_comfortable:
                    badge = "[MOST COMFORTABLE]"

                src_label = arr.crowd_source.value if hasattr(arr.crowd_source, "value") else arr.crowd_source
                stat_label = arr.crowd_status.value if hasattr(arr.crowd_status, "value") else arr.crowd_status
                eta_stat = arr.eta_status.value if hasattr(arr.eta_status, "value") else arr.eta_status
                c_level = arr.current_crowd_level.value if hasattr(arr.current_crowd_level, "value") else arr.current_crowd_level
                p_level = arr.predicted_crowd_at_stop.value if hasattr(arr.predicted_crowd_at_stop, "value") else arr.predicted_crowd_at_stop
                print(f"  {idx}. Route {arr.route_number} ({arr.destination}) {badge}")
                print(f"     Vehicle: {arr.vehicle_id} ({arr.registration_number})")
                print(f"     ETA: {arr.eta_minutes} min ({arr.eta_seconds}s) | Source: {arr.eta_source} ({eta_stat})")
                print(f"     Current Crowd: {c_level} (Source: {src_label} | Status: {stat_label})")
                print(f"     Predicted at Your Stop: {p_level} (Confidence: {int(arr.prediction_confidence * 100)}%)")
                print(f"     Current Position: {arr.current_stop_name} ({arr.stops_away} stops away)\n")

        print("[Step 4] Inspecting 3D Route Progression for Bus 115-C (Target: Meerut South)...")
        v_state = live_state.get_vehicle_state("BUS_115_C")
        prog = ProgressionService.get_route_progression_view(db, "BUS_115_C", v_state, user_stop_id=selected_stop)
        if prog:
            print(f"\n  --- 3D ROUTE TIMELINE: Route {prog.route_number} ({prog.origin} -> {prog.destination}) ---")
            print(f"  Progress: {prog.route_progress_percentage}% | Stops Passed: {prog.stops_passed_count} / {prog.total_stops_count}")
            print(f"  Next Major Stop: {prog.next_major_stop_name} | User Stop: {prog.user_stop_name}\n")
            for node in prog.stops:
                marker = "O"
                if node.is_current:
                    marker = "[BUS CURRENT POSITION]"
                elif node.is_user_stop:
                    marker = "[YOUR STOP]"
                elif node.is_passed:
                    marker = "[PASSED]"

                type_tag = f" [{node.stop_type.value}]" if node.is_major_stop or node.is_terminal_stop or node.is_depot else ""
                eta_str = f" (~{round(node.estimated_arrival_seconds / 60)} min)" if node.estimated_arrival_seconds and not node.is_passed else ""
                dist_str = f" [{node.distance_from_bus_meters}m away]" if node.distance_from_bus_meters else ""
                print(f"    |  {marker} {node.name if hasattr(node, 'name') else node.stop_name}{type_tag}{dist_str}{eta_str}")

        print("\n" + "=" * 80)
        print("   [OK] ANAND VIHAR -> MODIPURAM DEMO & VALIDATION COMPLETED")
        print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transit Demo Runner")
    parser.add_argument("--scenario", default="F", help="Scenario ID (A-K or ANAND_VIHAR_MODIPURAM)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--speed", type=float, default=1.0, help="Speed multiplier")
    args = parser.parse_args()

    asyncio.run(run_demo(scenario=args.scenario, seed=args.seed, speed=args.speed))
