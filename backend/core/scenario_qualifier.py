from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from backend.core.config import settings
from backend.core.prompts import SCENARIO_QUALIFICATION_PROMPT
from backend.core.qualification_models import ScenarioQualificationLLM


class ScenarioNotQualifiedError(ValueError):
    """Raised when an input cannot support a balanced simulation."""


class ScenarioQualifier:
    MODEL_NAME = "gpt-4o-mini"
    MINIMUM_TOTAL_SCORE = 5

    @classmethod
    def _get_llm(cls):
        return ChatOpenAI(
            model=cls.MODEL_NAME,
            api_key=settings.OPENAI_API_KEY,
            temperature=0,
            timeout=settings.QUALIFICATION_TIMEOUT_SECONDS,
        ).with_structured_output(
            ScenarioQualificationLLM,
            method="json_schema",
            strict=True,
        )

    @classmethod
    def qualify(
        cls,
        scenario: str,
        role: str,
    ) -> ScenarioQualificationLLM:
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SCENARIO_QUALIFICATION_PROMPT),
                (
                    "human",
                    """
Scenario: {scenario}
Role: {role}
""",
                ),
            ]
        )

        formatted_prompt = prompt.invoke(
            {
                "scenario": scenario,
                "role": role,
            }
        )

        return cls._get_llm().invoke(formatted_prompt)

    @classmethod
    def passes_gate(
        cls,
        result: ScenarioQualificationLLM,
    ) -> bool:
        quality_score = cls.quality_score(result)

        return (
            quality_score >= cls.MINIMUM_TOTAL_SCORE
            and result.competing_priorities >= 1
            and result.role_agency >= 1
        )

    @staticmethod
    def quality_score(
        result: ScenarioQualificationLLM,
    ) -> int:
        return (
            result.competing_priorities
            + result.meaningful_stakes
            + result.concrete_constraints
            + result.role_agency
        )

    @classmethod
    def choose_decision_depth(
        cls,
        difficulty: str,
        result: ScenarioQualificationLLM,
    ) -> int:
        quality_score = cls.quality_score(result)

        if difficulty == "beginner":
            return 3
        if difficulty == "advanced":
            return 5 if quality_score >= 7 else 4
        return 4 if quality_score >= 6 else 3

    @classmethod
    def require_qualified(
        cls,
        scenario: str,
        role: str,
    ) -> ScenarioQualificationLLM:
        result = cls.qualify(
            scenario=scenario,
            role=role,
        )

        if cls.passes_gate(result):
            return result

        message = (
            "This scenario does not yet contain a strong decision "
            f"trade-off. {result.reason}"
        )

        if result.suggestions:
            formatted_suggestions = " ".join(
                f"{index}. {suggestion}"
                for index, suggestion in enumerate(
                    result.suggestions,
                    start=1,
                )
            )
            message = (
                f"{message} Try improving it: "
                f"{formatted_suggestions}"
            )

        raise ScenarioNotQualifiedError(message)
