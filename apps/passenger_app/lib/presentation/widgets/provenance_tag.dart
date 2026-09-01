import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

class ProvenanceTag extends StatelessWidget {
  final bool isLive;
  final bool isStale;
  final String source;

  const ProvenanceTag({
    Key? key,
    required this.isLive,
    required this.isStale,
    required this.source,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    if (isStale) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: Colors.orange.shade100,
          borderRadius: BorderRadius.circular(6),
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.history_toggle_off, size: 12, color: Colors.deepOrange),
            SizedBox(width: 4),
            Text(
              'DATA DELAYED',
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: Colors.deepOrange),
            ),
          ],
        ),
      );
    }

    if (isLive) {
      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
        decoration: BoxDecoration(
          color: AppTheme.badgeLive.withOpacity(0.15),
          borderRadius: BorderRadius.circular(6),
        ),
        child: const Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.sensors, size: 12, color: AppTheme.badgeLive),
            SizedBox(width: 4),
            Text(
              'LIVE',
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.badgeLive),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: AppTheme.badgePredicted.withOpacity(0.15),
        borderRadius: BorderRadius.circular(6),
      ),
      child: const Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.auto_awesome, size: 12, color: AppTheme.badgePredicted),
          SizedBox(width: 4),
          Text(
            'PREDICTED',
            style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: AppTheme.badgePredicted),
          ),
        ],
      ),
    );
  }
}
