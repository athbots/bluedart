import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../../core/theme/app_theme.dart';
import '../../core/localization/app_localizations.dart';
import '../../data/models/arrival_model.dart';
import '../../data/models/progression_model.dart';
import '../widgets/train_progression_view.dart';
import '../widgets/crowd_badge.dart';

class RouteProgressionScreen extends StatefulWidget {
  final StopArrivalModel arrival;
  final String userStopId;
  final String apiBaseUrl;
  final AppLocalizations l10n;

  const RouteProgressionScreen({
    Key? key,
    required this.arrival,
    required this.userStopId,
    required this.apiBaseUrl,
    required this.l10n,
  }) : super(key: key);

  @override
  State<RouteProgressionScreen> createState() => _RouteProgressionScreenState();
}

class _RouteProgressionScreenState extends State<RouteProgressionScreen> {
  final Dio _dio = Dio();
  RouteProgressionViewModel? _progression;
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _fetchProgression();
  }

  Future<void> _fetchProgression() async {
    try {
      final resp = await _dio.get(
        '${widget.apiBaseUrl}/routes/${widget.arrival.routeId}/progress',
        queryParameters: {
          'vehicle_id': widget.arrival.vehicleId,
          'user_stop_id': widget.userStopId,
        },
      );
      if (resp.statusCode == 200) {
        setState(() {
          _progression = RouteProgressionViewModel.fromJson(resp.data);
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Route ${widget.arrival.routeNumber} Progression'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _fetchProgression),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _progression == null
              ? const Center(child: Text('Progression details unavailable.'))
              : SingleChildScrollView(
                  padding: const EdgeInsets.all(16.0),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      // Bus Status Banner
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          borderRadius: BorderRadius.circular(16),
                          boxShadow: [
                            BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 10, offset: const Offset(0, 4)),
                          ],
                        ),
                        child: Column(
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      '${widget.arrival.routeName}',
                                      style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                                    ),
                                    const SizedBox(height: 2),
                                    Text(
                                      'Vehicle: ${widget.arrival.vehicleId} • Speed: ${_progression!.currentSpeedKmh.round()} km/h',
                                      style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                                    ),
                                  ],
                                ),
                                CrowdBadge(crowdLevel: widget.arrival.currentCrowdLevel),
                              ],
                            ),
                            const Divider(height: 24),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceAround,
                              children: [
                                Column(
                                  children: [
                                    const Text('ETA TO YOUR STOP', style: TextStyle(fontSize: 10, color: Colors.grey)),
                                    const SizedBox(height: 2),
                                    Text(
                                      '${widget.arrival.etaMinutes} min',
                                      style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w900, color: AppTheme.primaryBlue),
                                    ),
                                  ],
                                ),
                                Column(
                                  children: [
                                    const Text('EXPECTED CROWD', style: TextStyle(fontSize: 10, color: Colors.grey)),
                                    const SizedBox(height: 2),
                                    CrowdBadge(crowdLevel: widget.arrival.predictedCrowdAtStop, isCompact: true),
                                  ],
                                ),
                                Column(
                                  children: [
                                    const Text('PREDICTION CONF', style: TextStyle(fontSize: 10, color: Colors.grey)),
                                    const SizedBox(height: 2),
                                    Text(
                                      '${(widget.arrival.predictionConfidence * 100).round()}%',
                                      style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, color: Color(0xFF1E293B)),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(height: 20),

                      // Train-Style Linear Timeline
                      const Text(
                        'LINEAR ROUTE PROGRESSION',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF64748B),
                          letterSpacing: 1.0,
                        ),
                      ),
                      const SizedBox(height: 12),

                      TrainProgressionView(
                        progression: _progression!,
                        l10n: widget.l10n,
                      ),
                    ],
                  ),
                ),
    );
  }
}
