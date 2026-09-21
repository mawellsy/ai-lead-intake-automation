from openai import OpenAI

from app.ai.classifier import classify_lead
from app.ai.openai_provider import OpenAIClassificationProvider
from app.config import settings
from app.schemas import LeadCreate


def main():
    if not settings.openai_api_key:
        raise RuntimeError(
            "OPENAI_API_KEY is missing. Add it to your local .env file."
        )

    if not settings.openai_model:
        raise RuntimeError(
            "OPENAI_MODEL is missing. Add it to your local .env file."
        )

    client = OpenAI(
        api_key=settings.openai_api_key,
    )

    provider = OpenAIClassificationProvider(
        model=settings.openai_model,
        client=client,
    )

    lead = LeadCreate(
        full_name="Maya Chen",
        email="maya.chen@example.com",
        phone="+1-555-0101",
        service_requested="Plumbing repair",
        message=(
            "A pipe under the kitchen sink burst and water "
            "is actively flooding the kitchen."
        ),
        city="Riverton",
    )

    result = classify_lead(
        lead,
        provider,
        max_attempts=2,
    )

    print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
