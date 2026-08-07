import unittest

from pydantic import ValidationError

from schemas.simulation import (
    GenerateSimulationRequest,
    SimulationDifficulty,
)


class GenerateSimulationRequestTest(unittest.TestCase):
    def test_trims_input_and_uses_default_difficulty(self):
        request = GenerateSimulationRequest(
            scenario="  A production database is failing during peak traffic  ",
            role="  Backend engineer  ",
        )

        self.assertEqual(
            request.scenario,
            "A production database is failing during peak traffic",
        )
        self.assertEqual(request.role, "Backend engineer")
        self.assertEqual(
            request.difficulty,
            SimulationDifficulty.INTERMEDIATE,
        )

    def test_rejects_blank_scenario(self):
        with self.assertRaises(ValidationError):
            GenerateSimulationRequest(
                scenario="          ",
                role="Backend engineer",
            )

    def test_rejects_unknown_difficulty(self):
        with self.assertRaises(ValidationError):
            GenerateSimulationRequest(
                scenario="A production database is failing",
                role="Backend engineer",
                difficulty="impossible",
            )


if __name__ == "__main__":
    unittest.main()