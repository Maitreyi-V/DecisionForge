import os
import unittest
from unittest.mock import patch

os.environ.update(
    {
        "DECISIONFORGE_DATABASE_URL": "sqlite:///:memory:",
        "DECISIONFORGE_API_PREFIX": "/api",
        "DECISIONFORGE_DEBUG": "False",
        "DECISIONFORGE_ALLOWED_ORIGINS": '["http://localhost:8501"]',
        "DECISIONFORGE_OPENAI_API_KEY": "test-key",
    }
)

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.simulation_generator import SimulationGenerator
from core.simulation_models import SimulationLLMResponse
from db.database import Base, get_db
from main import app
import services.generation_job_service as generation_service


class DecisionFlowTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        self.session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
        )

        Base.metadata.create_all(bind=self.engine)

        def override_get_db():
            db = self.session_factory()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db

        self.original_session_local = generation_service.SessionLocal
        generation_service.SessionLocal = self.session_factory

        self.structure = SimulationLLMResponse.model_validate(
            {
                "title": "Database Incident",
                "nodes": [
                    {
                        "node_key": "start",
                        "content": (
                            "The production database becomes slow "
                            "during peak traffic."
                        ),
                        "is_root": True,
                        "options": [
                            {
                                "text": "Inspect database metrics",
                                "target_node_key": "good_end",
                                "score_delta": 5,
                                "feedback": (
                                    "You gathered evidence before "
                                    "changing production."
                                ),
                            },
                            {
                                "text": "Restart immediately",
                                "target_node_key": "bad_end",
                                "score_delta": -5,
                                "feedback": (
                                    "You acted before identifying "
                                    "the underlying cause."
                                ),
                            },
                        ],
                    },
                    {
                        "node_key": "good_end",
                        "content": (
                            "You identify and safely resolve "
                            "the database bottleneck."
                        ),
                        "is_ending": True,
                        "outcome_summary": (
                            "Evidence-based diagnosis reduced risk."
                        ),
                    },
                    {
                        "node_key": "bad_end",
                        "content": (
                            "The restart causes an avoidable "
                            "service interruption."
                        ),
                        "is_ending": True,
                        "outcome_summary": (
                            "Acting without diagnosis caused downtime."
                        ),
                    },
                ],
            }
        )

    def tearDown(self):
        app.dependency_overrides.clear()
        generation_service.SessionLocal = self.original_session_local
        self.engine.dispose()

    def test_complete_decision_flow(self):
        with patch.object(
            SimulationGenerator,
            "generate_structure",
            return_value=self.structure,
        ):
            with TestClient(app) as client:
                create_response = client.post(
                    "/api/simulations/generate",
                    json={
                        "scenario": (
                            "A production database is slowing down "
                            "during peak traffic."
                        ),
                        "role": "Backend engineer",
                        "difficulty": "intermediate",
                    },
                )

                self.assertEqual(create_response.status_code, 202)
                job_id = create_response.json()["job_id"]

                job_response = client.get(f"/api/jobs/{job_id}")
                job = job_response.json()

                self.assertEqual(job["status"], "completed")
                self.assertIsNotNone(job["simulation_id"])

                attempt_response = client.post(
                    f"/api/simulations/{job['simulation_id']}/attempts"
                )
                attempt = attempt_response.json()

                self.assertEqual(attempt_response.status_code, 201)
                self.assertEqual(attempt["status"], "active")

                selected_option = attempt["current_node"]["options"][0]

                self.assertNotIn("score_delta", selected_option)
                self.assertNotIn("feedback", selected_option)

                decision_response = client.post(
                    (
                        f"/api/attempts/{attempt['attempt_id']}"
                        "/decisions"
                    ),
                    json={"option_id": selected_option["id"]},
                )
                decision = decision_response.json()

                self.assertEqual(decision_response.status_code, 200)
                self.assertEqual(
                    decision["decision_feedback"]["score_delta"],
                    5,
                )
                self.assertEqual(
                    decision["attempt"]["status"],
                    "completed",
                )

                result_response = client.get(
                    (
                        f"/api/attempts/{attempt['attempt_id']}"
                        "/result"
                    )
                )
                result = result_response.json()

                self.assertEqual(result_response.status_code, 200)
                self.assertEqual(result["total_score"], 5)
                self.assertEqual(len(result["decisions"]), 1)


if __name__ == "__main__":
    unittest.main()