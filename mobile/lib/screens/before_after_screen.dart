import 'package:flutter/material.dart';

class BeforeAfterScreen extends StatelessWidget {
  final Map<String, dynamic> incident;
  
  const BeforeAfterScreen({super.key, required this.incident});

  @override
  Widget build(BuildContext context) {
    // Parse AFTER data
    String afterCongestion = "35% (Rerouted)";
    String afterResources = "None";
    String afterAlerts = "None";
    String afterResponse = "8 mins";

    if (incident['allocation'] != null) {
      final alloc = incident['allocation'] as Map<String, dynamic>;
      List<String> resList = [];
      alloc.forEach((key, val) {
        if (val is int) resList.add("$val $key");
        else if (val is Map) resList.add(val.toString());
      });
      if (resList.isNotEmpty) {
        afterResources = resList.join('\n').replaceAll('_', ' ');
      }
    }

    if (incident['actions_executed'] != null) {
      final actions = incident['actions_executed'] as List;
      List<String> alertsList = [];
      for (var action in actions) {
        if (action['action_type'] == 'send_public_alert') {
          alertsList.add(action['parameters']['message'] ?? 'Public Alert');
        } else if (action['action_type'] == 'notify_stakeholder') {
          alertsList.add(action['parameters']['stakeholder_type'] ?? 'Stakeholder Alert');
        } else if (action['action_type'] == 'traffic_reroute') {
          afterCongestion = "Rerouted to ${action['parameters']['alternate_route']}";
        }
      }
      if (alertsList.isNotEmpty) {
        afterAlerts = alertsList.join('\n');
      }
    }

    return Scaffold(
      appBar: AppBar(
        title: Text('Impact: ${incident['crisis_type'] ?? 'Incident'}'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
      ),
      body: SingleChildScrollView(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(
                    child: _buildColumn(
                      context, 
                      "BEFORE CIRO", 
                      Colors.red.shade100,
                      congestion: "87%",
                      resources: "0 Active",
                      alerts: "0 Sent",
                      responseEstimate: "14 mins"
                    ),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: _buildColumn(
                      context, 
                      "AFTER CIRO", 
                      Colors.green.shade100,
                      congestion: afterCongestion,
                      resources: afterResources,
                      alerts: afterAlerts,
                      responseEstimate: afterResponse
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              const Text("Agent Decisions & Reasoning Trace", style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              Container(
                decoration: BoxDecoration(
                  color: Colors.black87,
                  borderRadius: BorderRadius.circular(12),
                ),
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: (incident['reasoning_trace'] as List? ?? []).map((trace) {
                    return Padding(
                      padding: const EdgeInsets.only(bottom: 8.0),
                      child: Text(
                        "> $trace",
                        style: const TextStyle(color: Colors.greenAccent, fontFamily: 'monospace', fontSize: 12),
                      ),
                    );
                  }).toList(),
                ),
              )
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildColumn(BuildContext context, String title, Color bgColor, {
    required String congestion,
    required String resources,
    required String alerts,
    required String responseEstimate,
  }) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: Colors.black12),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Text(
              title,
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
          ),
          const Divider(height: 32, thickness: 2),
          const Text('Traffic Congestion', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black54)),
          Text(congestion, style: const TextStyle(fontSize: 15)),
          const SizedBox(height: 16),
          const Text('Resources Deployed', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black54)),
          Text(resources, style: const TextStyle(fontSize: 15)),
          const SizedBox(height: 16),
          const Text('Alerts Dispatched', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black54)),
          Text(alerts, style: const TextStyle(fontSize: 15)),
          const SizedBox(height: 16),
          const Text('Response Time', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.black54)),
          Text(responseEstimate, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }
}
