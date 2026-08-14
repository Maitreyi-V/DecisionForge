from pydantic import BaseModel, Field


class ScenarioQualificationLLM(BaseModel):
    competing_priorities: int = Field(ge=0, le=2)
    meaningful_stakes: int = Field(ge=0, le=2)
    concrete_constraints: int = Field(ge=0, le=2)
    role_agency: int = Field(ge=0, le=2)

    reason: str = Field(min_length=10, max_length=500)

    suggestions: list[str] = Field(
        min_length=0,
        max_length=3,
    )
