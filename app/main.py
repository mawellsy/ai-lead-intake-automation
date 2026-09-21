from fastapi import FastAPI, HTTPException, Response, status
from openai import OpenAI

from app.ai.openai_provider import OpenAIClassificationProvider
from app.ai.service import classify_saved_lead
from app.config import settings
from app.db.lead_repository import (
    get_lead,
    mark_lead_for_review,
    save_lead,
)
from app.schemas import LeadCreate, LeadRead, LeadResponse


app = FastAPI(
    title="AI Lead Intake & Follow-Up Automation",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


def classify_new_lead(
    lead_id: str,
    lead: LeadCreate,
):
    """Classify a newly persisted lead without risking loss of the request."""

    if not settings.openai_api_key or not settings.openai_model:
        mark_lead_for_review(lead_id)
        return None

    client = OpenAI(
        api_key=settings.openai_api_key,
    )

    provider = OpenAIClassificationProvider(
        model=settings.openai_model,
        client=client,
    )

    return classify_saved_lead(
        lead_id,
        lead,
        provider,
    )


@app.get("/leads/{lead_id}", response_model=LeadRead)
def get_lead_by_id(lead_id: str):
    lead = get_lead(lead_id)

    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    return lead


@app.post(
    "/leads",
    status_code=status.HTTP_201_CREATED,
    response_model=LeadResponse,
    responses={
        status.HTTP_200_OK: {
            "model": LeadResponse,
            "description": "Duplicate lead already exists",
        }
    },
)
def create_lead(lead: LeadCreate, response: Response):
    result = save_lead(lead)

    if not result.created:
        response.status_code = status.HTTP_200_OK
        return {
            "message": "Duplicate lead ignored",
            "lead_id": result.lead_id,
            "created": False,
            "lead": lead.model_dump(),
        }

    classify_new_lead(
        result.lead_id,
        lead,
    )

    return {
        "message": "Lead created",
        "lead_id": result.lead_id,
        "created": True,
        "lead": lead.model_dump(),
    }
