from fastapi import APIRouter, HTTPException, status

from app.db.follow_up_repository import (
    list_due_follow_ups,
    process_due_follow_up,
)
from app.follow_up_schemas import (
    DueFollowUpEnvelope,
    FollowUpProcessRead,
)


router = APIRouter(
    prefix="/follow-ups",
    tags=["follow-ups"],
)


@router.get(
    "/due",
    response_model=DueFollowUpEnvelope,
)
def get_due_follow_ups():
    return {
        "items": list_due_follow_ups(),
    }


@router.post(
    "/{lead_id}/process",
    response_model=FollowUpProcessRead,
)
def process_follow_up(lead_id: str):
    try:
        return process_due_follow_up(lead_id)
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
