from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class SimulationDifficulty(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class GenerateSimulationRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    scenario: str = Field(min_length=10, max_length=500)
    role: str = Field(min_length=2, max_length=100)
    difficulty: SimulationDifficulty = SimulationDifficulty.INTERMEDIATE