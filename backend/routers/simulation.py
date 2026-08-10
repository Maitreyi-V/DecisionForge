import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from core.session import get_or_create_session_id
from db.database import get_db
from models.job import SimulationGenerationJob
from schemas.job import (
    GenerationJobStatus,
    SimulationGenerationJobResponse,
)
from schemas.simulation import GenerateSimulationRequest
from services.generation_job_service import (
    run_simulation_generation_job,
)


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
):
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