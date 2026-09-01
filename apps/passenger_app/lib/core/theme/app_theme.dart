import 'package:flutter/material.dart';

class AppTheme {
  static const Color primaryBlue = Color(0xFF0F52BA);
  static const Color accentNavy = Color(0xFF081C3B);
  static const Color backgroundLight = Color(0xFFF6F8FC);
  static const Color surfaceWhite = Color(0xFFFFFFFF);

  // Crowd Palette (Accessible with text labels & contrast)
  static const Color crowdLow = Color(0xFF10B981);       // Emerald Green
  static const Color crowdMedium = Color(0xFFF59E0B);    // Amber
  static const Color crowdHigh = Color(0xFFEF4444);      // Red
  static const Color crowdVeryHigh = Color(0xFF991B1B);  // Crimson Dark Red

  static const Color badgeLive = Color(0xFF0284C7);      // Sky blue
  static const Color badgePredicted = Color(0xFF8B5CF6); // Purple

  static ThemeData get lightTheme {
    return ThemeData(
      useMaterial3: true,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryBlue,
        primary: primaryBlue,
        background: backgroundLight,
        surface: surfaceWhite,
      ),
      scaffoldBackgroundColor: backgroundLight,
      appBarTheme: const AppBarTheme(
        backgroundColor: accentNavy,
        foregroundColor: Colors.white,
        elevation: 0,
        centerTitle: false,
      ),
      cardTheme: CardTheme(
        color: surfaceWhite,
        elevation: 1.5,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        margin: const EdgeInsets.symmetric(vertical: 8, horizontal: 16),
      ),
    );
  }
}
