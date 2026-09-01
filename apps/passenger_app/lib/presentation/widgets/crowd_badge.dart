import 'package:flutter/material.dart';
import '../../core/theme/app_theme.dart';

class CrowdBadge extends StatelessWidget {
  final String crowdLevel;
  final bool isCompact;

  const CrowdBadge({
    Key? key,
    required this.crowdLevel,
    this.isCompact = false,
  }) : super(key: key);

  Color _getColor() {
    switch (crowdLevel.toUpperCase()) {
      case 'LOW':
        return AppTheme.crowdLow;
      case 'MEDIUM':
        return AppTheme.crowdMedium;
      case 'HIGH':
        return AppTheme.crowdHigh;
      case 'VERY_HIGH':
        return AppTheme.crowdVeryHigh;
      default:
        return Colors.grey;
    }
  }

  IconData _getIcon() {
    switch (crowdLevel.toUpperCase()) {
      case 'LOW':
        return Icons.people_outline;
      case 'MEDIUM':
        return Icons.people;
      case 'HIGH':
      case 'VERY_HIGH':
        return Icons.groups;
      default:
        return Icons.person_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    final color = _getColor();
    final icon = _getIcon();

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isCompact ? 8 : 12,
        vertical: isCompact ? 4 : 6,
      ),
      decoration: BoxDecoration(
        color: color.withOpacity(0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withOpacity(0.35), width: 1.2),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: isCompact ? 14 : 16, color: color),
          const SizedBox(width: 4),
          Text(
            crowdLevel.replaceAll('_', ' '),
            style: TextStyle(
              color: color,
              fontSize: isCompact ? 11 : 13,
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
