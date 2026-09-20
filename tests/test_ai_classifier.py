import pytest

from app.ai.classifier import (
    AIClassificationError,
    AIProviderError,
    classify_lead,
)
from app.ai.schemas import LeadCategory, LeadUrgency
from app.schemas import LeadCreate


class FakeProvider:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = 0

    def classify(self, *, system_prompt, user_prompt):
        self.calls += 1
        response = self.responses.pop(0)

        if isinstance(response, Exception):
            raise response

        return response


@pytest.fixture
def lead():
    return LeadCreate(
        full_name="Maya Chen",
        email="maya.chen@example.com",
        phone="+1-555-0101",
        service_requested="Plumbing repair",
        message="A pipe under the kitchen sink burst.",
        city="Riverton",
    )


def test_valid_response_is_returned(lead):
    provider = FakeProvider(
        [
            {
                "classification": "emergency_repair",
                "urgency": "critical",
                "ai_summary": "Active water leak requires immediate attention.",
            }
        ]
    )

    result = classify_lead(lead, provider)

    assert result.classification == LeadCategory.EMERGENCY_REPAIR
    assert result.urgency == LeadUrgency.CRITICAL
    assert provider.calls == 1


def test_json_string_response_is_supported(lead):
    provider = FakeProvider(
        [
            '{"classification":"standard_repair",'
            '"urgency":"normal",'
            '"ai_summary":"Customer requested a plumbing repair."}'
        ]
    )

    result = classify_lead(lead, provider)

    assert result.classification == LeadCategory.STANDARD_REPAIR
    assert result.urgency == LeadUrgency.NORMAL


def test_invalid_response_is_retried(lead):
    provider = FakeProvider(
        [
            {"classification": "invalid"},
            {
                "classification": "emergency_repair",
                "urgency": "critical",
                "ai_summary": "Active water leak requires immediate attention.",
            },
        ]
    )

    result = classify_lead(lead, provider)

    assert result.classification == LeadCategory.EMERGENCY_REPAIR
    assert provider.calls == 2


def test_repeated_invalid_responses_raise_controlled_error(lead):
    provider = FakeProvider(
        [
            {"classification": "invalid"},
            {"classification": "still_invalid"},
        ]
    )

    with pytest.raises(AIClassificationError):
        classify_lead(lead, provider)

    assert provider.calls == 2


def test_provider_failure_is_retried(lead):
    provider = FakeProvider(
        [
            AIProviderError("Temporary provider failure"),
            {
                "classification": "standard_repair",
                "urgency": "normal",
                "ai_summary": "Customer needs a plumbing repair.",
            },
        ]
    )

    result = classify_lead(lead, provider)

    assert result.classification == LeadCategory.STANDARD_REPAIR
    assert provider.calls == 2


def test_zero_attempts_is_rejected(lead):
    provider = FakeProvider([])

    with pytest.raises(ValueError):
        classify_lead(lead, provider, max_attempts=0)
