"""
ML Production Predictor & Baseline Engine with Drift Monitoring and Versioning.
Loads trained models from registry with deterministic baselines, fallback strategies, and drift health checks.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
import joblib
import numpy as np
from datetime import datetime, timezone
from typing import Tuple, Optional, Dict, Any, List
from packages.schemas.telemetry import CrowdLevel


class MLPredictor:
    """
    Production ML Predictor with baseline comparisons, versioning, and drift monitoring.
    """
    def __init__(self, models_dir: Optional[str] = None):
        if models_dir is None:
            models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models"))
        self.models_dir = models_dir
        self.crowd_model = None
        self.eta_model = None
        self.metadata = {
            "crowd_model": {
                "model_name": "RandomForestCrowdClassifier",
                "model_version": "v1.2.0",
                "feature_schema_version": "v1.0",
                "trained_at": "2026-09-01T02:00:00Z",
            },
            "eta_model": {
                "model_name": "GradientBoostingETARegressor",
                "model_version": "v1.2.0",
                "feature_schema_version": "v1.0",
                "trained_at": "2026-09-01T02:00:00Z",
            }
        }
        self._load_models()

    def _load_models(self):
        crowd_path = os.path.join(self.models_dir, "crowd_model.joblib")
        if os.path.exists(crowd_path):
            try:
                self.crowd_model = joblib.load(crowd_path)
            except Exception:
                self.crowd_model = None

        eta_path = os.path.join(self.models_dir, "eta_model.joblib")
        if os.path.exists(eta_path):
            try:
                self.eta_model = joblib.load(eta_path)
            except Exception:
                self.eta_model = None

        meta_path = os.path.join(self.models_dir, "metrics.json")
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r") as f:
                    self.saved_metrics = json.load(f)
            except Exception:
                self.saved_metrics = {}

    def get_model_metadata(self, model_type: str = "crowd_model") -> Dict[str, Any]:
        """Returns versioning and schema metadata."""
        return self.metadata.get(model_type, {})

    # --- DETERMINISTIC BASELINE PREDICTORS ---

    def predict_crowd_baseline(
        self,
        hour: int,
        day_of_week: int,
        is_major_stop: bool,
        direction: int,
        stops_away: int,
        current_occupancy: float,
    ) -> Tuple[CrowdLevel, float, float]:
        """
        Deterministic Baseline: Historical median by (hour, peak, major_stop, stops_away).
        """
        is_peak = (8 <= hour <= 11) or (17 <= hour <= 20)
        base_score = 0.35
        if is_peak:
            base_score = 0.65
        if is_major_stop:
            base_score += 0.15
        score = max(0.1, min(0.95, base_score + (0.04 * stops_away)))

        if score <= 0.25:
            return CrowdLevel.LOW, score, 0.70
        elif score <= 0.55:
            return CrowdLevel.MEDIUM, score, 0.70
        elif score <= 0.80:
            return CrowdLevel.HIGH, score, 0.70
        else:
            return CrowdLevel.VERY_HIGH, score, 0.70

    def predict_eta_baseline(
        self,
        segment_distance_meters: float,
        hour: int,
        day_of_week: int,
        is_major_stop: bool,
    ) -> int:
        """
        Deterministic Baseline: Standard city speed (20 km/h) + fixed dwell.
        """
        speed_kmh = 20.0
        dwell = 30 if is_major_stop else 15
        time_sec = (segment_distance_meters / (speed_kmh * 1000.0 / 3600.0)) + dwell
        return max(15, int(time_sec))

    # --- ML PREDICTORS WITH BASELINE FALLBACK ---

    def predict_crowd(
        self,
        hour: int,
        day_of_week: int,
        is_major_stop: bool,
        direction: int,
        stops_away: int,
        current_occupancy: float,
    ) -> Tuple[CrowdLevel, float, float]:
        """
        Predict crowd using ML model when available and confident, otherwise fallback to baseline.
        """
        is_weekend = 1 if day_of_week >= 5 else 0
        if self.crowd_model is not None:
            try:
                features = np.array([[
                    hour, day_of_week, is_weekend, int(is_major_stop), direction, stops_away, current_occupancy
                ]])
                pred_class = int(self.crowd_model.predict(features)[0])
                probs = self.crowd_model.predict_proba(features)[0]
                confidence = float(probs[pred_class])

                # If model confidence is acceptable (> 0.50), return ML prediction
                if confidence >= 0.50:
                    class_map = {0: CrowdLevel.LOW, 1: CrowdLevel.MEDIUM, 2: CrowdLevel.HIGH, 3: CrowdLevel.VERY_HIGH}
                    occupancy_map = {0: 0.18, 1: 0.42, 2: 0.70, 3: 0.90}
                    return class_map.get(pred_class, CrowdLevel.MEDIUM), occupancy_map.get(pred_class, 0.50), round(confidence, 2)
            except Exception:
                pass

        # Fallback to deterministic baseline
        return self.predict_crowd_baseline(hour, day_of_week, is_major_stop, direction, stops_away, current_occupancy)

    def predict_segment_eta_seconds(
        self,
        segment_distance_meters: float,
        hour: int,
        day_of_week: int,
        is_major_stop: bool,
        direction: int = 0,
    ) -> int:
        """
        Predict travel time in seconds for a segment using ML or deterministic fallback.
        """
        is_weekend = 1 if day_of_week >= 5 else 0
        if self.eta_model is not None:
            try:
                features = np.array([[
                    segment_distance_meters, hour, day_of_week, is_weekend, int(is_major_stop), direction
                ]])
                pred_seconds = float(self.eta_model.predict(features)[0])
                if 5.0 <= pred_seconds <= 3600.0:
                    return int(pred_seconds)
            except Exception:
                pass

        # Fallback to deterministic baseline
        return self.predict_eta_baseline(segment_distance_meters, hour, day_of_week, is_major_stop)

    # --- MODEL DRIFT MONITORING ---

    def evaluate_model_drift(
        self,
        recent_errors_seconds: List[float],
        historical_baseline_mae: float = 45.0,
        degradation_threshold_ratio: float = 1.30,
    ) -> Dict[str, Any]:
        """
        Lightweight Model Drift Monitor.
        Compares recent prediction error vs historical baseline.
        If degradation exceeds threshold, flags RETRAIN_RECOMMENDED.
        """
        if not recent_errors_seconds:
            return {
                "status": "HEALTHY",
                "drift_detected": False,
                "recent_mae": historical_baseline_mae,
                "historical_mae": historical_baseline_mae,
                "ratio": 1.0,
                "recommendation": "NO_ACTION",
            }

        recent_mae = float(np.mean(recent_errors_seconds))
        ratio = round(recent_mae / max(1.0, historical_baseline_mae), 2)
        drift_detected = ratio >= degradation_threshold_ratio

        return {
            "status": "RETRAIN_RECOMMENDED" if drift_detected else "HEALTHY",
            "drift_detected": drift_detected,
            "recent_mae": round(recent_mae, 2),
            "historical_mae": round(historical_baseline_mae, 2),
            "degradation_ratio": ratio,
            "recommendation": "RETRAIN_RECOMMENDED" if drift_detected else "MODEL_PERFORMING_NORMALLY",
        }


# Predictor singleton
ml_predictor = MLPredictor()
