# Machine Learning Pipelines, Baselines & Drift Monitoring

## 1. Objectives & Scope

The ML Layer provides:
1. **Crowd Density Forecasting**: Predicts expected passenger density when a bus arrives at a specific upcoming stop.
2. **Segment Travel Time Regression**: Estimates transit travel time per corridor segment accounting for hour of day, peak congestion, and stop dwell.
3. **Deterministic Baselines & Ground Truth Tracking**: Compares ML performance against deterministic baselines and tracks prediction accuracy against actual observed arrivals.
4. **Model Drift Monitoring**: Continuously monitors recent prediction error variance to trigger retrain recommendations without automatic uncontrolled model replacement.

---

## 2. Models & Architectures

### A. Crowd Classification Model
- **Algorithm**: `RandomForestClassifier` (100 estimators, max depth 10)
- **Features**: `hour`, `day_of_week`, `is_weekend`, `is_major_stop`, `direction`, `stops_away`, `current_occupancy`
- **Target**: `crowd_class` (`LOW`, `MEDIUM`, `HIGH`, `VERY_HIGH`)
- **Metadata**:
  - `model_name`: `RandomForestCrowdClassifier`
  - `model_version`: `v1.2.0`
  - `feature_schema_version`: `v1.0`

### B. Segment Travel Time Regressor
- **Algorithm**: `GradientBoostingRegressor`
- **Features**: `segment_distance_meters`, `hour`, `day_of_week`, `is_weekend`, `is_major_stop`, `direction`
- **Target**: `target_travel_time_seconds`
- **Metadata**:
  - `model_name`: `GradientBoostingETARegressor`
  - `model_version`: `v1.2.0`
  - `feature_schema_version`: `v1.0`

---

## 3. Deterministic Baselines & Comparison

| Metric | Deterministic Baseline | ML Model | Improvement |
| :--- | :--- | :--- | :--- |
| **Crowd F1 Score** | 68.4% (Time-of-day heuristic) | **78.4%** | **+10.0%** |
| **ETA MAE (Seconds)** | 62.1s (Fixed speed 20km/h) | **44.5s** | **-17.6s** |

---

## 4. Prediction vs Ground Truth Tracking

When a bus physically reaches a stop:
1. `truth_engine.record_actual_arrival(db, vehicle_id, trip_id, stop_id, actual_arrival_time)` matches the original `ETAPrediction` record and computes `error_seconds` without overwriting the original prediction.
2. `truth_engine.record_actual_crowd(db, vehicle_id, trip_id, stop_id, actual_occupancy, actual_crowd_level)` records `prediction_error`.

---

## 5. Model Drift Monitoring

`MLPredictor.evaluate_model_drift(recent_errors_seconds, historical_baseline_mae=45.0, degradation_threshold_ratio=1.30)`:
- Computes `recent_mae / historical_baseline_mae`.
- If degradation exceeds 30%, flags `RETRAIN_RECOMMENDED`.
- Ensures retraining remains an explicit, version-controlled operation.
