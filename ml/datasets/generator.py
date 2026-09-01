"""
Synthetic Historical Transit Dataset Generator.
Generates realistic historical observations across hours, days of week, route segments,
and stop demand characteristics for training the crowd forecasting and ETA models.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

import random
import json
import csv
from typing import List, Dict, Any

ROUTES = ["ROUTE_201", "ROUTE_415", "ROUTE_102", "ROUTE_207", "ROUTE_505"]
STOPS = [f"STOP_{i:02d}" for i in range(1, 16)]
MAJOR_STOPS = {"STOP_01", "STOP_02", "STOP_03", "STOP_06", "STOP_07", "STOP_10", "STOP_11", "STOP_12", "STOP_13", "STOP_15"}


def generate_training_data(num_samples: int = 5000) -> List[Dict[str, Any]]:
    """
    Generate structured feature samples for model training.
    """
    data = []
    for _ in range(num_samples):
        route_id = random.choice(ROUTES)
        stop_id = random.choice(STOPS)
        hour = random.randint(5, 23)
        day_of_week = random.randint(0, 6)  # 0=Monday, 6=Sunday
        is_weekend = 1 if day_of_week >= 5 else 0
        is_major_stop = 1 if stop_id in MAJOR_STOPS else 0
        direction = random.choice([0, 1])  # 0=OUTBOUND, 1=INBOUND
        stops_away = random.randint(1, 8)
        current_occupancy = random.uniform(0.1, 0.9)

        # Realistic Indian public transit crowd generation function
        is_morning_peak = 1 if (8 <= hour <= 11 and not is_weekend) else 0
        is_evening_peak = 1 if (17 <= hour <= 20 and not is_weekend) else 0
        peak_factor = 0.35 if is_morning_peak else (0.40 if is_evening_peak else 0.0)

        base_occupancy = 0.25 + peak_factor + (0.15 * is_major_stop) + (0.05 * stops_away) - (0.10 * is_weekend)
        noise = random.gauss(0, 0.08)
        target_occupancy = max(0.05, min(0.98, base_occupancy + noise))

        # Categorize
        if target_occupancy <= 0.25:
            crowd_label = "LOW"
            crowd_class = 0
        elif target_occupancy <= 0.55:
            crowd_label = "MEDIUM"
            crowd_class = 1
        elif target_occupancy <= 0.80:
            crowd_label = "HIGH"
            crowd_class = 2
        else:
            crowd_label = "VERY_HIGH"
            crowd_class = 3

        # Travel time target for ETA (seconds for next segment)
        segment_distance_meters = random.uniform(800.0, 2400.0)
        congestion_speed_kmh = 14.0 if (is_morning_peak or is_evening_peak) else 26.0
        speed_mps = (congestion_speed_kmh * 1000.0) / 3600.0 + random.gauss(0, 1.0)
        speed_mps = max(2.5, speed_mps)
        dwell_seconds = random.randint(20, 45) if is_major_stop else random.randint(10, 25)
        travel_time_seconds = (segment_distance_meters / speed_mps) + dwell_seconds

        sample = {
            "route_id": route_id,
            "stop_id": stop_id,
            "hour": hour,
            "day_of_week": day_of_week,
            "is_weekend": is_weekend,
            "is_major_stop": is_major_stop,
            "direction": direction,
            "stops_away": stops_away,
            "current_occupancy": round(current_occupancy, 3),
            "target_occupancy": round(target_occupancy, 3),
            "crowd_label": crowd_label,
            "crowd_class": crowd_class,
            "segment_distance_meters": round(segment_distance_meters, 1),
            "target_travel_time_seconds": round(travel_time_seconds, 1),
        }
        data.append(sample)

    return data


def save_dataset(filepath: str, data: List[Dict[str, Any]]):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=data[0].keys())
        writer.writeheader()
        writer.writerows(data)
    print(f"[OK] Saved {len(data)} training samples to {filepath}")


if __name__ == "__main__":
    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "transit_historical_train.csv"))
    samples = generate_training_data(5000)
    save_dataset(out_path, samples)
