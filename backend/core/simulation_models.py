from pydantic import BaseModel, Field


class SimulationDecisionLLM(BaseModel):
    text: str = Field(min_length=3, max_length=300)
    target_node_key: str = Field(
        min_length=1,
        max_length=50,
        pattern=r"^[a-z0-9_]+$",
    )
    score_delta: int = Field(ge=-10, le=10)
    feedback: str = Field(min_length=10, max_length=500)


class SimulationNodeLLM(BaseModel):
    node_key: str = Field(
        min_length=1,
        max_length=50,
        pattern=r"^[a-z0-9_]+$",
    )
    content: str = Field(min_length=20, max_length=1500)
    is_root: bool = False
    is_ending: bool = False
    outcome_summary: str | None = Field(
        default=None,
        max_length=1000,
    )
    options: list[SimulationDecisionLLM] = Field(
        default_factory=list,
    )


class SimulationLLMResponse(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    nodes: list[SimulationNodeLLM] = Field(
        min_length=3,
        max_length=30,
    )