from types import SimpleNamespace

import pytest
from openai import OpenAIError

from app.ai.classifier import AIProviderError
from app.ai.openai_provider import OpenAIClassificationProvider
from app.ai.schemas import LeadClassification


class FakeResponses:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)

        if self.error is not None:
            raise self.error

        return self.response


class FakeClient:
    def __init__(self, responses):
        self.responses = responses


def test_openai_provider_requests_structured_output():
    classification = LeadClassification(
        classification="emergency_repair",
        urgency="critical",
        ai_summary="Active water leak requires immediate attention.",
    )

    responses = FakeResponses(
        response=SimpleNamespace(
            output_parsed=classification,
        )
    )

    provider = OpenAIClassificationProvider(
        model="test-model",
        client=FakeClient(responses),
    )

    result = provider.classify(
        system_prompt="System instructions",
        user_prompt="Lead information",
    )

    assert result == classification
    assert len(responses.calls) == 1

    call = responses.calls[0]

    assert call["model"] == "test-model"
    assert call["instructions"] == "System instructions"
    assert call["input"] == "Lead information"
    assert call["text_format"] is LeadClassification


def test_openai_provider_rejects_missing_parsed_output():
    responses = FakeResponses(
        response=SimpleNamespace(
            output_parsed=None,
        )
    )

    provider = OpenAIClassificationProvider(
        model="test-model",
        client=FakeClient(responses),
    )

    with pytest.raises(AIProviderError):
        provider.classify(
            system_prompt="System instructions",
            user_prompt="Lead information",
        )


def test_openai_error_becomes_provider_error():
    responses = FakeResponses(
        error=OpenAIError("Temporary OpenAI failure"),
    )

    provider = OpenAIClassificationProvider(
        model="test-model",
        client=FakeClient(responses),
    )

    with pytest.raises(AIProviderError):
        provider.classify(
            system_prompt="System instructions",
            user_prompt="Lead information",
        )


def test_blank_model_is_rejected():
    with pytest.raises(ValueError):
        OpenAIClassificationProvider(
            model="   ",
            client=FakeClient(FakeResponses()),
        )
