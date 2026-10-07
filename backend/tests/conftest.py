import pytest


@pytest.fixture(autouse=True)
def mock_gemini_api_key_for_tests(monkeypatch):
    """Ensure automated test runs execute deterministically against the local synthesizer

    without spending external LLM API quota or depending on external network availability.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "")
    from backend.app.services.llm_client import llm_client
    monkeypatch.setattr(llm_client, "_genai_client", None)
