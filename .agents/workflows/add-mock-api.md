---
description:  Add a mock API data source for signal ingestion
---

## Steps

### 1. Ask which signal type
- weather / traffic / social_posts / sensor

### 2. Create mock data
- Go to backend/mock_apis/{signal_type}.py
- Create 3-5 realistic Pakistan-context data entries
- For social_posts: include Urdu/Roman Urdu text
- For weather: include rainfall mm/hr, humidity, temperature
- For traffic: include congestion percentage per zone

### 3. Create the endpoint
- Add GET /mock/{signal_type} to main.py
- Return random or sequential mock entries with timestamps

### 4. Test it
- Hit the endpoint and verify data looks realistic