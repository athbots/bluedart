"""
Tests for ML Baseline Comparison and Model Drift Monitoring.
Verifies deterministic baselines vs ML predictions, versioning metadata, and drift detection.
"""

import pytest
from ml.inference.predictor import MLPredictor
from packages.schemas.telemetry import CrowdLevel


def test_deterministic_baselines():
    predictor = MLPredictor()

    # 1. Deterministic Crowd Baseline
    level, score, conf = predictor.predict_crowd_baseline(
        hour=9, day_of_week=1, is_major_stop=True, direction=0, stops_away=3, current_occupancy=0.50
    )
    assert level in (CrowdLevel.HIGH, CrowdLevel.VERY_HIGH)
    assert conf == 0.70

    # 2. Deterministic ETA Baseline
    travel_sec = predictor.predict_eta_baseline(
        segment_distance_meters=2000.0, hour=9, day_of_week=1, is_major_stop=True
    )
    assert 300 <= travel_sec <= 450


def test_model_versioning_metadata():
    predictor = MLPredictor()
    meta = predictor.get_model_metadata("crowd_model")
    assert "model_name" in meta
    assert "model_version" in meta
    assert "feature_schema_version" in meta


def test_model_drift_monitor():
    predictor = MLPredictor()

    # Normal healthy predictions (recent errors close to baseline ~45s)
    healthy_report = predictor.evaluate_model_drift([42.0, 48.0, 44.0], historical_baseline_mae=45.0)
    assert healthy_report["status"] == "HEALTHY"
    assert healthy_report["drift_detected"] is False

    # Degraded predictions with severe error (MAE ~75s vs baseline 45s)
    drifted_report = predictor.evaluate_model_drift([78.0, 82.0, 75.0, 80.0], historical_baseline_mae=45.0)
    assert drifted_report["status"] == "RETRAIN_RECOMMENDED"
    assert drifted_report["drift_detected"] is True
