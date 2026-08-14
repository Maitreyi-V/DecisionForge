from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.core.session import get_or_create_session_id
from backend.db.database import get_db
from backend.models.attempt import SimulationAttempt
from backend.schemas.attempt import (
    AlternativePathResponse,
    AttemptStateResponse,
    DecisionProfileResponse,
    PlayableNodeResponse,
    SubmitDecisionRequest,
    AttemptResultResponse,
    DecisionFeedbackResponse,
    DecisionSubmissionResponse,
)
from backend.services.attempt_service import (
    AttemptCompletedError,
    AttemptNotFoundError,
    InvalidDecisionError,
    SimulationNotFoundError,
    SimulationRootNotFoundError,
    start_attempt,
    submit_decision,
    AttemptNotCompletedError,
    AttemptResultUnavailableError,
    build_decision_profile,
    find_reachable_outcomes,
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
    profile_style, top_priorities, profile_summary = (
        build_decision_profile(attempt)
    )

    return AttemptResultResponse(
        attempt_id=attempt.attempt_id,
        simulation_id=attempt.simulation_id,
        outcome_summary=attempt.current_node.outcome_summary,
        decision_profile=DecisionProfileResponse(
            style=profile_style,
            top_priorities=top_priorities,
            summary=profile_summary,
        ),
        decisions=[
            DecisionFeedbackResponse(
                sequence_number=record.sequence_number,
                option_id=record.option_id,
                option_text=record.option.text,
                priorities=record.option.priorities,
                feedback=record.option.feedback,
                alternatives=[
                    AlternativePathResponse(
                        option_id=option.id,
                        option_text=option.text,
                        priorities=option.priorities,
                        immediate_feedback=option.feedback,
                        next_situation=option.target_node.content,
                        possible_outcomes=find_reachable_outcomes(
                            option.target_node
                        ),
                    )
                    for option in record.option.source_node.outgoing_options
                    if option.id != record.option_id
                ],
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
    response_model=DecisionSubmissionResponse,
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

    latest_decision = attempt.decision_records[-1]

    return DecisionSubmissionResponse(
        decision_feedback=DecisionFeedbackResponse(
            sequence_number=latest_decision.sequence_number,
            option_id=latest_decision.option_id,
            option_text=latest_decision.option.text,
            priorities=latest_decision.option.priorities,
            feedback=latest_decision.option.feedback,
        ),
        attempt=build_attempt_state_response(attempt),
    )

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
