from typing import Any

from pydantic import BaseModel, Field


class StoryOptionLLM(BaseModel):
    text: str = Field(description="The text of the option shown to the player.")
    nextNode: dict[str, Any] = Field(description="The next node that this option leads to.")


class StoryNodeLLM(BaseModel):
    content: str = Field(description="The main content of the story node.")
    is_ending: bool = Field(description="Indicates if this node is an ending node.")
    is_winning_ending: bool = Field(description="Indicates if this node is a winning ending node.")
    options: list[StoryOptionLLM] = Field(
        default_factory=list,
        description="A list of options available.",
    )


class StoryLLMResponse(BaseModel):
    title: str = Field(description="The title of the story.")
    rootNode: StoryNodeLLM = Field(description="The root node of the story.")
