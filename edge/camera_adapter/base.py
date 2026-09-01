"""
Hardware-Agnostic Provider Interfaces for Edge Computing.
Defines abstract contracts for CameraProvider, CrowdProvider, and GPSProvider.
"""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, Optional, Dict, Any
import numpy as np


class CameraProvider(ABC):
    """
    Abstract interface for video/camera feeds (RTSP, USB, Video File, Synthetic).
    """
    @abstractmethod
    async def start(self) -> bool:
        """Initialize and open the camera stream."""
        pass

    @abstractmethod
    async def get_frame(self) -> Optional[np.ndarray]:
        """Capture and return the latest video frame as a numpy array."""
        pass

    @abstractmethod
    async def stop(self):
        """Release camera hardware resources."""
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """Return diagnostic status of the camera stream."""
        pass


class CrowdProvider(ABC):
    """
    Abstract interface for crowd estimation hardware/models.
    """
    @abstractmethod
    async def estimate_crowd(self, frame: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Return {"occupancy_score": float, "crowd_level": str, "confidence": float}."""
        pass


class GPSProvider(ABC):
    """
    Abstract interface for GPS/VLTD/NMEA hardware or simulator.
    """
    @abstractmethod
    async def read_position(self) -> Dict[str, Any]:
        """Return {"latitude": float, "longitude": float, "speed": float, "heading": float, "accuracy": float}."""
        pass
