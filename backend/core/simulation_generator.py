from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from core.config import settings
from core.prompts import SIMULATION_PROMPT
from core.simulation_models import SimulationLLMResponse
from services.graph_validator import validate_simulation_graph

from sqlalchemy.orm import Session

from models.simulation import DecisionOption, Simulation, SimulationNode


class SimulationGenerator:
    @classmethod
    def _get_llm(cls) -> ChatOpenAI:
        return ChatOpenAI(
            model="gpt-4-turbo",
            api_key=settings.OPENAI_API_KEY,
            temperature=0.4,
        )

    @classmethod
    def generate_structure(
        cls,
        scenario: str,
        role: str,
        difficulty: str,
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
""",
                ),
            ]
        ).partial(
            format_instructions=parser.get_format_instructions()
        )

        formatted_prompt = prompt.invoke(
            {
                "scenario": scenario,
                "role": role,
                "difficulty": difficulty,
            }
        )

        raw_response = cls._get_llm().invoke(formatted_prompt)

        response_text = raw_response.content

        simulation_structure = parser.parse(response_text)

        validate_simulation_graph(simulation_structure)

        return simulation_structure



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
                        score_delta=option_data.score_delta,
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
    ) -> Simulation:
        structure = cls.generate_structure(
            scenario=scenario,
            role=role,
            difficulty=difficulty,
        )

        return cls.save_structure(
            db=db,
            session_id=session_id,
            scenario=scenario,
            role=role,
            difficulty=difficulty,
            structure=structure,
        )