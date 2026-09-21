from fastapi import APIRouter, status

from app.db.orchestration_repository import (
    create_staff_notification,
    list_execution_events,
    list_staff_notifications,
    record_execution_event,
)
from app.orchestration_schemas import (
    ExecutionLogCreate,
    ExecutionLogEnvelope,
    ExecutionLogRead,
    StaffNotificationCreate,
    StaffNotificationRead,
)


router = APIRouter(tags=["orchestration"])


@router.post(
    "/execution-logs",
    response_model=ExecutionLogEnvelope,
    status_code=status.HTTP_201_CREATED,
)
def create_execution_log(payload: ExecutionLogCreate):
    log = record_execution_event(
        lead_id=payload.lead_id,
        workflow_name=payload.workflow_name,
        outcome=payload.outcome,
        metadata=payload.metadata,
        error_type=payload.error_type,
        error_message=payload.error_message,
    )

    return {
        "log": log,
        "passthrough": payload.passthrough,
    }


@router.get(
    "/execution-logs",
    response_model=list[ExecutionLogRead],
)
def get_execution_logs(
    lead_id: str | None = None,
):
    return list_execution_events(
        lead_id=lead_id,
    )


@router.post(
    "/staff-notifications",
    response_model=StaffNotificationRead,
    status_code=status.HTTP_201_CREATED,
)
def post_staff_notification(payload: StaffNotificationCreate):
    return create_staff_notification(
        lead_id=payload.lead_id,
        customer_name=payload.customer_name,
        urgency=payload.urgency,
        classification=payload.classification,
        message=payload.message,
    )


@router.get(
    "/staff-notifications",
    response_model=list[StaffNotificationRead],
)
def get_staff_notifications():
    return list_staff_notifications()
