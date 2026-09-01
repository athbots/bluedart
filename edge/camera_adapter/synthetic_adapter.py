"""
Synthetic Video and Camera Adapter.
Produces simulated bus interior frames for zero-hardware automated testing and demos.
"""

import asyncio
import numpy as np
import cv2
from typing import Optional, Dict, Any
from edge.camera_adapter.base import CameraProvider


class SyntheticCameraProvider(CameraProvider):
    def __init__(self, width: int = 640, height: int = 480, fps: int = 10):
        self.width = width
        self.height = height
        self.fps = fps
        self.is_active = False
        self.frame_count = 0
        self.simulated_occupancy = 0.45

    async def start(self) -> bool:
        self.is_active = True
        return True

    def set_occupancy_target(self, occupancy: float):
        self.simulated_occupancy = max(0.0, min(1.0, occupancy))

    async def get_frame(self) -> Optional[np.ndarray]:
        if not self.is_active:
            return None

        self.frame_count += 1
        # Create a synthetic bus interior canvas
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        # Background bus corridor tint (slate grey)
        frame[:] = (45, 52, 58)

        # Draw aisle guidelines
        cv2.line(frame, (int(self.width * 0.35), 0), (int(self.width * 0.35), self.height), (70, 80, 90), 2)
        cv2.line(frame, (int(self.width * 0.65), 0), (int(self.width * 0.65), self.height), (70, 80, 90), 2)

        # Draw simulated passenger silhouettes based on simulated_occupancy
        max_people = 30
        num_people = int(self.simulated_occupancy * max_people)

        for i in range(num_people):
            # Deterministic grid distribution
            row = i // 4
            col = i % 4
            x = int(self.width * 0.15 + (col * (self.width * 0.22)))
            y = int(self.height * 0.20 + (row * 50))

            if y < self.height - 40:
                # Privacy-compliant abstract bounding silhouette
                cv2.circle(frame, (x, y), 14, (140, 160, 180), -1)  # head
                cv2.rectangle(frame, (x - 18, y + 14), (x + 18, y + 42), (100, 120, 140), -1)  # torso

        # Telemetry overlay banner
        cv2.putText(
            frame,
            f"EDGE CAMERA SIMULATOR - OCC: {self.simulated_occupancy:.2f}",
            (15, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 220, 120),
            2,
        )

        return frame

    async def stop(self):
        self.is_active = False

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "ONLINE" if self.is_active else "OFFLINE",
            "provider_type": "SYNTHETIC_SIMULATOR",
            "frame_count": self.frame_count,
            "resolution": f"{self.width}x{self.height}",
            "fps": self.fps,
        }
