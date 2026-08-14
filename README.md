# DecisionForge

DecisionForge is an AI-powered professional decision simulator. A user enters
a difficult scenario and their role, then explores a validated decision graph
with balanced trade-offs, consequence feedback, decision profiling, and
alternative-path replay.


## Live Demo

[Try DecisionForge](https://decisionforge-mv.streamlit.app)

The backend uses a free Render instance, so the first request may take up to
a minute while the service wakes up.


## What makes it different

- A low-cost qualification gate rejects scenarios with no genuine trade-off.
- GPT-generated output is parsed into typed Pydantic models.
- A graph validator rejects cycles, unreachable nodes, and dangling targets.
- Simulations vary between three and five decisions with two or three choices.
- A decision profile summarizes the priorities expressed across the path.
- Result replay shows unchosen branches and their possible outcomes.
- Signed anonymous sessions isolate user data without requiring accounts.
- A private generation key plus database-backed quotas protects OpenAI billing.

## Architecture

```text
Browser
  ↓
Streamlit UI
  ↓ private generation key
FastAPI
  ├── scenario qualification (GPT-4o mini)
  ├── simulation generation (GPT-4 Turbo)
  ├── graph validation and decision-profile services
  └── SQLAlchemy
         ↓
      PostgreSQL in production / SQLite locally
```

Generation runs as a tracked background job. The frontend polls job status,
while provider timeouts and stale-job recovery prevent indefinite loading.

## Run locally

From the repository root:

```bash
cp backend/.env.example backend/.env
uv sync --project backend
backend/.venv/bin/alembic -c backend/alembic.ini upgrade head
backend/.venv/bin/uvicorn backend.main:app --reload --port 8001
```

In another terminal:

```bash
python3 -m venv frontend/.venv
frontend/.venv/bin/pip install -r frontend/requirements.txt
frontend/.venv/bin/streamlit run frontend/app.py
```

The Streamlit app opens at `http://localhost:8501`; FastAPI documentation is
available at `http://localhost:8001/docs`.

## Important configuration

Copy `backend/.env.example` and set at minimum:

- `DECISIONFORGE_DATABASE_URL`
- `DECISIONFORGE_ENVIRONMENT=production`
- `DECISIONFORGE_OPENAI_API_KEY`
- `DECISIONFORGE_GENERATION_API_KEY`
- `DECISIONFORGE_GENERATION_ENABLED`
- `DECISIONFORGE_SESSION_SECRET_KEY`

The frontend must receive the same generation key through
`DECISIONFORGE_GENERATION_API_KEY`, plus the deployed backend URL through
`DECISIONFORGE_API_URL`.

For production, use PostgreSQL, set `DECISIONFORGE_COOKIE_SECURE=True`, and
replace both example secrets with independently generated random values.
Set `DECISIONFORGE_GENERATION_ENABLED=False` whenever you need to pause new
AI generation without taking the application offline.

## Tests

```bash
backend/.venv/bin/python -m unittest discover -s backend/tests -v
backend/.venv/bin/alembic -c backend/alembic.ini check
```

The focused suite covers the complete decision flow, generation-route access,
request validation, and graph corruption cases such as cycles, unreachable
nodes, and dangling target keys.


