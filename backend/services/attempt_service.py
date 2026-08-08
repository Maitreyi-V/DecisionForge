import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from models.attempt import DecisionRecord, SimulationAttempt
from models.simulation import DecisionOption, Simulation, SimulationNode

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

def start_attempt(
    db: Session,
    simulation_id: int,
    session_id: str,
) -> SimulationAttempt:
    simulation = db.get(Simulation, simulation_id)

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
        total_score=0,
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
        score_delta=option.score_delta,
    )

    attempt.decision_records.append(decision)
    attempt.total_score += option.score_delta
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