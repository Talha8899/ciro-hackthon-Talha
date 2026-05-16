import asyncio
import json
from agents.resource_allocator import allocate_resources, AllocatorRequest, IncidentInfo

request = AllocatorRequest(
    incidents=[
        IncidentInfo(
            incident_id="Incident 1",
            crisis_type="flood",
            severity=4,
            affected_population=8000,
            location="G-10"
        ),
        IncidentInfo(
            incident_id="Incident 2",
            crisis_type="heatwave",
            severity=3,
            affected_population=2000,
            location="G-9"
        )
    ],
    available_resources={
        "ambulances": 3,
        "rescue_teams": 2,
        "police_units": 2
    }
)

async def main():
    print("Sending request to Resource Allocator...")
    response = await allocate_resources(request)
    print("\n--- Response ---")
    print(response.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
