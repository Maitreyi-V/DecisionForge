from sqlalchemy.orm import Session

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from core.config import settings
from core.models import StoryLLMResponse, StoryNodeLLM
from core.prompts import STORY_PROMPT
from models.story import Story, StoryNode


class StoryGenerator:
    @classmethod
    def _get_llm(cls) -> ChatOpenAI:
        return ChatOpenAI(
            model="gpt-4-turbo",
            api_key=settings.OPENAI_API_KEY,
        )

    @classmethod
    def generate_story(
        cls,
        db: Session,
        session_id: str,
        theme: str = "fantasy",
    ) -> Story:
        llm = cls._get_llm()
        story_parser = PydanticOutputParser(pydantic_object=StoryLLMResponse)
        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    STORY_PROMPT,
                ),
                (
                    "human",
                    "Generate a story with the theme: {theme}",
                ),
            ]
        ).partial(format_instructions=story_parser.get_format_instructions())

        raw_response = llm.invoke(prompt.invoke({"theme": theme}))
        response_text = raw_response
        if hasattr(response_text, "content"):
            response_text = response_text.content

        story_structure = story_parser.parse(response_text)

        story_db = Story(title=story_structure.title, session_id=session_id)
        db.add(story_db)
        db.flush()

        root_node_data = story_structure.rootNode
        if isinstance(root_node_data, dict):
            root_node_data = StoryNodeLLM.model_validate(root_node_data)

        cls._process_story_node(db, story_db.id, root_node_data, is_root=True)

        db.commit()
        db.refresh(story_db)
        return story_db

    @classmethod
    def _process_story_node(
        cls,
        db: Session,
        story_id: int,
        node_data: StoryNodeLLM,
        is_root: bool = False,
    ) -> StoryNode:
        node = StoryNode(
            story_id=story_id,
            content=node_data.content,
            is_root=is_root,
            is_ending=node_data.is_ending,
            is_winning_ending=node_data.is_winning_ending,
            options=[],
        )

        db.add(node)
        db.flush()

        if not node.is_ending and node_data.options:
            options_list = []
            for option_data in node_data.options:
                next_node = option_data.nextNode

                if isinstance(next_node, dict):
                    next_node = StoryNodeLLM.model_validate(next_node)

                child_node = cls._process_story_node(db, story_id, next_node)
                options_list.append(
                    {
                        "text": option_data.text,
                        "node_id": child_node.id,
                    }
                )
            node.options = options_list

        db.flush()
        return node
