---
trigger: always_on
---

# CIRO Project Rules

## Project Context
This is CIRO — Crisis Intelligence & Response Orchestrator.
A hackathon project for Google AI Seekho 2026, Challenge 3.
We have 4 days. Prioritize working code over perfect code.

## Tech Stack
- Backend: FastAPI (Python)
- Mobile: Flutter
- Database: Firestore (mock JSON files locally for now)
- AI: Gemini 2.0 Flash via Antigravity agents
- All agent logic must be clearly commented for judge review

## Code Rules
- Every agent function must print a reasoning trace log to console AND return it in the response
- Log format: [AGENT_NAME] [STEP] message
- Use simple Python — no unnecessary abstractions
- All mock data goes in backend/mock_apis/ as Python dicts, not external files
- Every endpoint must return: result + confidence_score + reasoning_trace + timestamp

## Agent Rules
- Each agent is a separate Python file in backend/agents/
- Every agent must have: a docstring explaining what it does, input schema, output schema
- Never hardcode decisions — always show reasoning steps in the response
- Agents must handle the case where input data is missing or conflicting

## What NOT to do
- Do not use LangChain or any agent framework other than direct Gemini API calls
- Do not add authentication or user management
- Do not optimize for production scale — optimize for clear demo output