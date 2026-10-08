from unittest.mock import MagicMock, patch
import pytest
from backend.app.core.config import Settings, _fetch_gcp_secret


def test_settings_default_email_is_none_or_env(monkeypatch):
    """Verify that Settings default definition has no hardcoded email."""
    # When no env var or .env provides it, default should be None
    monkeypatch.delenv("NOTIFICATION_EMAIL_TO", raising=False)
    monkeypatch.setattr("backend.app.core.config._fetch_gcp_secret", lambda secret_id, project_id=None: None)

    s = Settings(_env_file=None)
    assert s.NOTIFICATION_EMAIL_TO is None
    assert s.NOTIFICATION_EMAIL_SECRET_ID == "notification-email"


def test_settings_loads_email_from_environment(monkeypatch):
    """Verify that Settings properly reads NOTIFICATION_EMAIL_TO from env / .env."""
    test_email = "test-alerts@domain.example"
    monkeypatch.setenv("NOTIFICATION_EMAIL_TO", test_email)

    s = Settings(_env_file=None)
    assert s.NOTIFICATION_EMAIL_TO == test_email


def test_settings_fetches_from_gcp_secret_manager_when_not_in_env(monkeypatch):
    """Verify that Settings queries GCP Secret Manager if NOTIFICATION_EMAIL_TO is unset."""
    monkeypatch.delenv("NOTIFICATION_EMAIL_TO", raising=False)
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project-123")

    mock_secret_val = "gcp-secret-alerts@domain.example"
    with patch("backend.app.core.config._fetch_gcp_secret", return_value=mock_secret_val) as mock_fetch:
        s = Settings(_env_file=None)
        mock_fetch.assert_any_call(secret_id="notification-email", project_id="test-project-123")
        assert s.NOTIFICATION_EMAIL_TO == mock_secret_val


def test_fetch_gcp_secret_handles_exceptions_gracefully(monkeypatch):
    """Verify _fetch_gcp_secret returns None without raising if Secret Manager fails."""
    monkeypatch.setenv("GCP_PROJECT_ID", "test-project-123")

    with patch("google.cloud.secretmanager.SecretManagerServiceClient", side_effect=Exception("API unavailable")):
        val = _fetch_gcp_secret("test-secret", project_id="test-project-123")
        assert val is None


def test_fetch_gcp_secret_success(monkeypatch):
    """Verify _fetch_gcp_secret correctly parses payload from Secret Manager."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.payload.data = b"secret-destination@example.com\n"
    mock_client.access_secret_version.return_value = mock_response

    with patch("google.cloud.secretmanager.SecretManagerServiceClient", return_value=mock_client):
        val = _fetch_gcp_secret("my-secret", project_id="my-proj")
        assert val == "secret-destination@example.com"
        mock_client.access_secret_version.assert_called_once_with(
            request={"name": "projects/my-proj/secrets/my-secret/versions/latest"}
        )
