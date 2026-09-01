"""
Tests for Crowd Classification and Temporal Smoothing.
Verifies thresholds, hysteresis behavior, and anti-flicker stability.
"""

import pytest
from packages.shared.crowd_config import CrowdConfig, TemporalCrowdSmoother
from packages.schemas.telemetry import CrowdLevel


def test_crowd_threshold_classification():
    config = CrowdConfig(low_max=0.25, medium_max=0.55, high_max=0.80)

    assert config.classify_raw(0.15) == CrowdLevel.LOW
    assert config.classify_raw(0.40) == CrowdLevel.MEDIUM
    assert config.classify_raw(0.70) == CrowdLevel.HIGH
    assert config.classify_raw(0.92) == CrowdLevel.VERY_HIGH


def test_temporal_smoother_hysteresis_anti_flicker():
    config = CrowdConfig(low_max=0.25, medium_max=0.55, high_max=0.80, hysteresis_margin=0.05)
    smoother = TemporalCrowdSmoother(window_size=5, alpha=0.4, config=config)

    # Initial observations at low crowd
    smoother.add_observation(0.20)
    score, level = smoother.add_observation(0.22)
    assert level == CrowdLevel.LOW

    # A single noisy spike just above threshold (0.28) should NOT immediately flip to MEDIUM
    # because exponential smoothing buffers the value and hysteresis demands solid margin
    score, level = smoother.add_observation(0.28)
    assert score < 0.30

    # Sustained higher observations transition cleanly
    smoother.add_observation(0.65)
    smoother.add_observation(0.70)
    score, level = smoother.add_observation(0.72)
    assert level in (CrowdLevel.MEDIUM, CrowdLevel.HIGH)
