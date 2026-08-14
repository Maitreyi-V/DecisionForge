FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY backend/pyproject.toml backend/uv.lock backend/README.md ./backend/
RUN uv sync --project backend --frozen --no-dev --no-install-project

COPY backend ./backend

ENV PATH="/app/backend/.venv/bin:$PATH"

EXPOSE 8001

CMD ["sh", "-c", "alembic -c backend/alembic.ini upgrade head && uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8001}"]
