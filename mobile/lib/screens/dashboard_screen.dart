import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';
import '../config/env_config.dart';
import '../services/tts_service.dart';
import 'trace_panel_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  List<dynamic> incidents = [];
  Map<String, dynamic>? systemState;
  Timer? _pollingTimer;
  Timer? _secondsTimer;
  int secondsSinceUpdate = 0;
  bool isPolling = false;

  final ScrollController _tickerScrollController = ScrollController();
  Timer? _tickerTimer;

  @override
  void initState() {
    super.initState();
    _fetchData();
    _startPolling();
    _startTickerAutoScroll();
  }

  @override
  void dispose() {
    _pollingTimer?.cancel();
    _secondsTimer?.cancel();
    _tickerTimer?.cancel();
    _tickerScrollController.dispose();
    super.dispose();
  }

  void _startPolling() {
    _pollingTimer = Timer.periodic(const Duration(seconds: 10), (timer) {
      _fetchData();
    });
    
    _secondsTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (mounted) {
        setState(() {
          secondsSinceUpdate++;
        });
      }
    });
  }

  void _startTickerAutoScroll() {
    _tickerTimer = Timer.periodic(const Duration(milliseconds: 50), (timer) {
      if (_tickerScrollController.hasClients) {
        final maxScroll = _tickerScrollController.position.maxScrollExtent;
        final currentScroll = _tickerScrollController.offset;
        if (currentScroll >= maxScroll) {
          _tickerScrollController.jumpTo(0);
        } else {
          _tickerScrollController.jumpTo(currentScroll + 1);
        }
      }
    });
  }

  Future<void> _fetchData() async {
    if (isPolling) return;
    isPolling = true;
    try {
      final incidentsRes = await http.get(Uri.parse('${EnvConfig.backendUrl}/api/incidents'));
      final stateRes = await http.get(Uri.parse('${EnvConfig.backendUrl}/api/system-state'));

      if (incidentsRes.statusCode == 200 && stateRes.statusCode == 200) {
        if (mounted) {
          setState(() {
            incidents = json.decode(incidentsRes.body)['incidents'];
            systemState = json.decode(stateRes.body);
            secondsSinceUpdate = 0;
          });
        }
      }
    } catch (e) {
      debugPrint("Error fetching data: $e");
    } finally {
      isPolling = false;
    }
  }

  Future<void> _injectDemoSignal(Map<String, dynamic> payload) async {
    try {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Injecting signal...")));
      final res = await http.post(
        Uri.parse('${EnvConfig.backendUrl}/api/inject-signal'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode(payload)
      );
      if (res.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text("Signal injected successfully!")));
        _fetchData();
      }
    } catch (e) {
      debugPrint("Error injecting signal: $e");
    }
  }

  void _showDemoInjectBottomSheet() {
    showModalBottomSheet(
      context: context,
      builder: (context) {
        return SafeArea(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const ListTile(
                title: Text("Demo Scenarios", style: TextStyle(fontWeight: FontWeight.bold)),
              ),
              ListTile(
                leading: const Icon(Icons.water_drop),
                title: const Text("Scenario A: G-10 Urban Flooding"),
                onTap: () {
                  Navigator.pop(context);
                  _injectDemoSignal({
                    "social_posts": [
                      "G-10 mein pani bhar gaya hai gaariyan phans gayi hain",
                      "Flooding on main road near G-10 markaz serious situation",
                      "Been stuck in G-10 for 45 mins water level rising"
                    ],
                    "weather": {"rainfall_mmhr": 42.0, "humidity": 94.0, "temperature_c": 28.0},
                    "traffic": {"G10": 87, "G9": 23, "G11": 31},
                    "location": "G-10 Markaz, Islamabad",
                    "lat": 33.6844,
                    "lng": 73.0479
                  });
                },
              ),
              ListTile(
                leading: const Icon(Icons.wb_sunny),
                title: const Text("Scenario B: G-9 Heatwave"),
                onTap: () {
                  Navigator.pop(context);
                  _injectDemoSignal({
                    "social_posts": [
                      "Elderly uncle collapsed in G-9 sector due to heat",
                      "Heat index touching 48 degrees in G-9 today unbearable"
                    ],
                    "weather": {"rainfall_mmhr": 0.0, "humidity": 15.0, "temperature_c": 47.0},
                    "traffic": {"G10": 22, "G9": 45, "G11": 19},
                    "location": "G-9 Sector, Islamabad",
                    "lat": 33.6938,
                    "lng": 73.0551
                  });
                },
              ),
              ListTile(
                leading: const Icon(Icons.warning),
                title: const Text("Scenario C: False Alarm (Water Main)"),
                onTap: () {
                  Navigator.pop(context);
                  _injectDemoSignal({
                    "social_posts": [
                      "Water everywhere on street 5 G-10 looks like flooding",
                      "Actually its a burst pipe not rain water KWSB please fix",
                      "Field team confirmed water main burst not flood G-10"
                    ],
                    "weather": {"rainfall_mmhr": 4.0, "humidity": 55.0, "temperature_c": 32.0},
                    "traffic": {"G10": 41, "G9": 20, "G11": 18},
                    "location": "Street 5, G-10, Islamabad",
                    "lat": 33.6844,
                    "lng": 73.0479
                  });
                },
              ),
            ],
          ),
        );
      }
    );
  }

  void _showIncidentDetailSheet(Map<String, dynamic> incident, Color sevColor, bool isRetracted) {
    double lat = incident['lat'] ?? (incident['location'] != null && incident['location'].toString().contains('G-9') ? 33.6938 : 33.6844);
    double lng = incident['lng'] ?? (incident['location'] != null && incident['location'].toString().contains('G-9') ? 73.0551 : 73.0479);

    final mapUrl = "https://maps.googleapis.com/maps/api/staticmap?center=$lat,$lng&zoom=15&size=600x300&markers=color:red|label:!|$lat,$lng&style=feature:all|element:geometry|color:0x1d2c4d&style=feature:water|element:geometry|color:0x0e1626&key=${EnvConfig.mapsKey}";

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) {
        return Container(
          height: MediaQuery.of(context).size.height * 0.85,
          decoration: const BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.only(topLeft: Radius.circular(24), topRight: Radius.circular(24)),
          ),
          child: Column(
            children: [
              ClipRRect(
                borderRadius: const BorderRadius.only(topLeft: Radius.circular(24), topRight: Radius.circular(24)),
                child: Image.network(
                  mapUrl,
                  height: 250,
                  width: double.infinity,
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) => Container(
                    height: 250,
                    color: Colors.grey.shade800,
                    alignment: Alignment.center,
                    child: const Text("Map Preview Unavailable", style: TextStyle(color: Colors.white)),
                  ),
                ),
              ),
              Expanded(
                child: ListView(
                  padding: const EdgeInsets.all(24.0),
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Expanded(
                          child: Text(
                            '${incident['crisis_type']} ${isRetracted ? "(Retracted)" : ""}',
                            style: TextStyle(
                              fontSize: 24, 
                              fontWeight: FontWeight.bold,
                              decoration: isRetracted ? TextDecoration.lineThrough : null
                            ),
                          ),
                        ),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          decoration: BoxDecoration(
                            color: isRetracted ? Colors.grey : sevColor,
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Text(
                            'Severity ${incident['severity']}',
                            style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                          ),
                        )
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text('Location: ${incident['location'] ?? "Unknown"}', style: const TextStyle(fontSize: 16, color: Colors.black54)),
                    const SizedBox(height: 16),
                    Row(
                      children: [
                        const Icon(Icons.people, color: Colors.blueGrey),
                        const SizedBox(width: 8),
                        Text('Affected Population: ${incident['affected_population']}'),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Row(
                      children: [
                        const Icon(Icons.analytics, color: Colors.blueGrey),
                        const SizedBox(width: 8),
                        Text('Confidence: ${((incident['confidence'] ?? 0) * 100).toInt()}%'),
                      ],
                    ),
                    const SizedBox(height: 24),
                    const Text('Actions Taken', style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
                    const SizedBox(height: 8),
                    if (incident['actions_executed'] != null && !isRetracted)
                      ...((incident['actions_executed'] as List).map((action) => ListTile(
                        contentPadding: EdgeInsets.zero,
                        leading: const Icon(Icons.check_circle, color: Colors.green),
                        title: Text(action['action_type'].toString().replaceAll('_', ' ').toUpperCase()),
                        subtitle: Text(action['parameters'].toString()),
                      )).toList())
                    else
                      const Text("No actions executed or incident retracted."),
                    const SizedBox(height: 32),
                    ElevatedButton.icon(
                      onPressed: () {
                        TTSService.speakIncidentAlert(incident);
                      },
                      icon: const Icon(Icons.volume_up),
                      label: const Text("Speak Alert"),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                    ),
                    const SizedBox(height: 16),
                    OutlinedButton.icon(
                      onPressed: () {
                        Navigator.pop(context);
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => TracePanelScreen(incidentId: incident['incident_id']),
                          ),
                        );
                      },
                      icon: const Icon(Icons.code),
                      label: const Text("View Agent Trace"),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      }
    );
  }

  Color _getSeverityColor(int severity) {
    if (severity >= 5) return Colors.red;
    if (severity == 4) return Colors.orange;
    if (severity == 3) return Colors.yellow.shade800;
    return Colors.green;
  }

  Widget _buildTicker() {
    List<String> recentActions = [];
    if (systemState != null && systemState!['recent_actions'] != null) {
      recentActions = List<String>.from(systemState!['recent_actions']);
    }

    if (recentActions.isEmpty) {
      recentActions = ["System ready. Awaiting autonomous loop data...", "Agents standing by for active monitoring."];
    }

    return Container(
      height: 40,
      color: Colors.black87,
      child: ListView.builder(
        controller: _tickerScrollController,
        scrollDirection: Axis.horizontal,
        physics: const NeverScrollableScrollPhysics(),
        itemCount: 1000, // Infinite scroll simulation
        itemBuilder: (context, index) {
          final action = recentActions[index % recentActions.length];
          return Padding(
            padding: const EdgeInsets.symmetric(horizontal: 24.0, vertical: 10.0),
            child: Row(
              children: [
                const Icon(Icons.circle, color: Colors.greenAccent, size: 8),
                const SizedBox(width: 8),
                Text(
                  action,
                  style: const TextStyle(color: Colors.greenAccent, fontFamily: 'monospace', fontSize: 13),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            const Text('Active Incidents'),
            const Spacer(),
            Container(
              width: 12,
              height: 12,
              decoration: const BoxDecoration(
                color: Colors.greenAccent,
                shape: BoxShape.circle,
                boxShadow: [BoxShadow(color: Colors.greenAccent, blurRadius: 4)]
              ),
            ),
            const SizedBox(width: 8),
            const Text("Autonomous mode", style: TextStyle(fontSize: 12)),
          ],
        ),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: Column(
        children: [
          _buildTicker(),
          Padding(
            padding: const EdgeInsets.all(8.0),
            child: Text("Last updated $secondsSinceUpdate seconds ago", style: const TextStyle(color: Colors.grey)),
          ),
          if (systemState != null)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16.0),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                children: [
                  _StatBadge(label: "Active", value: systemState!['active_incidents'].toString()),
                  _StatBadge(label: "Affected", value: systemState!['total_affected'].toString()),
                  _StatBadge(label: "Deployed", value: systemState!['resources_deployed'].toString()),
                ],
              ),
            ),
          Expanded(
            child: incidents.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : ListView.builder(
                    padding: const EdgeInsets.all(16),
                    itemCount: incidents.length,
                    itemBuilder: (context, index) {
                      final incident = incidents[index];
                      final sevColor = _getSeverityColor(incident['severity'] ?? 1);
                      final isRetracted = incident['status'] == 'retracted';
                      return AnimatedContainer(
                        duration: const Duration(milliseconds: 500),
                        child: Card(
                          elevation: 4,
                          margin: const EdgeInsets.only(bottom: 16),
                          color: isRetracted ? Colors.grey.shade200 : Colors.white,
                          child: InkWell(
                            onTap: () {
                              _showIncidentDetailSheet(incident, sevColor, isRetracted);
                            },
                            child: Padding(
                              padding: const EdgeInsets.all(16.0),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                                    children: [
                                      Expanded(
                                        child: Text(
                                          '${incident['crisis_type']} ${isRetracted ? "(Retracted)" : ""}',
                                          style: TextStyle(
                                            fontSize: 18, 
                                            fontWeight: FontWeight.bold,
                                            decoration: isRetracted ? TextDecoration.lineThrough : null
                                          ),
                                        ),
                                      ),
                                      Container(
                                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                        decoration: BoxDecoration(
                                          color: isRetracted ? Colors.grey : sevColor,
                                          borderRadius: BorderRadius.circular(16),
                                        ),
                                        child: Text(
                                          'Severity ${incident['severity']}',
                                          style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                                        ),
                                      )
                                    ],
                                  ),
                                  const SizedBox(height: 12),
                                  Text('Location: ${incident['location'] ?? "Unknown"}'),
                                  Text('Affected Population: ${incident['affected_population']}'),
                                  Text('Confidence: ${((incident['confidence'] ?? 0) * 100).toInt()}%'),
                                ],
                              ),
                            ),
                          ),
                        ),
                      );
                    },
                  ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _showDemoInjectBottomSheet,
        label: const Text("Demo Inject"),
        icon: const Icon(Icons.bolt),
      ),
    );
  }
}

class _StatBadge extends StatelessWidget {
  final String label;
  final String value;
  const _StatBadge({required this.label, required this.value});

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
        Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
      ],
    );
  }
}
