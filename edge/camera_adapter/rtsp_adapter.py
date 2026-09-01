"""
RTSP IP Camera Adapter.
Connects to standard H.264/H.265 RTSP streams from bus CCTV NVRs and industrial edge IP cameras.
"""

import cv2
import numpy as np
from typing import Optional, Dict, Any
from edge.camera_adapter.base import CameraProvider


class RTSPCameraProvider(CameraProvider):
    def __init__(self, rtsp_url: str):
        self.rtsp_url = rtsp_url
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_active = False
        self.frame_count = 0

    async def start(self) -> bool:
        try:
            self.cap = cv2.VideoCapture(self.rtsp_url)
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
            "provider_type": "RTSP_STREAM",
            "rtsp_url": self.rtsp_url,
            "frame_count": self.frame_count,
        }
