from langchain_core.exceptions import OutputParserException
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from backend.core.config import settings
from backend.core.prompts import SIMULATION_PROMPT
from backend.core.simulation_models import SimulationLLMResponse
from backend.services.graph_validator import (
    InvalidSimulationGraphError,
    validate_simulation_graph,
)

from sqlalchemy.orm import Session

from backend.models.simulation import DecisionOption, Simulation, SimulationNode


class SimulationGenerator:
    MAX_GENERATION_ATTEMPTS = 2

    @classmethod
    def _get_llm(cls) -> ChatOpenAI:
        return ChatOpenAI(
            model="gpt-4-turbo",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.4,
            timeout=settings.GENERATION_REQUEST_TIMEOUT_SECONDS,
        )

    @staticmethod
    def _build_topology_instructions(
        decision_depth: int,
    ) -> str:
        if decision_depth not in {3, 4, 5}:
            raise ValueError("Decision depth must be between 3 and 5")

        layers: list[list[str]] = [["root"]]
        layers.extend(
            [f"step_{step}_a", f"step_{step}_b"]
            for step in range(2, decision_depth + 1)
        )
        layers.append(["ending_a", "ending_b"])

        required_keys = [
            key
            for layer in layers
            for key in layer
        ]
        instructions = [
            "Required topology:",
            f"- Create exactly {len(required_keys)} nodes.",
            f"- Required node keys: {', '.join(required_keys)}.",
            "- root is the only root node.",
            "- ending_a and ending_b are the only ending nodes.",
        ]

        for current_layer, next_layer in zip(layers, layers[1:]):
            instructions.append(
                "- Options from "
                f"{', '.join(current_layer)} may target only "
                f"{', '.join(next_layer)}."
            )

        instructions.append(
            f"- Every path contains exactly {decision_depth} decisions."
        )
        return "\n".join(instructions)

    @staticmethod
    def _validate_required_topology(
        structure: SimulationLLMResponse,
        decision_depth: int,
    ) -> None:
        layers: list[list[str]] = [["root"]]
        layers.extend(
            [f"step_{step}_a", f"step_{step}_b"]
            for step in range(2, decision_depth + 1)
        )
        layers.append(["ending_a", "ending_b"])

        expected_keys = {
            key
            for layer in layers
            for key in layer
        }
        actual_keys = {
            node.node_key
            for node in structure.nodes
        }

        if actual_keys != expected_keys:
            missing = sorted(expected_keys - actual_keys)
            extra = sorted(actual_keys - expected_keys)
            raise InvalidSimulationGraphError(
                "Topology keys do not match the required blueprint; "
                f"missing={missing}, extra={extra}"
            )

        allowed_targets = {
            source_key: set(next_layer)
            for current_layer, next_layer in zip(layers, layers[1:])
            for source_key in current_layer
        }

        for node in structure.nodes:
            allowed = allowed_targets.get(node.node_key, set())
            for option in node.options:
                if option.target_node_key not in allowed:
                    raise InvalidSimulationGraphError(
                        f"Option in '{node.node_key}' must target one of "
                        f"{sorted(allowed)}, not "
                        f"'{option.target_node_key}'"
                    )

    @classmethod
    def generate_structure(
        cls,
        scenario: str,
        role: str,
        difficulty: str,
        decision_depth: int,
    ) -> SimulationLLMResponse:
        parser = PydanticOutputParser(
            pydantic_object=SimulationLLMResponse
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SIMULATION_PROMPT),
                (
                    "human",
                    """
Scenario: {scenario}
Role: {role}
Difficulty: {difficulty}
{topology_instructions}
{correction_guidance}
""",
                ),
            ]
        ).partial(
            format_instructions=parser.get_format_instructions()
        )

        previous_error: Exception | None = None
        topology_instructions = cls._build_topology_instructions(
            decision_depth
        )

        for attempt_number in range(cls.MAX_GENERATION_ATTEMPTS):
            correction_guidance = ""
            if previous_error is not None:
                correction_guidance = (
                    "Your previous graph was rejected for this reason: "
                    f"{str(previous_error)[:1500]}\n"
                    "Regenerate the complete graph and correct every listed "
                    "problem. Include every node referenced by an option."
                )

            formatted_prompt = prompt.invoke(
                {
                    "scenario": scenario,
                    "role": role,
                    "difficulty": difficulty,
                    "topology_instructions": topology_instructions,
                    "correction_guidance": correction_guidance,
                }
            )

            raw_response = cls._get_llm().invoke(formatted_prompt)

            try:
                simulation_structure = parser.parse(raw_response.content)
                validate_simulation_graph(simulation_structure)
                cls._validate_required_topology(
                    simulation_structure,
                    decision_depth,
                )
                return simulation_structure
            except (
                InvalidSimulationGraphError,
                OutputParserException,
            ) as error:
                previous_error = error

        if previous_error is None:
            raise RuntimeError("Simulation generation produced no result")

        raise previous_error



    @classmethod
    def save_structure(
        cls,
        db: Session,
        session_id: str,
        scenario: str,
        role: str,
        difficulty: str,
        structure: SimulationLLMResponse,
    ) -> Simulation:
        try:
            simulation = Simulation(
                title=structure.title,
                scenario=scenario,
                role=role,
                difficulty=difficulty,
                session_id=session_id,
            )

            db.add(simulation)
            db.flush()

            node_by_key: dict[str, SimulationNode] = {}

            for node_data in structure.nodes:
                node = SimulationNode(
                    simulation_id=simulation.id,
                    content=node_data.content,
                    is_root=node_data.is_root,
                    is_ending=node_data.is_ending,
                    outcome_summary=node_data.outcome_summary,
                )

                db.add(node)
                node_by_key[node_data.node_key] = node

            db.flush()

            for node_data in structure.nodes:
                source_node = node_by_key[node_data.node_key]

                for option_data in node_data.options:
                    target_node = node_by_key[
                        option_data.target_node_key
                    ]

                    option = DecisionOption(
                        source_node_id=source_node.id,
                        target_node_id=target_node.id,
                        text=option_data.text,
                        priorities=list(option_data.priorities),
                        feedback=option_data.feedback,
                    )

                    db.add(option)

            db.flush()

            return simulation

        except Exception:
            db.rollback()
            raise

    @classmethod
    def generate_simulation(
        cls,
        db: Session,
        session_id: str,
        scenario: str,
        role: str,
        difficulty: str,
        decision_depth: int,
    ) -> Simulation:
        structure = cls.generate_structure(
            scenario=scenario,
            role=role,
            difficulty=difficulty,
            decision_depth=decision_depth,
        )

        return cls.save_structure(
            db=db,
            session_id=session_id,
            scenario=scenario,
            role=role,
            difficulty=difficulty,
            structure=structure,
        )
