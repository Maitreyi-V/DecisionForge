import uuid
from collections import Counter
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.models.attempt import DecisionRecord, SimulationAttempt
from backend.models.simulation import DecisionOption, Simulation, SimulationNode


class SimulationNotFoundError(Exception):
    pass


class SimulationRootNotFoundError(Exception):
    pass


class AttemptNotFoundError(Exception):
    pass


class AttemptCompletedError(Exception):
    pass


class InvalidDecisionError(Exception):
    pass


class AttemptNotCompletedError(Exception):
    pass


class AttemptResultUnavailableError(Exception):
    pass


PRIORITY_LABELS = {
    "delivery_speed": "Delivery speed",
    "risk_reduction": "Risk reduction",
    "evidence": "Evidence gathering",
    "stakeholder_alignment": "Stakeholder alignment",
    "customer_impact": "Customer impact",
    "team_sustainability": "Team sustainability",
    "resource_efficiency": "Resource efficiency",
}

DECISION_STYLES = {
    "delivery_speed": "Momentum-focused",
    "risk_reduction": "Risk-aware",
    "evidence": "Evidence-led",
    "stakeholder_alignment": "Collaborative",
    "customer_impact": "Customer-centered",
    "team_sustainability": "Team-conscious",
    "resource_efficiency": "Resource-conscious",
}


def build_decision_profile(
    attempt: SimulationAttempt,
) -> tuple[str, list[str], str]:
    priority_counts: Counter[str] = Counter()

    for record in attempt.decision_records:
        priority_counts.update(record.option.priorities or [])

    if not priority_counts:
        return (
            "Context-dependent",
            [],
            "Your choices were shaped by the specific situation rather "
            "than one repeated priority.",
        )

    ranked_priorities = priority_counts.most_common(3)
    top_priority_keys = [key for key, _ in ranked_priorities]
    top_priority_labels = [
        PRIORITY_LABELS[key]
        for key in top_priority_keys
    ]
    has_tied_top_priorities = (
        len(ranked_priorities) > 1
        and ranked_priorities[0][1] == ranked_priorities[1][1]
    )
    style = (
        "Balanced"
        if has_tied_top_priorities
        else DECISION_STYLES[top_priority_keys[0]]
    )

    if len(top_priority_labels) == 1:
        priority_text = top_priority_labels[0]
    else:
        priority_text = (
            ", ".join(top_priority_labels[:-1])
            + f" and {top_priority_labels[-1]}"
        )

    summary = (
        f"Across this path, your choices most often emphasized "
        f"{priority_text}. This describes the trade-offs you selected; "
        "it is not a right-or-wrong rating."
    )
    return style, top_priority_labels, summary


def find_reachable_outcomes(
    start_node: SimulationNode,
) -> list[str]:
    outcomes: list[str] = []
    visited: set[int] = set()

    def visit(node: SimulationNode) -> None:
        if node.id in visited:
            return

        visited.add(node.id)

        if node.is_ending:
            if node.outcome_summary:
                outcomes.append(node.outcome_summary)
            return

        for option in node.outgoing_options:
            visit(option.target_node)

    visit(start_node)
    return list(dict.fromkeys(outcomes))


def start_attempt(
    db: Session,
    simulation_id: int,
    session_id: str,
) -> SimulationAttempt:
    simulation = (
        db.query(Simulation)
        .filter(
            Simulation.id == simulation_id,
            Simulation.session_id == session_id,
        )
        .first()
    )

    if simulation is None:
        raise SimulationNotFoundError(
            f"Simulation {simulation_id} was not found"
        )

    root_node = (
        db.query(SimulationNode)
        .filter(
            SimulationNode.simulation_id == simulation_id,
            SimulationNode.is_root.is_(True),
        )
        .first()
    )

    if root_node is None:
        raise SimulationRootNotFoundError(
            f"Simulation {simulation_id} has no root node"
        )

    attempt = SimulationAttempt(
        attempt_id=str(uuid.uuid4()),
        simulation=simulation,
        session_id=session_id,
        current_node=root_node,
        status="active",
    )

    db.add(attempt)

    try:
        db.commit()
        db.refresh(attempt)
    except Exception:
        db.rollback()
        raise

    return attempt

def submit_decision(
    db: Session,
    attempt_id: str,
    session_id: str,
    option_id: int,
) -> SimulationAttempt:
    attempt = (
        db.query(SimulationAttempt)
        .filter(
            SimulationAttempt.attempt_id == attempt_id,
            SimulationAttempt.session_id == session_id,
        )
        .first()
    )

    if attempt is None:
        raise AttemptNotFoundError(
            f"Attempt {attempt_id} was not found"
        )

    if attempt.status != "active":
        raise AttemptCompletedError(
            f"Attempt {attempt_id} is already completed"
        )

    option = db.get(DecisionOption, option_id)

    if (
        option is None
        or option.source_node_id != attempt.current_node_id
        or option.target_node.simulation_id != attempt.simulation_id
    ):
        raise InvalidDecisionError(
            "This option is not available at the current node"
        )

    decision = DecisionRecord(
        option=option,
        sequence_number=len(attempt.decision_records) + 1,
    )

    attempt.decision_records.append(decision)
    attempt.current_node = option.target_node

    if attempt.current_node.is_ending:
        attempt.status = "completed"
        attempt.completed_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(attempt)
    except Exception:
        db.rollback()
        raise

    return attempt


def get_completed_attempt(
    db: Session,
    attempt_id: str,
    session_id: str,
) -> SimulationAttempt:
    attempt = (
        db.query(SimulationAttempt)
        .filter(
            SimulationAttempt.attempt_id == attempt_id,
            SimulationAttempt.session_id == session_id,
        )
        .first()
    )

    if attempt is None:
        raise AttemptNotFoundError(
            f"Attempt {attempt_id} was not found"
        )

    if attempt.status != "completed":
        raise AttemptNotCompletedError(
            f"Attempt {attempt_id} is not completed"
        )

    if (
        attempt.current_node.outcome_summary is None
        or attempt.completed_at is None
    ):
        raise AttemptResultUnavailableError(
            f"Attempt {attempt_id} has incomplete result data"
        )

    return attempt
