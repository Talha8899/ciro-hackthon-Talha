import asyncio
import json
from agents.crisis_classifier import classify_crisis, ClassifierRequest

request = ClassifierRequest(
    unified_signal={
      "social_analysis": [
        {
          "text": "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain",
          "credibility": 0.8,
          "urgency": 0.9,
          "location_match": 0.9
        },
        {
          "text": "Flooding on main road near G-10 metro",
          "credibility": 0.8,
          "urgency": 0.9,
          "location_match": 0.9
        },
        {
          "text": "Heavy rain since 2 hours",
          "credibility": 0.8,
          "urgency": 0.9,
          "location_match": 0.5
        }
      ],
      "weather_data": {
        "rainfall_mmhr": 42.0,
        "humidity": 94.0,
        "temperature_c": 28.0
      },
      "traffic_data": {
        "G10": 87,
        "G9": 45,
        "G11": 23
      }
    }
)

async def main():
    print("Sending request to Crisis Classifier...")
    response = await classify_crisis(request)
    print("\n--- Response ---")
    print(response.model_dump_json(indent=2))

if __name__ == "__main__":
    asyncio.run(main())
