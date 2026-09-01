"""
Tests for ML Inference Predictors.
"""

import pytest
from ml.inference.predictor import MLPredictor
from packages.schemas.telemetry import CrowdLevel


def test_ml_crowd_predictor():
    predictor = MLPredictor()

    # Peak hour at major stop with 5 stops away
    level, occupancy, conf = predictor.predict_crowd(
        hour=9,
        day_of_week=1,
        is_major_stop=True,
        direction=0,
        stops_away=5,
        current_occupancy=0.60,
    )

    assert level in (CrowdLevel.HIGH, CrowdLevel.VERY_HIGH)
    assert occupancy >= 0.65
    assert 0.60 <= conf <= 1.0


def test_ml_eta_segment_predictor():
    predictor = MLPredictor()

    travel_time = predictor.predict_segment_eta_seconds(
        segment_distance_meters=1500.0,
        hour=18,
        day_of_week=2,
        is_major_stop=True,
        direction=0,
    )

    # 1.5km in evening peak with dwell time should take ~150s - 350s
    assert 120 <= travel_time <= 450
