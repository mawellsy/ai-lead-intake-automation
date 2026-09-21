from pydantic import BaseModel, ConfigDict


class DueFollowUpRead(BaseModel):
    id: str
    full_name: str
    email: str
    phone: str | None
    service_requested: str
    message: str
    city: str | None
    created_at: str
    classification: str
    urgency: str | None
    status: str
    ai_summary: str | None
    follow_up_at: str


class DueFollowUpEnvelope(BaseModel):
    items: list[DueFollowUpRead]


class FollowUpProcessRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_id: str
    lead_id: str
    customer_name: str
    email: str
    classification: str
    urgency: str | None
    due_at: str
    staff_notification: str
    customer_follow_up: str
    completed_at: str
