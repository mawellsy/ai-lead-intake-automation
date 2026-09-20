from fastapi import FastAPI

from app.schemas import LeadCreate


app = FastAPI(
    title="AI Lead Intake & Follow-Up Automation",
    version="0.1.0",
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/leads", status_code=201)
def create_lead(lead: LeadCreate):
    return {
        "message": "Lead accepted",
        "lead": lead.model_dump(),
    }