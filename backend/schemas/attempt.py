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
    current_node: PlayableNodeResponse


class AlternativePathResponse(BaseModel):
    option_id: int
    option_text: str
    priorities: list[str] = Field(default_factory=list)
    immediate_feedback: str
    next_situation: str
    possible_outcomes: list[str] = Field(default_factory=list)


class DecisionFeedbackResponse(BaseModel):
    sequence_number: int
    option_id: int
    option_text: str
    priorities: list[str] = Field(default_factory=list)
    feedback: str
    alternatives: list[AlternativePathResponse] = Field(
        default_factory=list,
    )


class DecisionSubmissionResponse(BaseModel):
    decision_feedback: DecisionFeedbackResponse
    attempt: AttemptStateResponse


class DecisionProfileResponse(BaseModel):
    style: str
    top_priorities: list[str] = Field(default_factory=list)
    summary: str


class AttemptResultResponse(BaseModel):
    attempt_id: UUID
    simulation_id: int
    outcome_summary: str
    decision_profile: DecisionProfileResponse
    decisions: list[DecisionFeedbackResponse] = Field(
        default_factory=list,
    )
    completed_at: datetime
