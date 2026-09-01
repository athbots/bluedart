"""
Crowd Classification, Thresholds, and Temporal Smoothing.
Centralized threshold configuration and hysteresis filter to prevent flicker.
"""

from collections import deque
from typing import Deque, Optional, Tuple
from packages.schemas.telemetry import CrowdLevel


class CrowdConfig:
    """
    Centralized configurable crowd occupancy thresholds.
    """
    def __init__(
        self,
        low_max: float = 0.25,
        medium_max: float = 0.55,
        high_max: float = 0.80,
        hysteresis_margin: float = 0.05,
    ):
        self.low_max = low_max
        self.medium_max = medium_max
        self.high_max = high_max
        self.hysteresis_margin = hysteresis_margin

    def classify_raw(self, occupancy_score: float) -> CrowdLevel:
        """Classify without hysteresis."""
        if occupancy_score <= self.low_max:
            return CrowdLevel.LOW
        elif occupancy_score <= self.medium_max:
            return CrowdLevel.MEDIUM
        elif occupancy_score <= self.high_max:
            return CrowdLevel.HIGH
        else:
            return CrowdLevel.VERY_HIGH

    def classify_with_hysteresis(
        self,
        current_score: float,
        previous_level: Optional[CrowdLevel] = None,
    ) -> CrowdLevel:
        """
        Classify with hysteresis margin to prevent boundary flickering.
        """
        if previous_level is None:
            return self.classify_raw(current_score)

        if previous_level == CrowdLevel.LOW:
            if current_score > (self.low_max + self.hysteresis_margin):
                return self.classify_raw(current_score)
            return CrowdLevel.LOW

        elif previous_level == CrowdLevel.MEDIUM:
            if current_score < (self.low_max - self.hysteresis_margin):
                return CrowdLevel.LOW
            elif current_score > (self.medium_max + self.hysteresis_margin):
                return self.classify_raw(current_score)
            return CrowdLevel.MEDIUM

        elif previous_level == CrowdLevel.HIGH:
            if current_score < (self.medium_max - self.hysteresis_margin):
                return CrowdLevel.MEDIUM
            elif current_score > (self.high_max + self.hysteresis_margin):
                return CrowdLevel.VERY_HIGH
            return CrowdLevel.HIGH

        else:  # VERY_HIGH
            if current_score < (self.high_max - self.hysteresis_margin):
                return CrowdLevel.HIGH
            return CrowdLevel.VERY_HIGH


class TemporalCrowdSmoother:
    """
    Rolling window + exponential smoothing + hysteresis filter for edge and backend crowd sensors.
    """
    def __init__(
        self,
        window_size: int = 5,
        alpha: float = 0.35,
        config: Optional[CrowdConfig] = None,
    ):
        self.window_size = window_size
        self.alpha = alpha
        self.config = config or CrowdConfig()
        self.history: Deque[float] = deque(maxlen=window_size)
        self.smoothed_score: Optional[float] = None
        self.current_level: Optional[CrowdLevel] = None

    def add_observation(self, raw_score: float) -> Tuple[float, CrowdLevel]:
        """
        Add a raw occupancy score (0.0 to 1.0) and return smoothed (score, crowd_level).
        """
        clamped_score = max(0.0, min(1.0, float(raw_score)))
        self.history.append(clamped_score)

        if self.smoothed_score is None:
            self.smoothed_score = clamped_score
        else:
            # Exponential moving average
            self.smoothed_score = self.alpha * clamped_score + (1.0 - self.alpha) * self.smoothed_score

        # Apply hysteresis classification
        self.current_level = self.config.classify_with_hysteresis(
            self.smoothed_score, self.current_level
        )

        return round(self.smoothed_score, 3), self.current_level

    def reset(self):
        self.history.clear()
        self.smoothed_score = None
        self.current_level = None
