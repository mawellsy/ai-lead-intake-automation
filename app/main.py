from fastapi import FastAPI, Response, status

from app.db.lead_repository import save_lead
from app.schemas import LeadCreate


app = FastAPI(
    title="AI Lead Intake & Follow-Up Automation",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/leads", status_code=status.HTTP_201_CREATED)
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

    return {
        "message": "Lead created",
        "lead_id": result.lead_id,
        "created": True,
        "lead": lead.model_dump(),
    }
