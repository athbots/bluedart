"""
Crowd Classification Model Training Script.
Trains a scikit-learn Random Forest Classifier on historical transit patterns.
Generates metrics.json and feature_schema.json.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import json
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, confusion_matrix

from ml.datasets.generator import generate_training_data


def train():
    print("Generating historical dataset for crowd forecasting...")
    samples = generate_training_data(6000)

    # Feature extraction
    features = []
    labels = []
    for s in samples:
        f = [
            s["hour"],
            s["day_of_week"],
            s["is_weekend"],
            s["is_major_stop"],
            s["direction"],
            s["stops_away"],
            s["current_occupancy"],
        ]
        features.append(f)
        labels.append(s["crowd_class"])

    X = np.array(features)
    y = np.array(labels)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"Training Random Forest Classifier on {len(X_train)} samples...")
    clf = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    prec, rec, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="weighted")
    cm = confusion_matrix(y_test, y_pred).tolist()

    models_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../models"))
    os.makedirs(models_dir, exist_ok=True)

    # Save model
    model_path = os.path.join(models_dir, "crowd_model.joblib")
    joblib.dump(clf, model_path)

    # Metrics
    metrics = {
        "model_type": "RandomForestClassifier",
        "model_version": "v1.2.0-rf",
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "confusion_matrix": cm,
        "classes": ["LOW", "MEDIUM", "HIGH", "VERY_HIGH"],
    }
    with open(os.path.join(models_dir, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    # Feature Schema
    schema = {
        "features": [
            {"name": "hour", "type": "int", "range": [0, 23]},
            {"name": "day_of_week", "type": "int", "range": [0, 6]},
            {"name": "is_weekend", "type": "int", "values": [0, 1]},
            {"name": "is_major_stop", "type": "int", "values": [0, 1]},
            {"name": "direction", "type": "int", "values": [0, 1]},
            {"name": "stops_away", "type": "int", "range": [1, 20]},
            {"name": "current_occupancy", "type": "float", "range": [0.0, 1.0]},
        ],
        "output": {"type": "classification", "num_classes": 4},
    }
    with open(os.path.join(models_dir, "feature_schema.json"), "w") as f:
        json.dump(schema, f, indent=2)

    print(f"[OK] Crowd Model trained! Accuracy: {acc:.2%}, F1: {f1:.2%}")
    print(f"[OK] Model saved to {model_path}")


if __name__ == "__main__":
    train()
