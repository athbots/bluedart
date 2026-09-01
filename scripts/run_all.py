"""
Unified Launcher for Smart Transit Intelligence System.
Starts the FastAPI Backend, Database Seeding, ML Predictor, Fleet Physics Simulator, and Edge Agent in a single process.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import asyncio
import logging
import uvicorn
from services.api.app.main import app
from services.api.app.core.database import init_db
from scripts.seed_data import seed_database
from services.simulator.fleet_simulator import fleet_simulator
from edge.edge_agent.agent import EdgeAgent

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("unified_launcher")


async def main():
    print("=" * 70)
    print("   SMART TRANSIT INTELLIGENCE SYSTEM — INDIA")
    print("   'Know Your Bus Before It Arrives'")
    print("=" * 70)

    # 1. Initialize & Seed Database
    print("\n[1/4] Initializing Database and Seeding NCR Corridor...")
    seed_database()

    # 2. Start Fleet Simulator
    print("\n[2/4] Initializing Multi-Bus Physics Fleet Simulator...")
    fleet_simulator.initialize_fleet()
    await fleet_simulator.start()

    # 3. Start Edge Agent
    print("\n[3/4] Initializing Edge AI Agent...")
    edge_agent = EdgeAgent(device_id="DEV_BUS_201_A", vehicle_id="BUS_201_A")
    # Run edge agent background tasks
    asyncio.create_task(edge_agent.start())

    # 4. Start FastAPI & WebSocket Server
    print("\n[4/4] Starting FastAPI Server on http://localhost:8000 ...")
    print("  - API Documentation: http://localhost:8000/docs")
    print("  - Admin Dashboard:    http://localhost:3000")
    print("  - Passenger Liveboard: http://localhost:8000/api/v1/stops/STOP_13/arrivals")
    print("\nPress Ctrl+C to stop all services.\n")

    config = uvicorn.Config(app=app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping Smart Transit System...")
