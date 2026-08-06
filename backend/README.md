# Choose Your Own Adventure API

A FastAPI backend that generates branching stories with an OpenAI model and
stores stories, nodes, and background-job status in PostgreSQL.

## Setup

```bash
uv sync
cp .env.example .env
```

Update `.env` with your PostgreSQL connection string and OpenAI API key.

## Run

```bash
uv run main.py
```

Open the interactive API documentation at:

```text
http://localhost:8001/docs
```

Creating a story calls the configured OpenAI model and may incur API usage.

## Test

The story-flow test uses a fake LLM and an in-memory database, so it does not
make network requests or consume OpenAI credits.

```bash
uv run python -m unittest discover -s tests -v
```
