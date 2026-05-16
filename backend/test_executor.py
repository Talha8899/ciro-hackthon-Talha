import asyncio
import json
from agents.action_executor import execute_actions, ExecutorRequest

request = ExecutorRequest(
    allocation_plan={
        "Incident 1": {
            "ambulances": 2,
            "rescue_teams": 1,
            "police_units": 1
        },
        "Incident 2": {
            "ambulances": 1,
            "rescue_teams": 1,
            "police_units": 1
        }
    }
)

async def main():
    print("Sending request to Action Executor...")
    response = await execute_actions(request)
    print("\n--- Response ---")
    print(response.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
