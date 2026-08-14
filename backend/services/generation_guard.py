from datetime import datetime, time, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.models.job import SimulationGenerationJob


def _job_count(
    db: Session,
    *,
    created_after: datetime,
    session_id: str | None = None,
) -> int:
    query = db.query(func.count(SimulationGenerationJob.id)).filter(
        SimulationGenerationJob.created_at >= created_after
    )

    if session_id is not None:
        query = query.filter(
            SimulationGenerationJob.session_id == session_id
        )

    return int(query.scalar() or 0)


def enforce_generation_limits(
    db: Session,
    session_id: str,
) -> None:
    if not settings.GENERATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "New simulations are temporarily paused. Please try "
                "again later."
            ),
        )

    now = datetime.now(timezone.utc)
    cooldown_start = now - timedelta(
        seconds=settings.GENERATION_COOLDOWN_SECONDS
    )

    if _job_count(
        db,
        created_after=cooldown_start,
        session_id=session_id,
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "Please wait a few seconds before creating another "
                "simulation."
            ),
        )

    day_start = datetime.combine(
        now.date(),
        time.min,
        tzinfo=timezone.utc,
    )

    session_count = _job_count(
        db,
        created_after=day_start,
        session_id=session_id,
    )
    if session_count >= settings.MAX_GENERATIONS_PER_SESSION_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="You have reached today's simulation-generation limit.",
        )

    global_count = _job_count(
        db,
        created_after=day_start,
    )
    if global_count >= settings.MAX_GENERATIONS_PER_DAY:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                "DecisionForge has reached today's generation capacity. "
                "Please try again tomorrow."
            ),
        )
