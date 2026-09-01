import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';
import '../../core/localization/app_localizations.dart';
import '../../data/models/progression_model.dart';
import 'crowd_badge.dart';

class TrainProgressionView extends StatelessWidget {
  final RouteProgressionViewModel progression;
  final AppLocalizations l10n;

  const TrainProgressionView({
    Key? key,
    required this.progression,
    required this.l10n,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: progression.stops.length,
      itemBuilder: (context, index) {
        final stop = progression.stops[index];
        final isFirst = index == 0;
        final isLast = index == progression.stops.length - 1;

        return Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Left Column: Linear Track with Connectors and Icons
            SizedBox(
              width: 54,
              child: Column(
                children: [
                  // Upper connector line
                  Container(
                    width: 4,
                    height: 24,
                    color: isFirst
                        ? Colors.transparent
                        : (stop.isPassed ? AppTheme.primaryBlue : Colors.grey.shade300),
                  ),

                  // Node Circle / Pin
                  if (stop.isCurrent)
                    Container(
                      width: 32,
                      height: 32,
                      decoration: const BoxDecoration(
                        color: AppTheme.primaryBlue,
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(color: Color(0x660F52BA), blurRadius: 8, spreadRadius: 2),
                        ],
                      ),
                      child: const Icon(Icons.directions_bus, size: 18, color: Colors.white),
                    )
                  else if (stop.isUserStop)
                    Container(
                      width: 28,
                      height: 28,
                      decoration: const BoxDecoration(
                        color: Colors.amber,
                        shape: BoxShape.circle,
                        boxShadow: [
                          BoxShadow(color: Color(0x66F59E0B), blurRadius: 6, spreadRadius: 1),
                        ],
                      ),
                      child: const Icon(Icons.person_pin_circle, size: 18, color: Colors.black87),
                    )
                  else if (stop.isPassed)
                    Container(
                      width: 18,
                      height: 18,
                      decoration: BoxDecoration(
                        color: AppTheme.primaryBlue.withOpacity(0.4),
                        shape: BoxShape.circle,
                      ),
                      child: const Icon(Icons.check, size: 12, color: Colors.white),
                    )
                  else
                    Container(
                      width: 16,
                      height: 16,
                      decoration: BoxDecoration(
                        color: Colors.white,
                        shape: BoxShape.circle,
                        border: Border.all(
                          color: stop.isMajorStop ? AppTheme.accentNavy : Colors.grey.shade400,
                          width: stop.isMajorStop ? 3 : 2,
                        ),
                      ),
                    ),

                  // Lower connector line
                  Container(
                    width: 4,
                    height: 24,
                    color: isLast
                        ? Colors.transparent
                        : (stop.isPassed ? AppTheme.primaryBlue : Colors.grey.shade300),
                  ),
                ],
              ),
            ),

            // Right Column: Stop Name, ETA, and Major Tag
            Expanded(
              child: Container(
                margin: const EdgeInsets.only(bottom: 12, top: 14),
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: stop.isUserStop
                      ? Colors.amber.shade50
                      : (stop.isCurrent ? const Color(0xFFEFF6FF) : Colors.white),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: stop.isUserStop
                        ? Colors.amber.shade400
                        : (stop.isCurrent ? AppTheme.primaryBlue.withOpacity(0.4) : Colors.grey.shade200),
                    width: (stop.isUserStop || stop.isCurrent) ? 1.5 : 1.0,
                  ),
                ),
                child: Row(
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Text(
                                stop.stopName,
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: (stop.isUserStop || stop.isCurrent || stop.isMajorStop)
                                      ? FontWeight.bold
                                      : FontWeight.w500,
                                  color: stop.isPassed ? Colors.grey.shade500 : const Color(0xFF0F172A),
                                ),
                              ),
                              if (stop.isMajorStop) ...[
                                const SizedBox(width: 6),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: Colors.blueGrey.shade100,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: const Text('HUB', style: TextStyle(fontSize: 9, fontWeight: FontWeight.bold)),
                                ),
                              ],
                            ],
                          ),
                          if (stop.isUserStop)
                            Text(
                              l10n.get('user_stop'),
                              style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: Colors.amber,
                              ),
                            ),
                        ],
                      ),
                    ),
                    if (stop.estimatedArrivalSeconds != null && !stop.isPassed)
                      Text(
                        '~${(stop.estimatedArrivalSeconds! / 60).round()} min',
                        style: const TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: AppTheme.primaryBlue,
                        ),
                      ),
                  ],
                ),
              ),
            ),
          ],
        );
      },
    );
  }
}
