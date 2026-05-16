import asyncio
import json
from agents.recovery_agent import process_recovery, RecoveryRequest
from agents.crisis_classifier import CrisisClassification

request = RecoveryRequest(
    incident_id="Incident-1",
    original_classification=CrisisClassification(
        crisis_type="flood",
        severity=4,
        affected_radius_km=2.5,
        affected_population=8000,
        conflict_detected=False,
        conflict_description="",
        confidence=0.85,
        reasoning_steps=["Initial assessment based on social media"]
    ),
    field_report="Water main burst confirmed. No surface flooding. Road team on site.",
    alerts_sent=[
        {"zone": "G-10", "message": "Emergency: Flood detected in G-10. Evacuate immediately."}
    ]
)

async def main():
    print("Sending request to Recovery Agent...")
    response = await process_recovery(request)
    print("\n--- Response ---")
    print(response.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
