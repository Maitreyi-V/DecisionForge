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

from backend.core.simulation_generator import SimulationGenerator
from backend.core.scenario_qualifier import ScenarioQualifier
from backend.core.qualification_models import ScenarioQualificationLLM
from backend.core.simulation_models import SimulationLLMResponse
from backend.db.database import Base, get_db
from backend.main import app
import backend.services.generation_job_service as generation_service


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
                                "priorities": [
                                    "evidence",
                                    "risk_reduction",
                                ],
                                "feedback": (
                                    "You gathered evidence before "
                                    "changing production."
                                ),
                            },
                            {
                                "text": "Restart immediately",
                                "target_node_key": "bad_end",
                                "priorities": ["delivery_speed"],
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
        with (
            patch.object(
                ScenarioQualifier,
                "require_qualified",
                return_value=ScenarioQualificationLLM(
                    competing_priorities=2,
                    meaningful_stakes=2,
                    concrete_constraints=2,
                    role_agency=2,
                    reason="The scenario contains a meaningful trade-off.",
                    suggestions=[],
                ),
            ),
            patch.object(
                SimulationGenerator,
                "generate_structure",
                return_value=self.structure,
            ),
        ):
            with TestClient(app) as client:
                create_response = client.post(
                    "/api/simulations/generate",
                    headers={
                        "X-Generation-Key": "local-development-key",
                    },
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

                self.assertNotIn("priorities", selected_option)
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
                    decision["decision_feedback"]["priorities"],
                    ["evidence", "risk_reduction"],
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
                self.assertNotIn("total_score", result)
                self.assertNotIn("score_percentage", result)
                self.assertEqual(
                    result["decision_profile"]["style"],
                    "Balanced",
                )
                self.assertEqual(
                    result["decision_profile"]["top_priorities"],
                    ["Evidence gathering", "Risk reduction"],
                )
                self.assertEqual(len(result["decisions"]), 1)
                alternatives = result["decisions"][0]["alternatives"]
                self.assertEqual(len(alternatives), 1)
                self.assertEqual(
                    alternatives[0]["option_text"],
                    "Restart immediately",
                )
                self.assertEqual(
                    alternatives[0]["possible_outcomes"],
                    ["Acting without diagnosis caused downtime."],
                )
                self.assertEqual(
                    alternatives[0]["priorities"],
                    ["delivery_speed"],
                )

    def test_generation_requires_private_key(self):
        with TestClient(app) as client:
            response = client.post(
                "/api/simulations/generate",
                json={
                    "scenario": (
                        "A risky release creates a conflict between "
                        "customer safety and an important deadline."
                    ),
                    "role": "Backend engineer",
                    "difficulty": "intermediate",
                },
            )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            response.json()["detail"],
            "Generation access denied",
        )


if __name__ == "__main__":
    unittest.main()
