from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class LeadCategory(StrEnum):
    EMERGENCY_REPAIR = "emergency_repair"
    STANDARD_REPAIR = "standard_repair"
    INSTALLATION = "installation"
    MAINTENANCE = "maintenance"
    QUOTE_REQUEST = "quote_request"
    IRRELEVANT = "irrelevant"


class LeadUrgency(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class LeadClassification(BaseModel):
    """Validated structured output expected from the AI classifier."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    classification: LeadCategory
    urgency: LeadUrgency
    ai_summary: str = Field(min_length=1, max_length=500)
