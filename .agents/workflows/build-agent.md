---
description: Build a new CIRO agent with full trace logging
---

## Steps

### 1. Ask what agent to build
- Ask the user: which agent? (signal_fusion / crisis_classifier / resource_allocator / action_executor / recovery)
- Ask: what inputs does it receive?
- Ask: what should it output?

### 2. Create the agent file
- Create backend/agents/{agent_name}.py
- Include: docstring, input schema as TypedDict, output schema as TypedDict
- Main function must be async
- Call Gemini API with a detailed reasoning prompt
- Parse Gemini response and extract: decision, confidence, reasoning_steps

### 3. Add trace logging
- Every reasoning step must log: print(f"[{AGENT_NAME}] {step}: {detail}")
- Return a trace_log list in the output dict

### 4. Add the endpoint to main.py
- POST /api/{agent_name}
- Validate input, call agent, return full output including trace

### 5. Test it
- Run the endpoint with sample data
- Show the output including the reasoning trace