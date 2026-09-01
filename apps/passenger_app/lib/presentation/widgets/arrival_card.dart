import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../core/localization/app_localizations.dart';
import '../../data/models/arrival_model.dart';
import 'crowd_badge.dart';
import 'provenance_tag.dart';

class ArrivalCard extends StatelessWidget {
  final StopArrivalModel arrival;
  final VoidCallback onTap;
  final AppLocalizations l10n;

  const ArrivalCard({
    Key? key,
    required this.arrival,
    required this.onTap,
    required this.l10n,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 2,
      margin: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: BorderSide(
          color: arrival.isFastest
              ? AppTheme.primaryBlue.withOpacity(0.5)
              : (arrival.isMostComfortable ? AppTheme.crowdLow.withOpacity(0.5) : Colors.transparent),
          width: 1.5,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top Row: Decision Badges + Provenance
              Row(
                children: [
                  if (arrival.isFastest)
                    Container(
                      margin: const EdgeInsets.only(right: 6),
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppTheme.primaryBlue,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        l10n.get('fastest'),
                        style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white),
                      ),
                    ),
                  if (arrival.isMostComfortable && !arrival.isFastest)
                    Container(
                      margin: const EdgeInsets.only(right: 6),
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppTheme.crowdLow,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: Text(
                        l10n.get('most_comfortable'),
                        style: const TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.white),
                      ),
                    ),
                  const Spacer(),
                  ProvenanceTag(
                    isLive: arrival.crowdIsLive,
                    isStale: arrival.isStale,
                    source: arrival.crowdSource,
                  ),
                ],
              ),
              const SizedBox(height: 10),

              // Main Row: Route Number, Destination, ETA
              Row(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  // Route Badge
                  Container(
                    width: 58,
                    height: 58,
                    decoration: BoxDecoration(
                      color: AppTheme.accentNavy,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    alignment: Alignment.center,
                    child: Text(
                      arrival.routeNumber,
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                        letterSpacing: 0.5,
                      ),
                    ),
                  ),
                  const SizedBox(width: 14),

                  // Route Name & Current Location
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          arrival.destination,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: Color(0xFF1E293B),
                          ),
                        ),
                        const SizedBox(height: 3),
                        Text(
                          'Near: ${arrival.currentStopName} (${arrival.stopsAway} stops away)',
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            fontSize: 12,
                            color: Colors.grey.shade600,
                          ),
                        ),
                      ],
                    ),
                  ),

                  // ETA Counter
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.end,
                    children: [
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.baseline,
                        textBaseline: TextBaseline.alphabetic,
                        children: [
                          Text(
                            '${arrival.etaMinutes}',
                            style: const TextStyle(
                              fontSize: 26,
                              fontWeight: FontWeight.w900,
                              color: AppTheme.primaryBlue,
                            ),
                          ),
                          const SizedBox(width: 2),
                          Text(
                            l10n.get('minutes_short'),
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.bold,
                              color: Colors.grey.shade700,
                            ),
                          ),
                        ],
                      ),
                      Text(
                        '${(arrival.etaConfidence * 100).toInt()}% conf',
                        style: TextStyle(fontSize: 10, color: Colors.grey.shade500),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 12),
              const Divider(height: 1, color: Color(0xFFE2E8F0)),
              const SizedBox(height: 10),

              // Bottom Row: Current Crowd vs Predicted Crowd at Commuter Stop
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      Text(
                        'Current: ',
                        style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                      ),
                      CrowdBadge(crowdLevel: arrival.currentCrowdLevel, isCompact: true),
                    ],
                  ),
                  Row(
                    children: [
                      Text(
                        'At your stop: ',
                        style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                      ),
                      CrowdBadge(crowdLevel: arrival.predictedCrowdAtStop, isCompact: true),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
