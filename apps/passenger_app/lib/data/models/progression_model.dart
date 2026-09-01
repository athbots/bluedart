class RouteProgressionNodeModel {
  final String stopId;
  final String stopName;
  final String displayName;
  final int sequence;
  final double cumulativeDistanceMeters;
  final String stopType;
  final bool isMajorStop;
  final bool isInterchangeStop;
  final bool isTerminalStop;
  final bool isDepot;
  final bool isPassed;
  final bool isCurrent;
  final bool isNext;
  final bool isUserStop;
  final double? distanceFromBusMeters;
  final int? estimatedArrivalSeconds;
  final String? predictedCrowdLevel;
  final double? crowdConfidence;

  RouteProgressionNodeModel({
    required this.stopId,
    required this.stopName,
    required this.displayName,
    required this.sequence,
    required this.cumulativeDistanceMeters,
    required this.stopType,
    required this.isMajorStop,
    required this.isInterchangeStop,
    required this.isTerminalStop,
    required this.isDepot,
    required this.isPassed,
    required this.isCurrent,
    required this.isNext,
    required this.isUserStop,
    this.distanceFromBusMeters,
    this.estimatedArrivalSeconds,
    this.predictedCrowdLevel,
    this.crowdConfidence,
  });

  factory RouteProgressionNodeModel.fromJson(Map<String, dynamic> json) {
    return RouteProgressionNodeModel(
      stopId: json['stop_id'] ?? '',
      stopName: json['stop_name'] ?? '',
      displayName: json['display_name'] ?? json['stop_name'] ?? '',
      sequence: json['sequence'] ?? 0,
      cumulativeDistanceMeters: (json['cumulative_distance_meters'] as num?)?.toDouble() ?? 0.0,
      stopType: json['stop_type'] ?? 'LOCAL',
      isMajorStop: json['is_major_stop'] ?? false,
      isInterchangeStop: json['is_interchange_stop'] ?? false,
      isTerminalStop: json['is_terminal_stop'] ?? false,
      isDepot: json['is_depot'] ?? false,
      isPassed: json['is_passed'] ?? false,
      isCurrent: json['is_current'] ?? false,
      isNext: json['is_next'] ?? false,
      isUserStop: json['is_user_stop'] ?? false,
      distanceFromBusMeters: (json['distance_from_bus_meters'] as num?)?.toDouble(),
      estimatedArrivalSeconds: json['estimated_arrival_seconds'],
      predictedCrowdLevel: json['predicted_crowd_level'],
      crowdConfidence: (json['crowd_confidence'] as num?)?.toDouble(),
    );
  }
}

class RouteProgressionViewModel {
  final String vehicleId;
  final String registrationNumber;
  final String routeId;
  final String routeNumber;
  final String routeName;
  final String direction;
  final String origin;
  final String destination;
  final double currentSpeedKmh;
  final double routeProgressPercentage;
  final int stopsPassedCount;
  final int totalStopsCount;
  final String currentStopName;
  final String nextMajorStopName;
  final List<RouteProgressionNodeModel> stops;
  final String? userStopId;
  final String? userStopName;
  final int? etaToUserStopSeconds;
  final String? crowdAtUserStop;
  final bool demoCorridor;

  RouteProgressionViewModel({
    required this.vehicleId,
    required this.registrationNumber,
    required this.routeId,
    required this.routeNumber,
    required this.routeName,
    required this.direction,
    required this.origin,
    required this.destination,
    required this.currentSpeedKmh,
    required this.routeProgressPercentage,
    required this.stopsPassedCount,
    required this.totalStopsCount,
    required this.currentStopName,
    required this.nextMajorStopName,
    required this.stops,
    this.userStopId,
    this.userStopName,
    this.etaToUserStopSeconds,
    this.crowdAtUserStop,
    this.demoCorridor = true,
  });

  factory RouteProgressionViewModel.fromJson(Map<String, dynamic> json) {
    var rawStops = (json['stops'] as List<dynamic>?) ?? [];
    var stopsList = rawStops.map((s) => RouteProgressionNodeModel.fromJson(s)).toList();

    return RouteProgressionViewModel(
      vehicleId: json['vehicle_id'] ?? '',
      registrationNumber: json['registration_number'] ?? json['vehicle_id'] ?? '',
      routeId: json['route_id'] ?? '',
      routeNumber: json['route_number'] ?? '',
      routeName: json['route_name'] ?? '',
      direction: json['direction'] ?? 'OUTBOUND',
      origin: json['origin'] ?? '',
      destination: json['destination'] ?? '',
      currentSpeedKmh: (json['current_speed_kmh'] as num?)?.toDouble() ?? 0.0,
      routeProgressPercentage: (json['route_progress_percentage'] as num?)?.toDouble() ?? 0.0,
      stopsPassedCount: json['stops_passed_count'] ?? 0,
      totalStopsCount: json['total_stops_count'] ?? stopsList.length,
      currentStopName: json['current_stop_name'] ?? '',
      nextMajorStopName: json['next_major_stop_name'] ?? '',
      stops: stopsList,
      userStopId: json['user_stop_id'],
      userStopName: json['user_stop_name'],
      etaToUserStopSeconds: json['eta_to_user_stop_seconds'],
      crowdAtUserStop: json['crowd_at_user_stop'],
      demoCorridor: json['demo_corridor'] ?? true,
    );
  }
}
