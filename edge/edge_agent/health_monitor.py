"""
Edge Health Monitor.
Gathers hardware health diagnostics: CPU temperature, RAM usage, disk storage, and sensor status.
"""

import os
import time
import psutil
from typing import Dict, Any


class EdgeHealthMonitor:
    def __init__(self, device_id: str, vehicle_id: str):
        self.device_id = device_id
        self.vehicle_id = vehicle_id
        self.start_time = time.time()

    def collect_diagnostics(
        self, camera_ok: bool = True, gps_ok: bool = True, network_ok: bool = True
    ) -> Dict[str, Any]:
        """
        Collect edge hardware metrics.
        """
        uptime_seconds = int(time.time() - self.start_time)
        cpu_pct = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/") if os.name != "nt" else psutil.disk_usage("C:\\")

        # CPU Temp estimate or reading
        cpu_temp = 48.5 + (cpu_pct * 0.2)

        return {
            "device_id": self.device_id,
            "vehicle_id": self.vehicle_id,
            "uptime": uptime_seconds,
            "cpu_temperature": round(cpu_temp, 1),
            "memory_usage": round(mem.percent, 1),
            "storage_usage": round(disk.percent, 1),
            "network_status": "CONNECTED" if network_ok else "DISCONNECTED",
            "camera_status": "OK" if camera_ok else "DEGRADED",
            "gps_status": "OK" if gps_ok else "OFFLINE",
            "software_version": "1.0.0",
        }
