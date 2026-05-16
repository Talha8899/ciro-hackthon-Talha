import os
import json
import random
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import google.generativeai as genai

# Global state tracker as requested
SYSTEM_STATE = {
    "active_incidents": [],
    "dispatched_resources": {},
    "sent_alerts": []
}

class ExecutorRequest(BaseModel):
    allocation_plan: Dict[str, Dict[str, int]]
    incident_details: Optional[Dict[str, Any]] = None # Optional context for Gemini

class ActionDefinition(BaseModel):
    incident_id: str
    action_type: str # traffic_reroute, emergency_dispatch, send_public_alert, notify_stakeholder
    parameters: Dict[str, Any]
    reasoning: str

class ActionPlanOutput(BaseModel):
    actions: List[ActionDefinition]
    reasoning_steps: List[str]

class ActionExecutionResult(BaseModel):
    incident_id: str
    action_type: str
    parameters: Dict[str, Any]
    status: str
    confirmation_id: Optional[str]
    timestamp: str
    retry_suggestion: Optional[str] = None
    reasoning: str

def generate_ticket(prefix: str) -> str:
    return f"{prefix}-{str(uuid.uuid4())[:6].upper()}"

def simulate_traffic_reroute(zone: str, alternate_route: str) -> Dict[str, Any]:
    return {
        "status": "success",
        "confirmation_id": generate_ticket("TRF"),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def simulate_emergency_dispatch(unit_type: str, count: int, destination: str) -> Dict[str, Any]:
    # Simulate a small chance of failure
    if random.random() < 0.1:
        return {
            "status": "failed",
            "confirmation_id": None,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "retry_suggestion": f"Check availability of {unit_type} at nearest depot."
        }
    
    # Update state
    current_count = SYSTEM_STATE["dispatched_resources"].get(unit_type, 0)
    SYSTEM_STATE["dispatched_resources"][unit_type] = current_count + count
    
    return {
        "status": "success",
        "confirmation_id": generate_ticket("DSP"),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def simulate_send_public_alert(zone: str, message: str) -> Dict[str, Any]:
    SYSTEM_STATE["sent_alerts"].append({"zone": zone, "message": message, "time": datetime.utcnow().isoformat()})
    return {
        "status": "success",
        "confirmation_id": generate_ticket("ALT"),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

def simulate_notify_stakeholder(stakeholder_type: str, message: str) -> Dict[str, Any]:
    return {
        "status": "success",
        "confirmation_id": generate_ticket("STK"),
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }

async def run_action_executor(allocation_plan: Dict[str, Dict[str, int]], incident_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Action Executor Agent function.
    Takes an allocation plan, plans concrete actions using Gemini, and executes simulated API calls.
    Maintains a SYSTEM_STATE dict reflecting the actions.
    """
    trace = []
    
    def log_step(step: str):
        msg = f"[ACTION_EXECUTOR] [STEP] {step}"
        print(msg)
        trace.append(msg)
        
    log_step(f"Received allocation plan for {len(allocation_plan)} incidents.")
    
    # Update system state with active incidents
    for inc_id in allocation_plan.keys():
        if inc_id not in SYSTEM_STATE["active_incidents"]:
            SYSTEM_STATE["active_incidents"].append(inc_id)
            
    log_step("Calling Gemini to formulate exact action definitions based on allocation plan.")
    
    api_key = os.environ.get("GEMINI_API_KEY", os.environ.get("GOOGLE_API_KEY", ""))
    if not api_key:
        log_step("WARNING: GEMINI_API_KEY not found in environment. Call may fail.")
    genai.configure(api_key=api_key)
    
    system_instruction = """
    You are an Action Executor Planner for an emergency response system.
    Given an allocation plan of resources to incidents, determine the concrete actions needed.
    You must output a list of actions to take. 
    Supported action_types:
    - traffic_reroute: needs parameters 'zone', 'alternate_route'
    - emergency_dispatch: needs parameters 'unit_type', 'count', 'destination'
    - send_public_alert: needs parameters 'zone', 'message'
    - notify_stakeholder: needs parameters 'stakeholder_type' (e.g., hospital, utility_company, police_command, media), 'message'
    
    For each assigned resource in the allocation plan, create an emergency_dispatch action.
    Also generate relevant public alerts, traffic reroutes, and stakeholder notifications.
    Provide reasoning steps for your plan.
    """
    
    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=system_instruction
        )
        
        prompt = f"Allocation Plan:\n{json.dumps(allocation_plan, indent=2)}\n\nGenerate the actions."
        log_step("Executing Gemini API call for action planning...")
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                response_schema=ActionPlanOutput,
                temperature=0.2
            )
        )
        
        log_step("Successfully received action plan from Gemini.")
        action_plan_data = json.loads(response.text)
        action_plan = ActionPlanOutput(**action_plan_data)
        
        for r_step in action_plan.reasoning_steps:
            log_step(f"Gemini reasoning: {r_step}")
            
    except Exception as e:
        log_step(f"Error calling Gemini API: {str(e)}")
        log_step("Falling back to deterministic action generation.")
        
        fallback_actions = []
        for inc_id, resources in allocation_plan.items():
            for res_type, count in resources.items():
                fallback_actions.append(ActionDefinition(
                    incident_id=inc_id,
                    action_type="emergency_dispatch",
                    parameters={"unit_type": res_type, "count": count, "destination": inc_id},
                    reasoning="Fallback deterministic dispatch"
                ))
            fallback_actions.append(ActionDefinition(
                incident_id=inc_id,
                action_type="send_public_alert",
                parameters={"zone": inc_id, "message": "Emergency response dispatched."},
                reasoning="Fallback deterministic alert"
            ))
            
        action_plan = ActionPlanOutput(
            actions=fallback_actions,
            reasoning_steps=["API failed", "Generated fallback actions deterministically"]
        )

    # Execute actions
    actions_executed = []
    success_count = 0
    
    log_step("Beginning simulation of action execution.")
    
    for action in action_plan.actions:
        log_step(f"Executing: {action.action_type} for {action.incident_id}")
        
        sim_result = {}
        if action.action_type == "traffic_reroute":
            sim_result = simulate_traffic_reroute(
                action.parameters.get("zone", "unknown"),
                action.parameters.get("alternate_route", "unknown")
            )
        elif action.action_type == "emergency_dispatch":
            sim_result = simulate_emergency_dispatch(
                action.parameters.get("unit_type", "unknown"),
                action.parameters.get("count", 1),
                action.parameters.get("destination", action.incident_id)
            )
        elif action.action_type == "send_public_alert":
            sim_result = simulate_send_public_alert(
                action.parameters.get("zone", action.incident_id),
                action.parameters.get("message", "Alert")
            )
        elif action.action_type == "notify_stakeholder":
            sim_result = simulate_notify_stakeholder(
                action.parameters.get("stakeholder_type", "hospital"),
                action.parameters.get("message", "Notification")
            )
        else:
            sim_result = {
                "status": "failed",
                "confirmation_id": None,
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "retry_suggestion": f"Unknown action type: {action.action_type}"
            }
            
        if sim_result["status"] == "success":
            success_count += 1
            log_step(f"Action {action.action_type} SUCCESS. ID: {sim_result.get('confirmation_id')}")
        else:
            log_step(f"Action {action.action_type} FAILED. Suggestion: {sim_result.get('retry_suggestion')}")
            
        executed_obj = ActionExecutionResult(
            incident_id=action.incident_id,
            action_type=action.action_type,
            parameters=action.parameters,
            status=sim_result["status"],
            confirmation_id=sim_result.get("confirmation_id"),
            timestamp=sim_result["timestamp"],
            retry_suggestion=sim_result.get("retry_suggestion"),
            reasoning=action.reasoning
        )
        actions_executed.append(executed_obj.model_dump())

    log_step("Formatting final response object.")
    
    return {
        "result": {
            "actions_executed": actions_executed,
            "total_actions": len(actions_executed),
            "success_count": success_count,
            "system_state_snapshot": SYSTEM_STATE
        },
        "confidence": 0.9,
        "reasoning_steps": trace,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "agent_name": "ACTION_EXECUTOR"
    }
