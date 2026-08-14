# DecisionForge API

DecisionForge is an AI-powered decision-simulation backend built with FastAPI.

Users provide a scenario, role, and difficulty level. The backend generates a
validated decision graph, records the user's choices, summarizes the priorities
they expressed, and returns feedback and a final outcome.

## Main Flow

1. Create a simulation-generation job.
2. Poll the job until generation completes.
3. Start an attempt using the generated simulation.
4. Submit decisions one at a time.
5. Receive feedback, a decision profile, and a final outcome.

## Architecture

```text
API routers
    ↓
Business services
    ↓
AI generation and graph validation
    ↓
SQLAlchemy models
    ↓
SQLite or PostgreSQL
```
