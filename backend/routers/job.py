from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.session import get_or_create_session_id
from backend.db.database import get_db
from backend.models.job import SimulationGenerationJob
from backend.schemas.job import SimulationGenerationJobResponse
from backend.services.generation_job_service import (
    expire_stale_generation_job,
)


router = APIRouter(
    prefix="/jobs",
    tags=["jobs"],
)


@router.get(
    "/{job_id}",
    response_model=SimulationGenerationJobResponse,
)
def get_job_status(
    job_id: UUID,
    session_id: str = Depends(get_or_create_session_id),
    db: Session = Depends(get_db),
):
    job = (
        db.query(SimulationGenerationJob)
        .filter(
            SimulationGenerationJob.job_id == str(job_id),
            SimulationGenerationJob.session_id == session_id,
        )
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generation job not found",
        )

    return expire_stale_generation_job(
        db=db,
        job=job,
    )
