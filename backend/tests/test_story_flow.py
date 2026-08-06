import json
import os
import unittest
from unittest.mock import patch

os.environ.update(
    {
        "DATABASE_URL": "sqlite:///:memory:",
        "API_PREFIX": "/api",
        "DEBUG": "False",
        "ALLOWED_ORIGINS": '["http://localhost:3000"]',
        "OPENAI_API_KEY": "test-key",
    }
)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.story_generator import StoryGenerator
from db.database import Base
from models.story import StoryNode
from routers.story import build_complete_story_tree


class FakeLLMResponse:
    content = json.dumps(
        {
            "title": "Test Adventure",
            "rootNode": {
                "content": "Choose a path.",
                "is_ending": False,
                "is_winning_ending": False,
                "options": [
                    {
                        "text": "Take the safe path",
                        "nextNode": {
                            "content": "You reached safety.",
                            "is_ending": True,
                            "is_winning_ending": True,
                            "options": [],
                        },
                    }
                ],
            },
        }
    )


class FakeLLM:
    def invoke(self, prompt):
        return FakeLLMResponse()


class StoryFlowTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_generate_and_build_complete_story(self):
        with patch.object(StoryGenerator, "_get_llm", return_value=FakeLLM()):
            story = StoryGenerator.generate_story(
                self.db,
                session_id="test-session",
                theme="test-theme",
            )

        nodes = (
            self.db.query(StoryNode)
            .filter(StoryNode.story_id == story.id)
            .all()
        )
        response = build_complete_story_tree(self.db, story)

        self.assertEqual(story.title, "Test Adventure")
        self.assertEqual(len(nodes), 2)
        self.assertEqual(response.root_node.options[0].node_id, nodes[1].id)
        self.assertEqual(set(response.all_nodes), {node.id for node in nodes})


if __name__ == "__main__":
    unittest.main()
