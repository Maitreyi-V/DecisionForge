from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from core.session import get_or_create_session_id
from db.database import get_db
from models.attempt import SimulationAttempt
from schemas.attempt import (
    AttemptStateResponse,
    PlayableNodeResponse,
    SubmitDecisionRequest,
    AttemptResultResponse,
    DecisionFeedbackResponse,
)
from services.attempt_service import (
    AttemptCompletedError,
    AttemptNotFoundError,
    InvalidDecisionError,
    SimulationNotFoundError,
    SimulationRootNotFoundError,
    start_attempt,
    submit_decision,
    AttemptNotCompletedError,
    AttemptResultUnavailableError,
    get_completed_attempt,
)


router = APIRouter(tags=["attempts"])


def build_attempt_state_response(
    attempt: SimulationAttempt,
) -> AttemptStateResponse:
    node = attempt.current_node

    return AttemptStateResponse(
        attempt_id=attempt.attempt_id,
        simulation_id=attempt.simulation_id,
        status=attempt.status,
        total_score=attempt.total_score,
        current_node=PlayableNodeResponse(
            id=node.id,
            content=node.content,
            is_ending=node.is_ending,
            options=node.outgoing_options,
        ),
    )

def build_attempt_result_response(
    attempt: SimulationAttempt,
) -> AttemptResultResponse:
    return AttemptResultResponse(
        attempt_id=attempt.attempt_id,
        simulation_id=attempt.simulation_id,
        outcome_summary=attempt.current_node.outcome_summary,
        total_score=attempt.total_score,
        decisions=[
            DecisionFeedbackResponse(
                sequence_number=record.sequence_number,
                option_id=record.option_id,
                option_text=record.option.text,
                score_delta=record.score_delta,
                feedback=record.option.feedback,
            )
            for record in attempt.decision_records
        ],
        completed_at=attempt.completed_at,
    )


@router.post(
    "/simulations/{simulation_id}/attempts",
    response_model=AttemptStateResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_attempt(
    simulation_id: int,
    session_id: str = Depends(get_or_create_session_id),
    db: Session = Depends(get_db),
):
    try:
        attempt = start_attempt(
            db=db,
            simulation_id=simulation_id,
            session_id=session_id,
        )
    except SimulationNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except SimulationRootNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return build_attempt_state_response(attempt)


@router.post(
    "/attempts/{attempt_id}/decisions",
    response_model=AttemptStateResponse,
)
def choose_option(
    attempt_id: UUID,
    request: SubmitDecisionRequest,
    session_id: str = Depends(get_or_create_session_id),
    db: Session = Depends(get_db),
):
    try:
        attempt = submit_decision(
            db=db,
            attempt_id=str(attempt_id),
            session_id=session_id,
            option_id=request.option_id,
        )
    except AttemptNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (AttemptCompletedError, InvalidDecisionError) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return build_attempt_state_response(attempt)

@router.get(
    "/attempts/{attempt_id}/result",
    response_model=AttemptResultResponse,
)
def get_attempt_result(
    attempt_id: UUID,
    session_id: str = Depends(get_or_create_session_id),
    db: Session = Depends(get_db),
):
    try:
        attempt = get_completed_attempt(
            db=db,
            attempt_id=str(attempt_id),
            session_id=session_id,
        )
    except AttemptNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except AttemptNotCompletedError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except AttemptResultUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    return build_attempt_result_response(attempt)