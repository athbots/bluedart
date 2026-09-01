import 'package:flutter/material.dart';
import 'core/theme/app_theme.dart';
import 'presentation/screens/home_screen.dart';

void main() {
  runApp(const SmartTransitPassengerApp());
}

class SmartTransitPassengerApp extends StatelessWidget {
  const SmartTransitPassengerApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Smart Transit India',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      home: const HomeScreen(),
    );
  }
}
