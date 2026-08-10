from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.session import get_or_create_session_id
from db.database import get_db
from models.job import SimulationGenerationJob
from schemas.job import SimulationGenerationJobResponse


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

    return job