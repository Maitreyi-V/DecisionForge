import copy
import unittest

from backend.core.simulation_models import SimulationLLMResponse
from backend.services.graph_validator import (
    InvalidSimulationGraphError,
    validate_simulation_graph,
)


def decision(text: str, target: str) -> dict:
    return {
        "text": text,
        "target_node_key": target,
        "priorities": ["risk_reduction"],
        "feedback": "This choice creates a benefit and a meaningful cost.",
    }


def valid_graph_data() -> dict:
    return {
        "title": "Release Decision",
        "nodes": [
            {
                "node_key": "root",
                "content": "The team must choose how to approach a risky release.",
                "is_root": True,
                "options": [
                    decision("Run a limited release", "evidence_first"),
                    decision("Delay the release", "coordination_first"),
                ],
            },
            {
                "node_key": "evidence_first",
                "content": "Early evidence reveals both demand and reliability risk.",
                "options": [
                    decision("Expand monitoring", "final_review"),
                    decision("Restrict the audience", "stakeholder_review"),
                ],
            },
            {
                "node_key": "coordination_first",
                "content": "Stakeholders request a revised delivery commitment.",
                "options": [
                    decision("Negotiate scope", "final_review"),
                    decision("Request more testing time", "stakeholder_review"),
                ],
            },
            {
                "node_key": "final_review",
                "content": "The team has enough evidence for a final decision.",
                "options": [
                    decision("Proceed with safeguards", "stable_outcome"),
                    decision("Pause and remediate", "delayed_outcome"),
                ],
            },
            {
                "node_key": "stakeholder_review",
                "content": "Leadership weighs timing against customer impact.",
                "options": [
                    decision("Accept controlled exposure", "stable_outcome"),
                    decision("Protect reliability", "delayed_outcome"),
                ],
            },
            {
                "node_key": "stable_outcome",
                "content": "The release proceeds with controlled operational risk.",
                "is_ending": True,
                "outcome_summary": "The team balanced delivery with safeguards.",
            },
            {
                "node_key": "delayed_outcome",
                "content": "The release is delayed while the team reduces risk.",
                "is_ending": True,
                "outcome_summary": "Reliability improved at the cost of timing.",
            },
        ],
    }


class GraphValidatorTest(unittest.TestCase):
    def test_rejects_dangling_target_key(self):
        data = valid_graph_data()
        data["nodes"][0]["options"][0]["target_node_key"] = "missing_node"
        graph = SimulationLLMResponse.model_validate(data)

        with self.assertRaisesRegex(
            InvalidSimulationGraphError,
            "missing node 'missing_node'",
        ):
            validate_simulation_graph(graph)

    def test_rejects_unreachable_node(self):
        data = valid_graph_data()
        data["nodes"].append(
            {
                "node_key": "isolated_outcome",
                "content": "This outcome cannot be reached from the root node.",
                "is_ending": True,
                "outcome_summary": "This node should be rejected as unreachable.",
            }
        )
        graph = SimulationLLMResponse.model_validate(data)

        with self.assertRaisesRegex(
            InvalidSimulationGraphError,
            r"Unreachable nodes: \['isolated_outcome'\]",
        ):
            validate_simulation_graph(graph)

    def test_rejects_cycle(self):
        data = copy.deepcopy(valid_graph_data())
        data["nodes"][3]["options"][0]["target_node_key"] = "root"
        graph = SimulationLLMResponse.model_validate(data)

        with self.assertRaisesRegex(
            InvalidSimulationGraphError,
            "cannot contain cycles",
        ):
            validate_simulation_graph(graph)


if __name__ == "__main__":
    unittest.main()
