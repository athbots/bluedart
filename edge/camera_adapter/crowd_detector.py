"""
Edge Crowd Detector & Occupancy Engine.
Processes camera frames with OpenCV, extracts passenger occupancy features,
and applies temporal smoothing without transmitting raw passenger video.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import cv2
import numpy as np
from typing import Optional, Dict, Any, Tuple
from packages.schemas.telemetry import CrowdLevel, CrowdSource
from packages.shared.crowd_config import CrowdConfig, TemporalCrowdSmoother


class EdgeCrowdDetector:
    """
    Privacy-first edge crowd inference pipeline.
    """
    def __init__(self, max_bus_capacity_visual_units: int = 25):
        self.max_units = max_bus_capacity_visual_units
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=25, detectShadows=False)
        self.crowd_config = CrowdConfig()
        self.smoother = TemporalCrowdSmoother(window_size=5, alpha=0.35, config=self.crowd_config)

    def process_frame(self, frame: Optional[np.ndarray]) -> Dict[str, Any]:
        """
        Process a single video frame and extract crowd metadata.
        Returns:
            {
                "occupancy_score": float,
                "crowd_level": str,
                "confidence": float,
                "source": "EDGE_CAMERA",
                "detected_units": int
            }
        """
        if frame is None:
            # Fallback estimation
            return {
                "occupancy_score": 0.50,
                "crowd_level": CrowdLevel.MEDIUM.value,
                "confidence": 0.65,
                "source": CrowdSource.SIMULATED.value,
                "detected_units": 0,
            }

        # 1. Preprocessing (Resize & Grayscale)
        small_frame = cv2.resize(frame, (320, 240))
        gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # 2. Foreground / Motion Mask
        fg_mask = self.bg_subtractor.apply(blurred)
        _, thresh = cv2.threshold(fg_mask, 150, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        cleaned_mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # 3. Contour / Blob Area Analysis
        contours, _ = cv2.findContours(cleaned_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        valid_units = 0
        total_foreground_pixels = cv2.countNonZero(cleaned_mask)
        frame_area = 320 * 240
        density_ratio = total_foreground_pixels / frame_area

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area > 120:  # Minimum blob size threshold
                valid_units += 1

        # Hybrid occupancy score combining blob count and pixel density
        blob_score = min(1.0, valid_units / float(self.max_units))
        density_score = min(1.0, density_ratio * 4.5)
        raw_occupancy = (0.6 * blob_score) + (0.4 * density_score)

        # 4. Temporal Smoothing & Hysteresis Classification
        smoothed_score, crowd_level = self.smoother.add_observation(raw_occupancy)

        return {
            "occupancy_score": smoothed_score,
            "crowd_level": crowd_level.value,
            "confidence": 0.93,
            "source": CrowdSource.EDGE_CAMERA.value,
            "detected_units": valid_units,
        }
