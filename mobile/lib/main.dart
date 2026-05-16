import 'package:flutter/material.dart';
import 'screens/home_screen.dart';
import 'config/env_config.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await EnvConfig.init();
  runApp(const CiroApp());
}

class CiroApp extends StatelessWidget {
  const CiroApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'CIRO Mobile',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blueGrey),
        useMaterial3: true,
      ),
      home: const HomeScreen(),
    );
  }
}
