from datetime import datetime
from enum import Enum
from uuid import UUID
from pydantic import BaseModel, ConfigDict

class GenerationJobStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class SimulationGenerationJobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    job_id: UUID
    status: GenerationJobStatus
    created_at: datetime
    simulation_id: int | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
