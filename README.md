---

# CIRO — Crisis Intelligence & Response Orchestrator

> Built for Google AI Seekho Hackathon 2026 — Challenge 3

CIRO is an autonomous agentic AI system that detects urban crises 
in real time, reasons through multi-source signals, allocates 
emergency resources autonomously, and simulates coordinated 
response actions — all without human intervention.

---

## What CIRO Does

Most crisis response systems are reactive and fragmented. Signals 
exist — social media posts, weather data, traffic spikes — but 
nobody connects them into coordinated action in real time.

CIRO does exactly that. It continuously monitors multiple signal sources, detects anomalies, and uses Gemini 2.0 Flash to autonomously fuse, classify, and respond to crisis situations like urban flooding, heatwaves, or infrastructure failures.

## Features
- **Agentic Workflow**: Fully autonomous loop driven by specialized AI agents.
- **Signal Fusion**: Consolidates mock real-time data from various simulated feeds.
- **Resource Allocation**: Intelligently assigns response units based on crisis severity.
- **Mobile Dashboard**: Flutter frontend with real-time incident visualization and Text-to-Speech alerting.

## Tech Stack
- **Backend**: FastAPI (Python)
- **Frontend**: Flutter (Mobile/Web)
- **AI Models**: Gemini 2.0 Flash / Gemini 3.1 Pro (via Antigravity agents)
- **Architecture**: Modular Agentic Pipeline
