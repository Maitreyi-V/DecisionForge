from datetime import datetime, timezone
import logging 
from core.simulation_generator import SimulationGenerator
from db.database import SessionLocal
from models.job import SimulationGenerationJob
from schemas.job import GenerationJobStatus

logger = logging.getLogger(__name__)

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
            simulation = SimulationGenerator.generate_simulation(
                db=db,
                session_id=job.session_id,
                scenario=job.scenario,
                role=job.role,
                difficulty=job.difficulty,
            )

            job.simulation_id = simulation.id
            job.status = GenerationJobStatus.COMPLETED.value
            job.completed_at = datetime.now(timezone.utc)
            db.commit()

        except Exception :
            db.rollback()

            logger.exception(
                f"Simulation generation job {job_id} failed"
            )

            job = (
                db.query(SimulationGenerationJob)
                .filter(SimulationGenerationJob.job_id == job_id)
                .first()
            )

            if job is None:
                return

            job.status = GenerationJobStatus.FAILED.value
            job.error_message = (
                "Simulation generation failed. Please try again."
            )
            job.completed_at = datetime.now(timezone.utc)
            db.commit()

    finally:
        db.close()