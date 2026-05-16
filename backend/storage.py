import json
import os
from filelock import FileLock

STORAGE_FILE = "incidents.json"
LOCK_FILE = "incidents.json.lock"

def _read_data():
    if not os.path.exists(STORAGE_FILE):
        return {}
    with open(STORAGE_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def _write_data(data):
    with open(STORAGE_FILE, "w") as f:
        json.dump(data, f, indent=2)

def save_incident(incident_dict):
    """Saves a new incident or completely overwrites an existing one."""
    incident_id = incident_dict.get("incident_id")
    if not incident_id:
        return
        
    with FileLock(LOCK_FILE):
        data = _read_data()
        data[incident_id] = incident_dict
        _write_data(data)

def get_all_incidents():
    """Returns a list of all incidents."""
    with FileLock(LOCK_FILE):
        data = _read_data()
        return list(data.values())

def update_incident(incident_id, updates):
    """Updates specific fields in an existing incident."""
    with FileLock(LOCK_FILE):
        data = _read_data()
        if incident_id in data:
            data[incident_id].update(updates)
            _write_data(data)

def get_incident_trace(incident_id):
    """Retrieves only the reasoning trace for a specific incident."""
    with FileLock(LOCK_FILE):
        data = _read_data()
        incident = data.get(incident_id, {})
        return incident.get("reasoning_trace", [])

def seed_demo_incidents():
    """Seeds 3 pre-built demo incidents if no data exists, saving API quota."""
    if os.path.exists(STORAGE_FILE):
        data = _read_data()
        if data:
            return  # Already has data
            
    demo_data = {
        "INC-001": {
            "incident_id": "INC-001",
            "crisis_type": "Urban Flooding",
            "location": "G-10 Markaz, Islamabad",
            "zone": "G-10",
            "severity": 4,
            "confidence": 0.87,
            "affected_population": 8200,
            "status": "active",
            "allocated_resources": ["2x Rescue Teams", "1x Police Unit", "1x Water Tanker"],
            "actions_executed": [
                {"action_type": "traffic_reroute", "description": "Traffic rerouted via F-10"},
                {"action_type": "emergency_dispatch", "description": "Rescue teams dispatched", "parameters": {"count": 2}},
                {"action_type": "ticket_opened", "description": "Emergency ticket 4821 opened"},
                {"action_type": "stakeholder_alert", "description": "Poly Clinic Hospital alerted"},
                {"action_type": "public_alert", "description": "Public alert broadcast sent"}
            ],
            "lat": 33.6844,
            "lng": 73.0479,
            "timestamp": "2026-05-16T12:00:00Z",
            "reasoning_trace": [
                "[SIGNAL_FUSION] 4 social posts matched G-10 flooding",
                "[SIGNAL_FUSION] Rainfall 42mm/hr — above flood threshold of 30mm",
                "[SIGNAL_FUSION] Traffic congestion 87% in G-10 — spike detected",
                "[SIGNAL_FUSION] Source credibility scored — 3 high, 1 medium",
                "[CLASSIFY] Analyzing unified signal with Gemini 2.0 Flash",
                "[CLASSIFY] Crisis type: Urban Flooding — confidence 87%",
                "[CLASSIFY] Severity 4/5 — estimated population 8200 in 2km radius",
                "[CLASSIFY] No conflicting signals detected",
                "[ALLOCATE] Flood priority score: 4 x 8200 = 32800",
                "[ALLOCATE] Heatwave priority score: 3 x 2000 = 6000",
                "[ALLOCATE] Decision: flood gets 2 rescue teams + 1 police unit",
                "[ALLOCATE] Heatwave gets remaining 1 ambulance",
                "[ACTION] Executing traffic reroute via F-10 Markaz",
                "[ACTION] Emergency dispatch ticket 4821 created",
                "[ACTION] Poly Clinic Hospital notified via stakeholder alert",
                "[ACTION] Public alert broadcast sent via SMS to G-10 residents"
            ]
        },
        "INC-002": {
            "incident_id": "INC-002",
            "crisis_type": "Building Fire",
            "location": "Blue Area, Islamabad",
            "zone": "Blue Area",
            "severity": 5,
            "confidence": 0.95,
            "affected_population": 1500,
            "status": "active",
            "allocated_resources": ["3x Fire Trucks", "2x Ambulances", "2x Police Units"],
            "actions_executed": [
                {"action_type": "emergency_dispatch", "description": "Fire trucks and ambulances dispatched", "parameters": {"count": 5}},
                {"action_type": "evacuation_order", "description": "Evacuation order issued for adjacent buildings"},
                {"action_type": "stakeholder_alert", "description": "PIMS Hospital alerted for burn victims"}
            ],
            "lat": 33.7077,
            "lng": 73.0498,
            "timestamp": "2026-05-16T13:30:00Z",
            "reasoning_trace": [
                "[SIGNAL_FUSION] Multiple smoke detectors triggered in Blue Area sector F",
                "[SIGNAL_FUSION] 12 emergency calls routed from location",
                "[CLASSIFY] Crisis type: Building Fire — confidence 95%",
                "[CLASSIFY] Severity 5/5 — critical infrastructure at risk",
                "[ALLOCATE] High priority due to life safety risk",
                "[ALLOCATE] Dispatched maximum available fire units",
                "[ACTION] Executed evacuation protocol for immediate vicinity"
            ]
        },
        "INC-003": {
            "incident_id": "INC-003",
            "crisis_type": "Major Traffic Accident",
            "location": "Kashmir Highway near G-11",
            "zone": "G-11",
            "severity": 3,
            "confidence": 0.92,
            "affected_population": 40,
            "status": "resolved",
            "allocated_resources": ["1x Ambulance", "1x Police Unit", "1x Tow Truck"],
            "actions_executed": [
                {"action_type": "emergency_dispatch", "description": "Ambulance and police dispatched", "parameters": {"count": 2}},
                {"action_type": "traffic_reroute", "description": "Traffic diverted to service road"}
            ],
            "lat": 33.6700,
            "lng": 73.0100,
            "timestamp": "2026-05-16T10:15:00Z",
            "reasoning_trace": [
                "[SIGNAL_FUSION] Camera feed detected multi-vehicle collision",
                "[CLASSIFY] Crisis type: Major Traffic Accident — confidence 92%",
                "[CLASSIFY] Severity 3/5 — significant traffic disruption",
                "[ALLOCATE] 1 Ambulance assigned based on camera casualty estimation",
                "[ACTION] Traffic diversion activated"
            ]
        }
    }
    
    with FileLock(LOCK_FILE):
        _write_data(demo_data)

# Call on import to seed automatically
seed_demo_incidents()
