"""
WebSocket API Endpoints.
Provides high-frequency real-time event streaming for stop liveboards, bus tracking, and fleet map.
"""

import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.api.app.core.live_state import live_state
from services.api.app.core.database import SessionLocal
from services.api.app.services.crowd_service import CrowdService

logger = logging.getLogger("websockets")
router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws/stops/{stop_id}")
async def websocket_stop_liveboard(websocket: WebSocket, stop_id: str):
    """
    Passenger Stop Liveboard WebSocket:
    Streams live arrivals, crowd levels, and ETA recalculations whenever approaching buses move.
    """
    await websocket.accept()
    queue = await live_state.subscribe_stop(stop_id)
    db = SessionLocal()

    try:
        # Send initial snapshot immediately upon connection
        initial_board = CrowdService.get_stop_liveboard(db, stop_id)
        if initial_board:
            await websocket.send_text(initial_board.model_dump_json())

        # Polling/Event stream loop
        while True:
            try:
                # Wait for broadcast event or periodic interval
                event = await asyncio.wait_for(queue.get(), timeout=3.0)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                # Periodic liveboard refresh
                board = CrowdService.get_stop_liveboard(db, stop_id)
                if board:
                    await websocket.send_text(board.model_dump_json())

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from stop liveboard ws for stop {stop_id}")
    except Exception as e:
        logger.warning(f"Error in stop liveboard ws {stop_id}: {e}")
    finally:
        db.close()
        await live_state.unsubscribe_stop(stop_id, queue)


@router.websocket("/ws/buses/{bus_id}")
async def websocket_bus_telemetry(websocket: WebSocket, bus_id: str):
    """
    Bus Real-Time Progression WebSocket:
    Streams continuous coordinate, speed, crowd, and upcoming stop timeline updates.
    """
    await websocket.accept()
    queue = await live_state.subscribe_bus(bus_id)

    try:
        # Initial state snapshot
        curr_state = live_state.get_vehicle_state(bus_id)
        if curr_state:
            await websocket.send_json(curr_state)

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=2.0)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                curr_state = live_state.get_vehicle_state(bus_id)
                if curr_state:
                    await websocket.send_json(curr_state)

    except WebSocketDisconnect:
        logger.info(f"Client disconnected from bus ws {bus_id}")
    except Exception as e:
        logger.warning(f"Error in bus ws {bus_id}: {e}")
    finally:
        await live_state.unsubscribe_bus(bus_id, queue)


@router.websocket("/ws/fleet")
async def websocket_fleet_overview(websocket: WebSocket):
    """
    Admin Live Fleet WebSocket:
    Streams all active bus coordinates and statuses for the admin live map.
    """
    await websocket.accept()
    queue = await live_state.subscribe_fleet()

    try:
        # Send initial snapshot of all active vehicles
        all_buses = live_state.get_all_active_vehicles()
        await websocket.send_json({"type": "FLEET_SNAPSHOT", "vehicles": all_buses})

        while True:
            try:
                event = await asyncio.wait_for(queue.get(), timeout=3.0)
                await websocket.send_json({"type": "VEHICLE_UPDATE", "data": event})
            except asyncio.TimeoutError:
                all_buses = live_state.get_all_active_vehicles()
                await websocket.send_json({"type": "FLEET_SNAPSHOT", "vehicles": all_buses})

    except WebSocketDisconnect:
        logger.info("Admin disconnected from fleet live stream")
    except Exception as e:
        logger.warning(f"Error in fleet ws: {e}")
    finally:
        await live_state.unsubscribe_fleet(queue)
