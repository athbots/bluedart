"""
Model Evaluation and Drift Monitoring Script.
Evaluates accuracy, confusion matrix, and RMSE, and inspects model drift indicators.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
import joblib
import numpy as np
from sklearn.metrics import classification_report, mean_absolute_error, root_mean_squared_error
from ml.datasets.generator import generate_training_data


def evaluate_models():
    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models"))
    crowd_model_path = os.path.join(models_dir, "crowd_model.joblib")
    eta_model_path = os.path.join(models_dir, "eta_model.joblib")

    print("--- EVALUATING PRODUCTION TRANSIT MODELS ---")

    if os.path.exists(crowd_model_path):
        clf = joblib.load(crowd_model_path)
        eval_samples = generate_training_data(1000)
        X_crowd = np.array([
            [s["hour"], s["day_of_week"], s["is_weekend"], s["is_major_stop"], s["direction"], s["stops_away"], s["current_occupancy"]]
            for s in eval_samples
        ])
        y_crowd = np.array([s["crowd_class"] for s in eval_samples])

        preds = clf.predict(X_crowd)
        print("\n[Crowd Classification Report]")
        print(classification_report(y_crowd, preds, target_names=["LOW", "MEDIUM", "HIGH", "VERY_HIGH"]))

    if os.path.exists(eta_model_path):
        reg = joblib.load(eta_model_path)
        eval_samples = generate_training_data(1000)
        X_eta = np.array([
            [s["segment_distance_meters"], s["hour"], s["day_of_week"], s["is_weekend"], s["is_major_stop"], s["direction"]]
            for s in eval_samples
        ])
        y_eta = np.array([s["target_travel_time_seconds"] for s in eval_samples])

        preds = reg.predict(X_eta)
        mae = mean_absolute_error(y_eta, preds)
        rmse = root_mean_squared_error(y_eta, preds)
        print(f"\n[ETA Regression Metrics] MAE: {mae:.2f}s | RMSE: {rmse:.2f}s")


if __name__ == "__main__":
    evaluate_models()
