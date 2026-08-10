from enum import Enum
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AttemptStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"


class SubmitDecisionRequest(BaseModel):
    option_id: int = Field(gt=0)


class AvailableDecisionOptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str


class PlayableNodeResponse(BaseModel):
    id: int
    content: str
    is_ending: bool
    options: list[AvailableDecisionOptionResponse] = Field(
        default_factory=list,
    )


class AttemptStateResponse(BaseModel):
    attempt_id: UUID
    simulation_id: int
    status: AttemptStatus
    total_score: int
    current_node: PlayableNodeResponse


class DecisionFeedbackResponse(BaseModel):
    sequence_number: int
    option_id: int
    option_text: str
    score_delta: int
    feedback: str


class DecisionSubmissionResponse(BaseModel):
    decision_feedback: DecisionFeedbackResponse
    attempt: AttemptStateResponse


class AttemptResultResponse(BaseModel):
    attempt_id: UUID
    simulation_id: int
    outcome_summary: str
    total_score: int
    decisions: list[DecisionFeedbackResponse] = Field(
        default_factory=list,
    )
    completed_at: datetime
