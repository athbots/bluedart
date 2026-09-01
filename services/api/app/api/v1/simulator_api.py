"""
Simulator API Endpoints.
Allows Admin Dashboard and tests to start, stop, configure, and inject scenarios into the fleet simulator.
"""

from typing import Dict, Any
from fastapi import APIRouter
from services.simulator.fleet_simulator import fleet_simulator
from services.simulator.scenario_runner import ScenarioRunner

router = APIRouter(prefix="/simulator", tags=["Simulator Control"])


@router.post("/start")
async def start_simulator():
    """Start the multi-bus fleet simulator."""
    await fleet_simulator.start()
    return {"status": "RUNNING", "active_buses": len(fleet_simulator.buses)}


@router.post("/stop")
async def stop_simulator():
    """Stop the fleet simulator."""
    await fleet_simulator.stop()
    return {"status": "STOPPED"}


@router.get("/status")
def get_simulator_status() -> Dict[str, Any]:
    """Get current simulator status and active bus count."""
    return {
        "is_running": fleet_simulator.is_running,
        "active_buses_count": len(fleet_simulator.buses),
        "gps_noise_meters": fleet_simulator.gps_noise_meters,
        "tick_interval_seconds": fleet_simulator.tick_interval_seconds,
    }


@router.post("/scenario/{scenario_id}")
async def trigger_scenario(scenario_id: str) -> Dict[str, Any]:
    """
    Trigger a specific test or demo scenario (A through H).
    """
    res = await ScenarioRunner.run_scenario(scenario_id)
    return res
