class StopArrivalModel {
  final String vehicleId;
  final String tripId;
  final String routeId;
  final String routeNumber;
  final String routeName;
  final String direction;
  final String destination;
  final double currentLatitude;
  final double currentLongitude;
  final String currentStopName;
  final int stopsAway;
  final double distanceToStopMeters;
  final int etaSeconds;
  final int etaMinutes;
  final double etaConfidence;
  final String etaSource;
  final bool isFastest;
  final bool isMostComfortable;
  final String currentCrowdLevel;
  final double currentOccupancyScore;
  final String crowdSource;
  final bool crowdIsLive;
  final String predictedCrowdAtStop;
  final double predictedOccupancyAtStop;
  final double predictionConfidence;
  final bool isStale;
  final int lastUpdatedSecondsAgo;

  StopArrivalModel({
    required this.vehicleId,
    required this.tripId,
    required this.routeId,
    required this.routeNumber,
    required this.routeName,
    required this.direction,
    required this.destination,
    required this.currentLatitude,
    required this.currentLongitude,
    required this.currentStopName,
    required this.stopsAway,
    required this.distanceToStopMeters,
    required this.etaSeconds,
    required this.etaMinutes,
    required this.etaConfidence,
    required this.etaSource,
    required this.isFastest,
    required this.isMostComfortable,
    required this.currentCrowdLevel,
    required this.currentOccupancyScore,
    required this.crowdSource,
    required this.crowdIsLive,
    required this.predictedCrowdAtStop,
    required this.predictedOccupancyAtStop,
    required this.predictionConfidence,
    required this.isStale,
    required this.lastUpdatedSecondsAgo,
  });

  factory StopArrivalModel.fromJson(Map<String, dynamic> json) {
    return StopArrivalModel(
      vehicleId: json['vehicle_id'] ?? '',
      tripId: json['trip_id'] ?? '',
      routeId: json['route_id'] ?? '',
      routeNumber: json['route_number'] ?? '',
      routeName: json['route_name'] ?? '',
      direction: json['direction'] ?? 'OUTBOUND',
      destination: json['destination'] ?? '',
      currentLatitude: (json['current_latitude'] as num?)?.toDouble() ?? 0.0,
      currentLongitude: (json['current_longitude'] as num?)?.toDouble() ?? 0.0,
      currentStopName: json['current_stop_name'] ?? 'On Route',
      stopsAway: json['stops_away'] ?? 0,
      distanceToStopMeters: (json['distance_to_stop_meters'] as num?)?.toDouble() ?? 0.0,
      etaSeconds: json['eta_seconds'] ?? 0,
      etaMinutes: json['eta_minutes'] ?? 0,
      etaConfidence: (json['eta_confidence'] as num?)?.toDouble() ?? 0.85,
      etaSource: json['eta_source'] ?? 'HYBRID_MODEL',
      isFastest: json['is_fastest'] ?? false,
      isMostComfortable: json['is_most_comfortable'] ?? false,
      currentCrowdLevel: json['current_crowd_level'] ?? 'MEDIUM',
      currentOccupancyScore: (json['current_occupancy_score'] as num?)?.toDouble() ?? 0.5,
      crowdSource: json['crowd_source'] ?? 'EDGE_CAMERA',
      crowdIsLive: json['crowd_is_live'] ?? true,
      predictedCrowdAtStop: json['predicted_crowd_at_stop'] ?? 'MEDIUM',
      predictedOccupancyAtStop: (json['predicted_occupancy_at_stop'] as num?)?.toDouble() ?? 0.5,
      predictionConfidence: (json['prediction_confidence'] as num?)?.toDouble() ?? 0.85,
      isStale: json['is_stale'] ?? false,
      lastUpdatedSecondsAgo: json['last_updated_seconds_ago'] ?? 0,
    );
  }
}
