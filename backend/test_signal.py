import requests
import json

url = "http://127.0.0.1:8000/api/signal-fusion"
payload = {
  "social_posts": [
    "G-10 mein pani bhar gaya hai, gaariyan phans gayi hain", 
    "Flooding on main road near G-10 metro", 
    "Heavy rain since 2 hours"
  ],
  "weather": {"rainfall_mmhr": 42, "humidity": 94, "temperature_c": 28},
  "traffic": {"G10": 87, "G9": 45, "G11": 23}
}

response = requests.post(url, json=payload)
print(f"Status Code: {response.status_code}")
try:
    print(json.dumps(response.json(), indent=2))
except Exception as e:
    print("Response is not JSON:")
    print(response.text)
