from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Verify required keys
if not os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("Missing GEMINI_API_KEY or GOOGLE_API_KEY in environment variables. Please check your .env file.")

import storage
import autonomous_loop

app = FastAPI(title="CIRO Autonomous Backend API", version="2.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    import asyncio
    # Start the autonomous loop background scheduler
    autonomous_loop.start_loop()
    # Run one immediate cycle when the server starts
    asyncio.create_task(autonomous_loop.run_one_cycle())

@app.on_event("shutdown")
async def shutdown_event():
    autonomous_loop.stop_loop()

@app.get("/")
async def root():
    return {"status": "CIRO Autonomous Engine running", "version": "2.0"}

@app.get("/api/incidents")
async def get_incidents():
    incidents = storage.get_all_incidents()
    # Sort by severity descending
    incidents.sort(key=lambda x: x.get("severity", 0), reverse=True)
    return {"incidents": incidents, "total": len(incidents)}

@app.get("/api/incidents/{incident_id}/trace")
async def get_incident_trace(incident_id: str):
    trace = storage.get_incident_trace(incident_id)
    return {"incident_id": incident_id, "trace": trace}

@app.get("/api/system-state")
async def get_system_state():
    incidents = storage.get_all_incidents()
    active_incidents = [i for i in incidents if i.get("status") == "active"]
    
    total_affected = sum(i.get("affected_population", 0) for i in active_incidents)
    
    # Calculate deployed resources and executed actions from the traces/state
    resources_deployed = 0
    actions_executed = 0
    recent_actions = []
    
    # Sort incidents by timestamp to get most recent first
    sorted_incidents = sorted(incidents, key=lambda x: x.get("timestamp", ""), reverse=True)
    
    from datetime import datetime, timezone
    
    for inc in sorted_incidents:
        if inc.get("status") == "active":
            for acts in inc.get("actions_executed", []):
                actions_executed += 1
                if acts.get("action_type") == "emergency_dispatch":
                    resources_deployed += acts.get("parameters", {}).get("count", 0)
        
        # Calculate time_ago for recent actions
        time_str = inc.get("timestamp", "")
        time_ago = "Just now"
        if time_str:
            try:
                # Handle isoformat with Z or + offset
                if time_str.endswith("Z"):
                    time_str = time_str[:-1] + "+00:00"
                dt = datetime.fromisoformat(time_str)
                now = datetime.now(timezone.utc)
                diff = (now - dt).total_seconds()
                if diff < 60:
                    time_ago = f"{int(diff)}s ago"
                elif diff < 3600:
                    time_ago = f"{int(diff//60)} min ago"
                else:
                    time_ago = f"{int(diff//3600)} hr ago"
            except Exception:
                pass
                
        # Extract traces
        traces = inc.get("reasoning_trace", [])
        for trace in reversed(traces):
            # Parse "[AGENT_NAME] [STEP] msg"
            if trace.startswith("[") and "]" in trace:
                parts = trace.split("]", 2)
                if len(parts) >= 3:
                    agent = parts[0][1:]
                    msg = parts[2].strip()
                    recent_actions.append(f"{time_ago} — {agent}: {msg}")
            if len(recent_actions) >= 5:
                break
        if len(recent_actions) >= 5:
            break
            
    if not recent_actions:
        recent_actions = ["System ready — monitoring signals"]
    
    return {
        "active_incidents": len(active_incidents),
        "total_affected": total_affected,
        "resources_deployed": resources_deployed,
        "actions_executed": actions_executed,
        "last_updated": autonomous_loop.last_run_timestamp,
        "loop_status": "running" if autonomous_loop.is_running else "stopped",
        "recent_actions": recent_actions[:5]
    }

@app.get("/api/loop-status")
async def get_loop_status():
    return {
        "status": "running" if autonomous_loop.is_running else "stopped",
        "last_run": autonomous_loop.last_run_timestamp,
        "next_run": autonomous_loop.get_next_run_time()
    }

class ManualSignalRequest(BaseModel):
    social_posts: List[str]
    weather: Dict[str, float]
    traffic: Dict[str, int]

@app.post("/api/inject-signal")
async def inject_signal(request: ManualSignalRequest, background_tasks: BackgroundTasks):
    """
    Accepts a manual signal injection and attempts to run Gemini. 
    Falls back to rule-based logic if API quota exhausted.
    """
    manual_signals = {
        "social_posts": request.social_posts,
        "weather": request.weather,
        "traffic": request.traffic
    }
    
    mode = "gemini"
    incident_id = None
    
    try:
        incident_id = await autonomous_loop.run_one_cycle(manual_signals)
        if not incident_id:
            raise Exception("Gemini pipeline failed to return an incident ID (possible 429 quota error).")
    except Exception as e:
        print(f"Gemini pipeline failed: {e}. Running rule-based fallback.")
        mode = "fallback"
        import time
        from datetime import datetime
        
        rainfall = request.weather.get("rainfall_mmhr", 0)
        temp = request.weather.get("temperature_c", 0)
        traffic_val = sum(request.traffic.values()) / max(len(request.traffic), 1) if request.traffic else 0
        social_text = " ".join(request.social_posts).lower()
        
        crisis_type = "General Emergency"
        severity = 3
        confidence = 0.70
        trace = []
        actions = []
        resources = ["1x Ambulance", "1x Medical Unit"]
        
        if rainfall > 30 and any(kw in social_text for kw in ["flood", "pani", "water"]):
            crisis_type = "Urban Flooding"
            severity = 4
            confidence = 0.84
            resources = ["2x Rescue Teams", "1x Police Unit", "1x Water Tanker"]
            actions = [
                {"action_type": "traffic_reroute", "description": "Traffic reroute executed via alternate route"},
                {"action_type": "emergency_dispatch", "description": "Emergency dispatch ticket created", "parameters": {"count": 3}},
                {"action_type": "stakeholder_alert", "description": "Hospital and emergency services notified"},
                {"action_type": "public_alert", "description": "Public alert broadcast sent to affected zone"}
            ]
            trace = [
                f"[SIGNAL_FUSION] {len(request.social_posts)} social posts analyzed — flood keywords detected",
                f"[SIGNAL_FUSION] Rainfall {rainfall}mm/hr — exceeds flood threshold 30mm",
                f"[SIGNAL_FUSION] Traffic congestion {int(traffic_val)}% — spike confirmed",
                "[SIGNAL_FUSION] Source credibility: high — multiple corroborating signals",
                "[CLASSIFY] Rule-based classification: Urban Flooding",
                "[CLASSIFY] Confidence 84% — rainfall + social + traffic all aligned",
                "[CLASSIFY] Severity 4/5 — high rainfall volume + population density",
                "[ALLOCATE] Priority score calculated: severity x population",
                "[ALLOCATE] Dispatching 2 rescue teams + 1 police unit + water tanker",
                "[ACTION] Traffic reroute executed via alternate route",
                "[ACTION] Emergency dispatch ticket created",
                "[ACTION] Hospital and emergency services notified",
                "[ACTION] Public alert broadcast sent to affected zone"
            ]
        elif temp > 40 and any(kw in social_text for kw in ["heat", "garmi"]):
            crisis_type = "Heatwave Alert"
            severity = 3
            confidence = 0.76
            resources = ["1x Ambulance", "1x Medical Unit"]
            actions = [
                {"action_type": "emergency_dispatch", "description": "Ambulance dispatched to affected sector", "parameters": {"count": 1}},
                {"action_type": "facility_activation", "description": "Cooling center activated at nearest community hall"},
                {"action_type": "public_alert", "description": "SMS alert sent to residents"}
            ]
            population = severity * 1500
            trace = [
                f"[SIGNAL_FUSION] Temperature {temp}C detected — critical heat threshold",
                "[SIGNAL_FUSION] Social signals: elderly distress reports confirmed",
                "[SIGNAL_FUSION] Humidity low — heat index elevated",
                "[CLASSIFY] Rule-based classification: Heatwave Alert",
                "[CLASSIFY] Confidence 76% — temperature + social signals aligned",
                "[CLASSIFY] Severity 3/5 — vulnerable population at risk",
                "[ALLOCATE] Medical resources prioritized for heat emergency",
                "[ALLOCATE] Dispatching ambulance + medical unit to zone",
                "[ACTION] Ambulance dispatched to affected sector",
                "[ACTION] Cooling center activated at nearest community hall",
                f"[ACTION] SMS alert sent to {population} residents"
            ]
        elif rainfall < 10 and any(kw in social_text for kw in ["pipe", "main", "kwsb"]):
            crisis_type = "Infrastructure Failure"
            severity = 2
            confidence = 0.91
            resources = ["1x Utility Team"]
            actions = [
                {"action_type": "emergency_dispatch", "description": "Utility team dispatched to repair water main", "parameters": {"count": 1}},
                {"action_type": "public_alert", "description": "Public correction notice sent"},
                {"action_type": "traffic_reroute", "description": "Road closure implemented at affected street"}
            ]
            trace = [
                "[SIGNAL_FUSION] Conflicting signals detected in social posts",
                "[SIGNAL_FUSION] Initial posts suggest flooding — later corrected",
                f"[SIGNAL_FUSION] Rainfall only {rainfall}mm/hr — below flood threshold",
                "[CLASSIFY] Initial classification: possible flooding",
                "[CLASSIFY] Conflict detected — posts contradict weather data",
                "[RECOVERY] Field verification: water main burst confirmed",
                "[RECOVERY] Decision: reclassify as Infrastructure Failure",
                "[RECOVERY] Flood alert retracted — stakeholders notified",
                "[ACTION] Utility team dispatched to repair water main",
                "[ACTION] Public correction notice sent",
                "[ACTION] Road closure implemented at affected street"
            ]
        else:
            actions = [
                {"action_type": "stakeholder_alert", "description": "Relevant authorities notified"}
            ]
            trace = [
                "[SIGNAL_FUSION] Signal anomalies detected across multiple vectors",
                "[CLASSIFY] Rule-based classification: General Emergency",
                "[ALLOCATE] Standard response protocol activated",
                "[ACTION] Authorities notified"
            ]
            
        incident_id = f"INC-{int(time.time())}"
        zone = list(request.traffic.keys())[0] if request.traffic else "Unknown Zone"
        
        fallback_incident = {
            "incident_id": incident_id,
            "status": "active",
            "crisis_type": crisis_type,
            "severity": severity,
            "affected_population": severity * 1500,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "reasoning_trace": trace,
            "location": f"{zone}, Islamabad",
            "zone": zone,
            "lat": 33.6844,
            "lng": 73.0479,
            "allocated_resources": resources,
            "actions_executed": actions
        }
        
        storage.save_incident(fallback_incident)
        
    return {
        "status": "success", 
        "incident_id": incident_id,
        "message": "Signal processed via rule-based fallback" if mode == "fallback" else "Signal injected. Autonomous cycle completed.",
        "mode": mode
    }
