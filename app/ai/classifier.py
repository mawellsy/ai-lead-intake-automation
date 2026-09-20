from typing import Any, Protocol

from pydantic import ValidationError

from app.ai.prompt import SYSTEM_PROMPT, build_user_prompt
from app.ai.schemas import LeadClassification
from app.schemas import LeadCreate


class AIProviderError(RuntimeError):
    """Raised when the external AI provider cannot return a response."""


class AIClassificationError(RuntimeError):
    """Raised when classification fails after all allowed attempts."""


class ClassificationProvider(Protocol):
    def classify(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> Any:
        ...


def _validate_response(raw_response: Any) -> LeadClassification:
    if isinstance(raw_response, str):
        return LeadClassification.model_validate_json(raw_response)

    return LeadClassification.model_validate(raw_response)


def classify_lead(
    lead: LeadCreate,
    provider: ClassificationProvider,
    *,
    max_attempts: int = 2,
) -> LeadClassification:
    if max_attempts < 1:
        raise ValueError("max_attempts must be at least 1")

    user_prompt = build_user_prompt(lead)
    last_error: Exception | None = None

    for _ in range(max_attempts):
        try:
            raw_response = provider.classify(
                system_prompt=SYSTEM_PROMPT,
                user_prompt=user_prompt,
            )
            return _validate_response(raw_response)
        except (ValidationError, AIProviderError) as exc:
            last_error = exc

    raise AIClassificationError(
        f"AI classification failed after {max_attempts} attempts"
    ) from last_error
