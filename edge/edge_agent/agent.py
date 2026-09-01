"""
Edge Agent Daemon.
Coordinates camera frame acquisition, crowd inference, health monitoring,
and SQLite offline buffering with HTTP/MQTT upstream synchronization.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import asyncio
import logging
from datetime import datetime, timezone
import httpx
from typing import Optional

from edge.camera_adapter.base import CameraProvider
from edge.camera_adapter.synthetic_adapter import SyntheticCameraProvider
from edge.camera_adapter.crowd_detector import EdgeCrowdDetector
from edge.edge_agent.offline_buffer import OfflineEdgeBuffer
from edge.edge_agent.health_monitor import EdgeHealthMonitor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("edge_agent")


class EdgeAgent:
    def __init__(
        self,
        device_id: str = "DEV_BUS_201_A",
        vehicle_id: str = "BUS_201_A",
        api_base_url: str = "http://localhost:8000/api/v1",
        camera_provider: Optional[CameraProvider] = None,
    ):
        self.device_id = device_id
        self.vehicle_id = vehicle_id
        self.api_base_url = api_base_url
        self.camera = camera_provider or SyntheticCameraProvider()
        self.detector = EdgeCrowdDetector()
        self.buffer = OfflineEdgeBuffer(db_path=f"./edge_buffer_{vehicle_id}.db")
        self.health = EdgeHealthMonitor(device_id, vehicle_id)
        self.is_running = False

    async def start(self):
        self.is_running = True
        await self.camera.start()
        logger.info(f"[OK] Edge Agent started for Vehicle '{self.vehicle_id}', Device '{self.device_id}'")

        # Run loops concurrently
        await asyncio.gather(
            self._crowd_inference_loop(),
            self._health_loop(),
            self._buffer_sync_loop(),
        )

    async def stop(self):
        self.is_running = False
        await self.camera.stop()
        logger.info("[OK] Edge Agent stopped.")

    async def _crowd_inference_loop(self):
        """Captures camera frames, extracts crowd metadata, and enqueues to buffer."""
        while self.is_running:
            try:
                frame = await self.camera.get_frame()
                metadata = self.detector.process_frame(frame)

                payload = {
                    "vehicle_id": self.vehicle_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "occupancy_score": metadata["occupancy_score"],
                    "crowd_level": metadata["crowd_level"],
                    "confidence": metadata["confidence"],
                    "source": metadata["source"],
                }

                # Enqueue in offline SQLite buffer
                self.buffer.enqueue(self.vehicle_id, "crowd", payload)

            except Exception as e:
                logger.warning(f"Error in crowd inference loop: {e}")

            await asyncio.sleep(3.0)

    async def _health_loop(self):
        """Periodically reports hardware diagnostics."""
        while self.is_running:
            try:
                cam_status = self.camera.get_status().get("status") == "ONLINE"
                diag = self.health.collect_diagnostics(camera_ok=cam_status, gps_ok=True, network_ok=True)
                diag["timestamp"] = datetime.now(timezone.utc).isoformat()
                self.buffer.enqueue(self.vehicle_id, "heartbeat", diag)
            except Exception as e:
                logger.warning(f"Error in health loop: {e}")

            await asyncio.sleep(10.0)

    async def _buffer_sync_loop(self):
        """Flushes buffered telemetry to backend REST API with exponential backoff on failure."""
        async with httpx.AsyncClient(timeout=4.0) as client:
            while self.is_running:
                pending_items = self.buffer.get_pending(limit=20)
                for item in pending_items:
                    event_id = item["id"]
                    topic = item["topic"]
                    payload = item["payload"]
                    retry_count = item["retry_count"]

                    url = f"{self.api_base_url}/device/crowd" if topic == "crowd" else f"{self.api_base_url}/device/heartbeat"

                    try:
                        resp = await client.post(url, json=payload)
                        if resp.status_code in (200, 201):
                            self.buffer.acknowledge_success(event_id)
                        else:
                            self.buffer.record_failure(event_id, retry_count)
                    except Exception:
                        # Network down - record retry with backoff
                        self.buffer.record_failure(event_id, retry_count)

                await asyncio.sleep(2.0)


if __name__ == "__main__":
    agent = EdgeAgent()
    asyncio.run(agent.start())
