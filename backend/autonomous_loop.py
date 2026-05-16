import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import storage

from agents.signal_fusion import run_signal_fusion
from agents.crisis_classifier import run_crisis_classifier, CrisisClassification
from agents.resource_allocator import run_resource_allocator
from agents.action_executor import run_action_executor
from agents.recovery_agent import run_recovery_agent

scheduler = AsyncIOScheduler()
is_running = False
last_run_timestamp = None

def fetch_all_signals():
    """Mock API to fetch signals."""
    return {
        "social_posts": [
            "Heavy rain in G-10 right now",
            "Roads starting to flood near G-10 Markaz"
        ],
        "weather": {
            "rainfall_mmhr": 45.0,
            "humidity": 88.0,
            "temperature_c": 24.0
        },
        "traffic": {
            "G10": 85,
            "G9": 30,
            "G11": 40
        }
    }

def fetch_available_resources():
    return {
        "ambulances": 5,
        "rescue_teams": 3,
        "police_units": 4,
        "water_tankers": 2
    }

async def run_one_cycle(manual_signals=None):
    global last_run_timestamp
    print("\n" + "="*50)
    print(f"[AUTONOMOUS LOOP] Starting cycle at {datetime.utcnow().isoformat()}Z")
    
    signals = manual_signals if manual_signals else fetch_all_signals()
    
    incident_id = f"INC-{int(datetime.utcnow().timestamp())}"
    
    try:
        # 1. Signal Fusion
        fusion_output = await run_signal_fusion(
            social_posts=signals.get("social_posts", []),
            weather=signals.get("weather", {}),
            traffic=signals.get("traffic", {})
        )
        
        # 2. Crisis Classifier
        classifier_output = await run_crisis_classifier(
            unified_signal=fusion_output["result"]["unified_signal"]
        )
        
        confidence = classifier_output["confidence"]
        crisis_type = classifier_output["result"]["crisis_type"]
        conflict_detected = classifier_output["result"].get("conflict_detected", False)
        conflict_description = classifier_output["result"].get("conflict_description", "")
        
        active_incidents = [inc for inc in storage.get_all_incidents() if inc.get("status") == "active"]
        
        if confidence > 0.6 and crisis_type != "unknown":
            print(f"[AUTONOMOUS LOOP] Detected {crisis_type} with {confidence} confidence.")
            
            # Check for conflict with recent active incident
            if conflict_detected and active_incidents:
                # Heuristic: Match with the most recent active incident
                recent_incident = sorted(active_incidents, key=lambda x: x.get("timestamp", ""), reverse=True)[0]
                print(f"[AUTONOMOUS LOOP] Conflict detected! Calling Recovery Agent for incident {recent_incident['incident_id']}.")
                
                # We need to construct a CrisisClassification object for the recovery agent
                from agents.crisis_classifier import CrisisClassification
                original_classification = CrisisClassification(
                    crisis_type=recent_incident.get("crisis_type", "unknown"),
                    severity=recent_incident.get("severity", 1),
                    affected_radius_km=0.0, # Approximate
                    affected_population=recent_incident.get("affected_population", 0),
                    conflict_detected=False,
                    conflict_description="",
                    confidence=recent_incident.get("confidence", 0.0),
                    reasoning_steps=[]
                )
                
                # We need to simulate alerts sent
                alerts_sent = [{"zone": recent_incident["incident_id"], "message": "Initial crisis alert"}]
                
                recovery_output = await run_recovery_agent(
                    incident_id=recent_incident["incident_id"],
                    original_classification=original_classification,
                    field_report=f"Conflict detected during autonomous loop: {conflict_description}",
                    alerts_sent=alerts_sent
                )
                
                decision = recovery_output["result"]["decision"]
                recent_incident["status"] = "retracted" if decision == "retract" else "reclassified"
                if decision == "reclassified":
                    # Update crisis type if available
                    updated_class = recovery_output["result"].get("updated_classification")
                    if updated_class:
                        recent_incident["crisis_type"] = updated_class.get("crisis_type", recent_incident["crisis_type"])
                        recent_incident["severity"] = updated_class.get("severity", recent_incident["severity"])
                
                recent_incident["reasoning_trace"].extend(fusion_output["reasoning_steps"])
                recent_incident["reasoning_trace"].extend(classifier_output["reasoning_steps"])
                recent_incident["reasoning_trace"].extend(recovery_output["reasoning_steps"])
                
                storage.update_incident(recent_incident["incident_id"], {
                    "status": recent_incident["status"],
                    "crisis_type": recent_incident["crisis_type"],
                    "severity": recent_incident.get("severity"),
                    "reasoning_trace": recent_incident["reasoning_trace"]
                })
                print(f"[AUTONOMOUS LOOP] Incident {recent_incident['incident_id']} updated to {recent_incident['status']}.")
                return recent_incident["incident_id"]
                
            else:
                # Normal flow: prepare incident state for tracking
                current_incident = {
                    "incident_id": incident_id,
                    "status": "active",
                    "crisis_type": crisis_type,
                    "severity": classifier_output["result"]["severity"],
                    "affected_population": classifier_output["result"]["affected_population"],
                    "confidence": confidence,
                    "timestamp": datetime.utcnow().isoformat() + "Z",
                    "reasoning_trace": []
                }
                
                # Append traces
                current_incident["reasoning_trace"].extend(fusion_output["reasoning_steps"])
                current_incident["reasoning_trace"].extend(classifier_output["reasoning_steps"])
                
                # 3. Resource Allocator
                # We must pass it as a list of dicts as per the new programmatic signature
                incident_list_for_allocator = [current_incident]
                allocator_output = await run_resource_allocator(
                    incidents=incident_list_for_allocator,
                    available_resources=fetch_available_resources()
                )
                
                current_incident["allocation"] = allocator_output["result"]["allocation_plan"]
                current_incident["reasoning_trace"].extend(allocator_output["reasoning_steps"])
                
                # 4. Action Executor
                executor_output = await run_action_executor(
                    allocation_plan=allocator_output["result"]["allocation_plan"],
                    incident_details=current_incident
                )
                
                current_incident["actions_executed"] = executor_output["result"]["actions_executed"]
                current_incident["reasoning_trace"].extend(executor_output["reasoning_steps"])
                
                # Save to persistent storage
                storage.save_incident(current_incident)
                print(f"[AUTONOMOUS LOOP] Incident {incident_id} saved successfully.")
                return incident_id
            
        else:
            print(f"[AUTONOMOUS LOOP] No significant crisis detected. Confidence: {confidence}")
            if manual_signals is not None:
                raise Exception("No significant crisis detected.")
            
    except Exception as e:
        import traceback
        print(f"[AUTONOMOUS LOOP] Error during cycle: {e}")
        traceback.print_exc()
        
    last_run_timestamp = datetime.utcnow().isoformat() + "Z"
    print("[AUTONOMOUS LOOP] Cycle complete.")
    print("="*50 + "\n")

def get_next_run_time():
    job = scheduler.get_job('autonomous_cycle')
    if job and job.next_run_time:
        return job.next_run_time.isoformat()
    return None

def start_loop():
    global is_running
    if not is_running:
        interval = int(os.getenv("SCHEDULER_INTERVAL_SECONDS", "30"))
        scheduler.add_job(run_one_cycle, 'interval', seconds=interval, id='autonomous_cycle', max_instances=1)
        scheduler.start()
        is_running = True
        print(f"[AUTONOMOUS LOOP] Scheduler started. Running every {interval} seconds.")

def stop_loop():
    global is_running
    if is_running:
        scheduler.shutdown()
        is_running = False
        print("[AUTONOMOUS LOOP] Scheduler stopped.")
