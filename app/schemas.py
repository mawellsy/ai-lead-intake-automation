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