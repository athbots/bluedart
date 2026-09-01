"""
USB / V4L2 Camera Adapter.
Connects to USB webcams and CSI ribbon cameras (e.g. Raspberry Pi Camera, Jetson CSI).
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any
from edge.camera_adapter.base import CameraProvider


class USBCameraProvider(CameraProvider):
    def __init__(self, device_index: int = 0):
        self.device_index = device_index
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_active = False
        self.frame_count = 0

    async def start(self) -> bool:
        try:
            self.cap = cv2.VideoCapture(self.device_index)
            self.is_active = self.cap.isOpened()
            return self.is_active
        except Exception:
            self.is_active = False
            return False

    async def get_frame(self) -> Optional[np.ndarray]:
        if not self.is_active or not self.cap:
            return None
        ret, frame = self.cap.read()
        if ret and frame is not None:
            self.frame_count += 1
            return frame
        return None

    async def stop(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        self.is_active = False

    def get_status(self) -> Dict[str, Any]:
        return {
            "status": "ONLINE" if self.is_active else "OFFLINE",
            "provider_type": "USB_CAMERA",
            "device_index": self.device_index,
            "frame_count": self.frame_count,
        }
