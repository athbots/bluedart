import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import '../../core/theme/app_theme.dart';
import '../../core/localization/app_localizations.dart';
import '../../data/models/arrival_model.dart';
import '../widgets/arrival_card.dart';
import 'route_progression_screen.dart';

class HomeScreen extends StatefulWidget {
  final String apiBaseUrl;

  const HomeScreen({Key? key, this.apiBaseUrl = 'http://localhost:8000/api/v1'}) : super(key: key);

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final Dio _dio = Dio();
  String _language = 'en';
  late AppLocalizations _l10n;

  // Selected commuter stop (defaults to Raj Nagar District Centre)
  String _selectedStopId = 'STOP_13';
  String _selectedStopName = 'Raj Nagar District Centre (RDC)';
  int _distanceMeters = 185;

  List<StopArrivalModel> _arrivals = [];
  bool _isLoading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _l10n = AppLocalizations(_language);
    _fetchArrivals();
  }

  void _toggleLanguage() {
    setState(() {
      _language = _language == 'en' ? 'hi' : 'en';
      _l10n = AppLocalizations(_language);
    });
  }

  Future<void> _fetchArrivals() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final resp = await _dio.get('${widget.apiBaseUrl}/stops/$_selectedStopId/arrivals');
      if (resp.statusCode == 200) {
        final data = resp.data;
        final rawArrivals = (data['arrivals'] as List<dynamic>?) ?? [];
        setState(() {
          _arrivals = rawArrivals.map((a) => StopArrivalModel.fromJson(a)).toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _errorMessage = 'Could not load live arrivals. Check backend connectivity.';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _l10n.get('app_title'),
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            Text(
              _l10n.get('tagline'),
              style: const TextStyle(fontSize: 11, color: Colors.white70),
            ),
          ],
        ),
        actions: [
          TextButton.icon(
            onPressed: _toggleLanguage,
            icon: const Icon(Icons.translate, color: Colors.amber, size: 18),
            label: Text(
              _language == 'en' ? 'हिंदी' : 'English',
              style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _fetchArrivals,
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _fetchArrivals,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Nearest Bus Stop Banner
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(20),
                decoration: const BoxDecoration(
                  color: AppTheme.accentNavy,
                  borderRadius: BorderRadius.only(
                    bottomLeft: Radius.circular(24),
                    bottomRight: Radius.circular(24),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        const Icon(Icons.near_me, color: Colors.amber, size: 16),
                        const SizedBox(width: 6),
                        Text(
                          _l10n.get('nearest_stop').toUpperCase(),
                          style: const TextStyle(
                            color: Colors.white70,
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            letterSpacing: 1.0,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _selectedStopName,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 22,
                        fontWeight: FontWeight.w900,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '$_distanceMeters m away • Ghaziabad Transit Hub',
                      style: const TextStyle(color: Colors.white60, fontSize: 13),
                    ),
                  ],
                ),
              ),

              const SizedBox(height: 16),

              // Section Title: Coming to your stop
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 20),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _l10n.get('arriving_buses'),
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF0F172A),
                      ),
                    ),
                    if (_arrivals.isNotEmpty)
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: AppTheme.primaryBlue.withOpacity(0.1),
                          borderRadius: BorderRadius.circular(12),
                        ),
                        child: Text(
                          '${_arrivals.length} buses live',
                          style: const TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.bold,
                            color: AppTheme.primaryBlue,
                          ),
                        ),
                      ),
                  ],
                ),
              ),

              const SizedBox(height: 8),

              // Loading & Error States
              if (_isLoading)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(40.0),
                    child: CircularProgressIndicator(),
                  ),
                )
              else if (_errorMessage != null)
                Padding(
                  padding: const EdgeInsets.all(24.0),
                  child: Center(
                    child: Column(
                      children: [
                        const Icon(Icons.wifi_off, size: 48, color: Colors.orange),
                        const SizedBox(height: 12),
                        Text(_errorMessage!, textAlign: TextAlign.center),
                        const SizedBox(height: 12),
                        ElevatedButton(
                          onPressed: _fetchArrivals,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                )
              else if (_arrivals.isEmpty)
                const Padding(
                  padding: EdgeInsets.all(32.0),
                  child: Center(
                    child: Text('No active buses approaching this stop at this moment.'),
                  ),
                )
              else
                ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: _arrivals.length,
                  itemBuilder: (context, index) {
                    final arrival = _arrivals[index];
                    return ArrivalCard(
                      arrival: arrival,
                      l10n: _l10n,
                      onTap: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => RouteProgressionScreen(
                              arrival: arrival,
                              userStopId: _selectedStopId,
                              apiBaseUrl: widget.apiBaseUrl,
                              l10n: _l10n,
                            ),
                          ),
                        );
                      },
                    );
                  },
                ),
            ],
          ),
        ),
      ),
    );
  }
}
