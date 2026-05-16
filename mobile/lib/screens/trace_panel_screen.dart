import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'dart:async';
import '../config/env_config.dart';

class TracePanelScreen extends StatefulWidget {
  final String? incidentId;
  const TracePanelScreen({super.key, this.incidentId});

  @override
  State<TracePanelScreen> createState() => _TracePanelScreenState();
}

class _TracePanelScreenState extends State<TracePanelScreen> {
  List<String> allTraces = [];
  List<String> visibleTraces = [];
  bool isLoading = true;
  Timer? _traceTimer;
  final ScrollController _scrollController = ScrollController();

  @override
  void initState() {
    super.initState();
    _fetchTraces();
  }

  @override
  void dispose() {
    _traceTimer?.cancel();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _fetchTraces() async {
    try {
      String targetId = widget.incidentId ?? '';
      
      // If no incident ID passed, try to fetch the most recent active incident
      if (targetId.isEmpty) {
        final incidentsRes = await http.get(Uri.parse('${EnvConfig.backendUrl}/api/incidents'));
        if (incidentsRes.statusCode == 200) {
          final incidents = json.decode(incidentsRes.body)['incidents'] as List<dynamic>;
          if (incidents.isNotEmpty) {
            targetId = incidents.first['incident_id'];
          }
        }
      }

      if (targetId.isNotEmpty) {
        final res = await http.get(Uri.parse('${EnvConfig.backendUrl}/api/incidents/$targetId/trace'));
        if (res.statusCode == 200) {
          final data = json.decode(res.body);
          if (mounted) {
            setState(() {
              allTraces = (data['trace'] as List<dynamic>).map((e) => e.toString()).toList();
              isLoading = false;
            });
          }
          _startStreaming();
          return;
        }
      }
      
      if (mounted) {
        setState(() {
          isLoading = false;
        });
      }
    } catch (e) {
      debugPrint("Error fetching traces: $e");
      if (mounted) {
        setState(() {
          isLoading = false;
        });
      }
    }
  }

  void _startStreaming() {
    int index = 0;
    _traceTimer = Timer.periodic(const Duration(milliseconds: 300), (timer) {
      if (index < allTraces.length) {
        if (mounted) {
          setState(() {
            visibleTraces.add(allTraces[index]);
          });
          _scrollToBottom();
        }
        index++;
      } else {
        timer.cancel();
      }
    });
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent + 50,
        duration: const Duration(milliseconds: 200),
        curve: Curves.easeOut,
      );
    }
  }

  Color _getAgentColor(String agentName) {
    if (agentName.contains('SIGNAL_FUSION')) return Colors.blue;
    if (agentName.contains('CRISIS_CLASSIFIER')) return Colors.amber;
    if (agentName.contains('RESOURCE_ALLOCATOR')) return Colors.purpleAccent;
    if (agentName.contains('ACTION_EXECUTOR')) return Colors.greenAccent;
    if (agentName.contains('RECOVERY_AGENT')) return Colors.redAccent;
    return Colors.white70;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Agent Reasoning Trace'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      backgroundColor: Colors.black87,
      body: isLoading 
        ? const Center(child: CircularProgressIndicator())
        : Column(
            children: [
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                color: Colors.blueGrey.shade900,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: const [
                    Icon(Icons.auto_awesome, color: Colors.amber, size: 16),
                    SizedBox(width: 8),
                    Text(
                      "This decision was made autonomously",
                      style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold),
                      textAlign: TextAlign.center,
                    ),
                  ],
                ),
              ),
              Expanded(
                child: visibleTraces.isEmpty && !isLoading && allTraces.isEmpty
                  ? const Center(child: Text("No traces found", style: TextStyle(color: Colors.white)))
                  : ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.all(16),
                      itemCount: visibleTraces.length,
                      itemBuilder: (context, index) {
                        final log = visibleTraces[index];
                        final agentNameMatch = RegExp(r'\[(.*?)\]').firstMatch(log);
                        final agentName = agentNameMatch != null ? agentNameMatch.group(1) ?? "SYSTEM" : "SYSTEM";
                        final agentColor = _getAgentColor(agentName);
                        
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 8.0),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                '> ',
                                style: TextStyle(color: agentColor, fontFamily: 'monospace', fontSize: 14),
                              ),
                              Expanded(
                                child: RichText(
                                  text: TextSpan(
                                    style: const TextStyle(color: Colors.white70, fontFamily: 'monospace', fontSize: 13),
                                    children: [
                                      TextSpan(
                                        text: '[$agentName] ',
                                        style: TextStyle(color: agentColor, fontWeight: FontWeight.bold),
                                      ),
                                      TextSpan(
                                        text: log.substring(log.indexOf(']') + 1).trim(),
                                      ),
                                    ],
                                  ),
                                ),
                              ),
                            ],
                          ),
                        );
                      },
                    ),
              ),
              if (allTraces.isNotEmpty && visibleTraces.length == allTraces.length)
                Container(
                  padding: const EdgeInsets.all(16),
                  color: Colors.black,
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.check_circle, color: Colors.green, size: 16),
                      const SizedBox(width: 8),
                      Text(
                        "Total processing time: ~${(allTraces.length * 0.3).toStringAsFixed(1)}s",
                        style: const TextStyle(color: Colors.greenAccent, fontFamily: 'monospace'),
                      ),
                    ],
                  ),
                )
            ],
          ),
    );
  }
}
