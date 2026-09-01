export interface LiveBus {
  vehicle_id: string;
  registration_number: string;
  fleet_number: string;
  vehicle_type: string;
  route_id?: string;
  route_number?: string;
  route_name?: string;
  direction: string;
  latitude: number;
  longitude: number;
  speed_kmh: number;
  heading: number;
  current_stop_index: number;
  current_stop_name?: string;
  next_stop_name?: string;
  route_progress_percentage: number;
  crowd_level: string;
  occupancy_score: number;
  crowd_confidence: number;
  crowd_source: string;
  location_source?: string;
  device_timestamp?: string;
  server_received_timestamp?: string;
  is_live: boolean;
  is_stale: boolean;
  age_seconds: number;
}

export interface DeviceInfo {
  id: string;
  vehicle_id?: string;
  device_type: string;
  serial_number: string;
  firmware_version: string;
  software_version: string;
  status: string;
  last_seen?: string;
  cpu_temperature?: number;
  memory_usage?: number;
  storage_usage?: number;
  network_status?: string;
  camera_status?: string;
  gps_status?: string;
  uptime?: number;
}

export interface CrowdAnalyticsData {
  hourly_trends: Array<{ hour: number; occupancy: number; level: string }>;
  routes_analytics: Array<{ route_number: string; name: string; avg_occupancy: number; high_crowd_trips: number }>;
  peak_morning_window: string;
  peak_evening_window: string;
  high_demand_corridor: string;
}

export interface ETAAnalyticsData {
  mean_absolute_error_seconds: number;
  root_mean_squared_error_seconds: number;
  mean_absolute_percentage_error: number;
  accuracy_within_2_min_pct: number;
  accuracy_within_5_min_pct: number;
  sample_comparisons: Array<{
    trip: string;
    stop: string;
    predicted_eta_min: number;
    actual_min: number;
    error_sec: number;
  }>;
}
