from typing import Any

from openai import OpenAI, OpenAIError

from app.ai.classifier import AIProviderError
from app.ai.schemas import LeadClassification


class OpenAIClassificationProvider:
    """OpenAI adapter for structured lead classification."""

    def __init__(
        self,
        *,
        model: str,
        client: Any | None = None,
    ):
        if not model.strip():
            raise ValueError("model must not be blank")

        self.model = model
        self.client = client or OpenAI()

    def classify(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
    ) -> LeadClassification:
        try:
            response = self.client.responses.parse(
                model=self.model,
                instructions=system_prompt,
                input=user_prompt,
                text_format=LeadClassification,
            )
        except OpenAIError as exc:
            raise AIProviderError(
                "OpenAI classification request failed"
            ) from exc

        parsed = response.output_parsed

        if parsed is None:
            raise AIProviderError(
                "OpenAI returned no parsed classification"
            )

        return parsed
