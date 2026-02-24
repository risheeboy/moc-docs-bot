"""Tests for Hindi language support and guardrails

Tests Hindi prompts, PII redaction, and toxicity filtering.
"""

import pytest
from app.services.prompt_templates import PromptTemplateService
from app.services.guardrails import GuardrailsService
from app.models.completions import Message


@pytest.fixture
def prompt_service():
    """Prompt template service"""
    return PromptTemplateService()


@pytest.fixture
def guardrails_service():
    """Guardrails service"""
    return GuardrailsService()


def test_hindi_qa_prompt(prompt_service):
    """Test Hindi QA system prompt"""
    prompt = prompt_service.get_qa_system_prompt(language="hi")
    assert "संस्कृति मंत्रालय" in prompt
    assert "हिंदी" in prompt
    assert len(prompt) > 100


def test_english_qa_prompt(prompt_service):
    """Test English QA system prompt"""
    prompt = prompt_service.get_qa_system_prompt(language="en")
    assert "Ministry of Culture" in prompt
    assert "English" in prompt
    assert len(prompt) > 100


def test_hindi_summarization_prompt(prompt_service):
    """Test Hindi summarization prompt"""
    prompt = prompt_service.get_summarization_prompt(language="hi")
    assert "सारांश" in prompt
    assert len(prompt) > 50


def test_english_summarization_prompt(prompt_service):
    """Test English summarization prompt"""
    prompt = prompt_service.get_summarization_prompt(language="en")
    assert "summarization" in prompt.lower()
    assert len(prompt) > 50


def test_sentiment_prompt(prompt_service):
    """Test sentiment analysis prompt"""
    prompt = prompt_service.get_sentiment_prompt()
    assert "sentiment" in prompt.lower()
    assert "POSITIVE" in prompt or "positive" in prompt.lower()


def test_message_formatting(prompt_service):
    """Test message formatting for vLLM"""
    messages = [
        Message(role="system", content="You are helpful"),
        Message(role="user", content="Hello"),
        Message(role="assistant", content="Hi there")
    ]

    formatted = prompt_service.format_messages(messages)
    assert "[SYSTEM]" in formatted
    assert "[USER]" in formatted
    assert "[ASSISTANT]" in formatted


@pytest.mark.asyncio
async def test_pii_redaction_aadhaar(guardrails_service):
    """Test Aadhaar number redaction"""
    text = "My Aadhaar is 1234 5678 9012"
    redacted = guardrails_service._redact_pii(text)
    assert "[AADHAAR_REDACTED]" in redacted
    assert "1234 5678 9012" not in redacted


@pytest.mark.asyncio
async def test_pii_redaction_phone(guardrails_service):
    """Test phone number redaction"""
    text = "Call me at +919876543210"
    redacted = guardrails_service._redact_pii(text)
    assert "[PHONE_REDACTED]" in redacted
    assert "9876543210" not in redacted


@pytest.mark.asyncio
async def test_pii_redaction_email(guardrails_service):
    """Test email redaction"""
    text = "Email me at user@example.com"
    redacted = guardrails_service._redact_pii(text)
    assert "[EMAIL_REDACTED]" in redacted
    assert "user@example.com" not in redacted


@pytest.mark.asyncio
async def test_pii_redaction_pan(guardrails_service):
    """Test PAN redaction"""
    text = "PAN: ABCDE1234F"
    redacted = guardrails_service._redact_pii(text)
    assert "[PAN_REDACTED]" in redacted
    assert "ABCDE1234F" not in redacted


@pytest.mark.asyncio
async def test_pii_detection(guardrails_service):
    """Test PII detection"""
    assert guardrails_service._detect_pii("My Aadhaar is 1234 5678 9012")
    assert guardrails_service._detect_pii("Call +919876543210")
    assert guardrails_service._detect_pii("Email: test@example.com")
    assert not guardrails_service._detect_pii("This is a normal sentence")


@pytest.mark.asyncio
async def test_toxicity_detection_english(guardrails_service):
    """Test English toxicity detection"""
    assert guardrails_service._check_toxicity("This is stupid and idiotic")
    assert guardrails_service._check_toxicity("damn, this is bad")
    assert not guardrails_service._check_toxicity("This is a nice sentence")


@pytest.mark.asyncio
async def test_toxicity_detection_hindi(guardrails_service):
    """Test Hindi toxicity detection"""
    assert guardrails_service._check_toxicity("यह बहुत मादरचोद है")
    assert guardrails_service._check_toxicity("साला कमीना")
    assert not guardrails_service._check_toxicity("यह एक अच्छा वाक्य है")


@pytest.mark.asyncio
async def test_input_validation(guardrails_service):
    """Test input message validation"""
    messages = [
        Message(role="system", content="You are helpful"),
        Message(role="user", content="My Aadhaar is 1234 5678 9012")
    ]

    validated = await guardrails_service.validate_input(messages)
    assert len(validated) == 2
    assert "[AADHAAR_REDACTED]" in validated[1].content


@pytest.mark.asyncio
async def test_output_filtering(guardrails_service):
    """Test output filtering"""
    text = "The answer is 1234 5678 9012 and you can call +919876543210"
    filtered = await guardrails_service.filter_output(text)
    assert "[AADHAAR_REDACTED]" in filtered
    assert "[PHONE_REDACTED]" in filtered
