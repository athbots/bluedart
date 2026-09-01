"""
Video File Camera Adapter.
Streams frames from local prerecorded MP4/AVI bus footage for testing and reproducible evaluation.
"""

import os
import cv2
import numpy as np
from typing import Optional, Dict, Any
from edge.camera_adapter.base import CameraProvider


class VideoFileCameraProvider(CameraProvider):
    def __init__(self, video_path: str, loop: bool = True):
        self.video_path = video_path
        self.loop = loop
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_active = False
        self.frame_count = 0

    async def start(self) -> bool:
        if not os.path.exists(self.video_path):
            self.is_active = False
            return False
        self.cap = cv2.VideoCapture(self.video_path)
        self.is_active = self.cap.isOpened()
        return self.is_active

    async def get_frame(self) -> Optional[np.ndarray]:
        if not self.is_active or not self.cap:
            return None

        ret, frame = self.cap.read()
        if not ret:
            if self.loop:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = self.cap.read()
            else:
                return None

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
            "provider_type": "VIDEO_FILE",
            "video_path": self.video_path,
            "frame_count": self.frame_count,
        }
