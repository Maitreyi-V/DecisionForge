import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from backend.core.session import get_or_create_session_id
from backend.core.security import require_generation_api_key
from backend.db.database import get_db
from backend.models.job import SimulationGenerationJob
from backend.schemas.job import (
    GenerationJobStatus,
    SimulationGenerationJobResponse,
)
from backend.schemas.simulation import GenerateSimulationRequest
from backend.services.generation_job_service import (
    run_simulation_generation_job,
)
from backend.services.generation_guard import enforce_generation_limits


router = APIRouter(
    prefix="/simulations",
    tags=["simulations"],
)


@router.post(
    "/generate",
    response_model=SimulationGenerationJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def generate_simulation(
    request: GenerateSimulationRequest,
    background_tasks: BackgroundTasks,
    session_id: str = Depends(get_or_create_session_id),
    db: Session = Depends(get_db),
    _: None = Depends(require_generation_api_key),
):
    enforce_generation_limits(
        db=db,
        session_id=session_id,
    )

    job = SimulationGenerationJob(
        job_id=str(uuid.uuid4()),
        session_id=session_id,
        scenario=request.scenario,
        role=request.role,
        difficulty=request.difficulty.value,
        status=GenerationJobStatus.PENDING.value,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    background_tasks.add_task(
        run_simulation_generation_job,
        job_id=job.job_id,
    )

    return job
