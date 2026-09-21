from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class LeadCreate(BaseModel):
    """Data accepted when a new customer lead is submitted."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    full_name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=40)
    service_requested: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=2000)
    city: str | None = Field(default=None, max_length=120)
    source: str = Field(default="website", min_length=1, max_length=50)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).lower()

    @field_validator("phone", "city", mode="before")
    @classmethod
    def empty_strings_become_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("source")
    @classmethod
    def normalize_source(cls, value: str) -> str:
        return value.lower()


class LeadResponse(BaseModel):
    """Response returned after a lead submission."""

    message: str
    lead_id: str
    created: bool
    lead: LeadCreate


class LeadRead(BaseModel):
    """Stored lead returned to workflow/orchestration clients."""

    id: str
    full_name: str
    email: EmailStr
    phone: str | None = None
    service_requested: str
    message: str
    city: str | None = None
    created_at: str
    classification: str | None = None
    urgency: str | None = None
    status: str
    source: str
    ai_summary: str | None = None
    follow_up_at: str | None = None
    updated_at: str
