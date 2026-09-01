"""
ETA Segment Travel Time Model Training Script.
Trains a scikit-learn Gradient Boosting Regressor for segment travel time estimation.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, root_mean_squared_error

from ml.datasets.generator import generate_training_data


def train():
    print("Generating training dataset for ETA segment regression...")
    samples = generate_training_data(6000)

    features = []
    targets = []
    for s in samples:
        f = [
            s["segment_distance_meters"],
            s["hour"],
            s["day_of_week"],
            s["is_weekend"],
            s["is_major_stop"],
            s["direction"],
        ]
        features.append(f)
        targets.append(s["target_travel_time_seconds"])

    X = np.array(features)
    y = np.array(targets)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"Training Gradient Boosting Regressor on {len(X_train)} samples...")
    reg = GradientBoostingRegressor(n_estimators=100, max_depth=5, random_state=42)
    reg.fit(X_train, y_train)

    y_pred = reg.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = root_mean_squared_error(y_test, y_pred)

    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models"))
    os.makedirs(models_dir, exist_ok=True)

    model_path = os.path.join(models_dir, "eta_model.joblib")
    joblib.dump(reg, model_path)

    eta_metrics = {
        "model_type": "GradientBoostingRegressor",
        "model_version": "v1.1.0-gbr",
        "mean_absolute_error_seconds": round(float(mae), 2),
        "root_mean_squared_error_seconds": round(float(rmse), 2),
    }
    with open(os.path.join(models_dir, "eta_metrics.json"), "w") as f:
        json.dump(eta_metrics, f, indent=2)

    print(f"[OK] ETA Model trained! MAE: {mae:.2f}s, RMSE: {rmse:.2f}s")
    print(f"[OK] Model saved to {model_path}")


if __name__ == "__main__":
    train()
