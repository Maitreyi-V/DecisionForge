from datetime import datetime, timezone
import logging

from backend.core.scenario_qualifier import (
    ScenarioNotQualifiedError,
    ScenarioQualifier,
)
from backend.core.config import settings
from backend.core.simulation_generator import SimulationGenerator
from backend.db.database import SessionLocal
from backend.models.job import SimulationGenerationJob
from backend.schemas.job import GenerationJobStatus

logger = logging.getLogger(__name__)


def expire_stale_generation_job(
    db,
    job: SimulationGenerationJob,
) -> SimulationGenerationJob:
    if job.status not in {
        GenerationJobStatus.PENDING.value,
        GenerationJobStatus.IN_PROGRESS.value,
    }:
        return job

    created_at = job.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    age_seconds = (
        datetime.now(timezone.utc) - created_at
    ).total_seconds()

    if age_seconds <= settings.GENERATION_JOB_TIMEOUT_SECONDS:
        return job

    job.status = GenerationJobStatus.FAILED.value
    job.error_message = (
        "Generation timed out or the worker restarted. Please try again."
    )
    job.completed_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(job)
    return job


def _mark_job_failed(
    db,
    job_id: str,
    error_message: str,
) -> None:
    job = (
        db.query(SimulationGenerationJob)
        .filter(SimulationGenerationJob.job_id == job_id)
        .first()
    )

    if job is None:
        return

    job.status = GenerationJobStatus.FAILED.value
    job.error_message = error_message
    job.completed_at = datetime.now(timezone.utc)
    db.commit()


def run_simulation_generation_job(job_id: str) -> None:
    db = SessionLocal()

    try:
        job = (
            db.query(SimulationGenerationJob)
            .filter(SimulationGenerationJob.job_id == job_id)
            .first()
        )

        if job is None:
            return

        job.status = GenerationJobStatus.IN_PROGRESS.value
        db.commit()

        try:
            qualification = ScenarioQualifier.require_qualified(
                scenario=job.scenario,
                role=job.role,
            )
            decision_depth = ScenarioQualifier.choose_decision_depth(
                difficulty=job.difficulty,
                result=qualification,
            )

            simulation = SimulationGenerator.generate_simulation(
                db=db,
                session_id=job.session_id,
                scenario=job.scenario,
                role=job.role,
                difficulty=job.difficulty,
                decision_depth=decision_depth,
            )

            job.simulation_id = simulation.id
            job.status = GenerationJobStatus.COMPLETED.value
            job.completed_at = datetime.now(timezone.utc)
            db.commit()

        except ScenarioNotQualifiedError as exc:
            db.rollback()
            logger.info(
                "Simulation generation job %s rejected by qualification gate",
                job_id,
            )
            _mark_job_failed(
                db=db,
                job_id=job_id,
                error_message=str(exc),
            )

        except Exception:
            db.rollback()

            logger.exception(
                "Simulation generation job %s failed",
                job_id,
            )
            _mark_job_failed(
                db=db,
                job_id=job_id,
                error_message=(
                    "Simulation generation failed. Please try again."
                ),
            )

    finally:
        db.close()
