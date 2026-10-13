"""Tests for Question Logging and Log/Account Querying."""

import logging
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock
import pytest
from httpx import AsyncClient, ASGITransport

from backend.app.main import app
from backend.app.core.security import UserIdentity
from backend.app.api.v1.chat import format_requester
from scripts.query_logs import extract_question_info, parse_since as parse_log_since
from scripts.query_accounts import (
    parse_since as parse_account_since,
    get_account_creation_time,
    parse_iso_datetime
)


def test_format_requester():
    """Verify format_requester displays email/uid for authenticated users and IP for anonymous."""
    # Authenticated with email
    auth_user = UserIdentity(
        is_authenticated=True,
        uid="user123",
        email="recruiter@tech.com",
        client_ip="198.51.100.1"
    )
    assert format_requester(auth_user) == "authenticated user 'recruiter@tech.com' (IP: 198.51.100.1)"

    # Authenticated without email
    auth_no_email = UserIdentity(
        is_authenticated=True,
        uid="gh-user-99",
        client_ip="198.51.100.2"
    )
    assert format_requester(auth_no_email) == "authenticated user 'gh-user-99' (IP: 198.51.100.2)"

    # Anonymous
    anon_user = UserIdentity(
        is_authenticated=False,
        uid="anon:198.51.100.3",
        client_ip="198.51.100.3"
    )
    assert format_requester(anon_user) == "anonymous IP '198.51.100.3'"


@pytest.mark.asyncio
async def test_chat_stream_logs_anonymous_question(caplog):
    """Verify info level logging logs anonymous question and IP."""
    transport = ASGITransport(app=app)
    caplog.set_level(logging.INFO)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {
            "X-Client-Verification": "portfolio-client-v1",
            "X-Real-IP": "203.0.113.195"
        }
        resp = await ac.post(
            "/api/v1/chat/stream",
            json={"question": "What is Brandon's experience with Kafka?", "messages": []},
            headers=headers
        )
        assert resp.status_code == 200

    # Verify that the question and IP were logged at INFO level
    expected_log_found = any(
        "Question asked by anonymous IP '203.0.113.195': What is Brandon's experience with Kafka?" in record.message
        for record in caplog.records
        if record.levelno == logging.INFO
    )
    assert expected_log_found, "Expected INFO level question log for anonymous user was not found"


@pytest.mark.asyncio
async def test_chat_stream_logs_authenticated_question(caplog):
    """Verify info level logging logs authenticated user identity and question."""
    from backend.app.core.security import get_current_user_optional

    auth_user = UserIdentity(
        is_authenticated=True,
        uid="recruiter-demo",
        email="recruiter-demo@example.com",
        name="Recruiter Demo",
        client_ip="198.51.100.42"
    )
    app.dependency_overrides[get_current_user_optional] = lambda: auth_user
    transport = ASGITransport(app=app)
    caplog.set_level(logging.INFO)

    try:
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            headers = {
                "X-Client-Verification": "portfolio-client-v1",
                "X-Real-IP": "198.51.100.42"
            }
            resp = await ac.post(
                "/api/v1/chat/stream",
                json={"question": "Where did Brandon work previously?", "messages": []},
                headers=headers
            )
            assert resp.status_code == 200

        expected_log_found = any(
            "Question asked by authenticated user 'recruiter-demo@example.com' (IP: 198.51.100.42): Where did Brandon work previously?" in record.message
            for record in caplog.records
            if record.levelno == logging.INFO
        )
        assert expected_log_found, "Expected INFO level question log for authenticated user was not found"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_contact_form_logs_submitted_question(caplog):
    """Verify info level logging on contact form submission."""
    transport = ASGITransport(app=app)
    caplog.set_level(logging.INFO)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        headers = {
            "X-Client-Verification": "portfolio-client-v1",
            "X-Real-IP": "192.0.2.77"
        }
        resp = await ac.post(
            "/api/v1/leads/contact",
            json={
                "name": "Alex Recruiter",
                "email": "alex@hiring.com",
                "question": "Are you interested in a Lead Platform Engineer role?"
            },
            headers=headers
        )
        assert resp.status_code == 200

    expected_log_found = any(
        "Question asked via contact form by authenticated user 'alex@hiring.com' (IP: 192.0.2.77): Are you interested in a Lead Platform Engineer role?" in record.message
        for record in caplog.records
        if record.levelno == logging.INFO
    )
    assert expected_log_found, "Expected INFO level log for contact submission was not found"



def test_extract_question_info_from_logs():
    """Verify extraction of requester and question from log text patterns."""
    # Standard format
    log1 = "2026-10-13T12:00:00Z [INFO] Question asked by authenticated user 'alex@company.com' (IP: 1.2.3.4): Tell me about Kubernetes."
    q1 = extract_question_info(log1)
    assert q1 is not None
    assert q1["requester"] == "authenticated user 'alex@company.com' (IP: 1.2.3.4)"
    assert q1["question"] == "Tell me about Kubernetes."

    # Anonymous standard format
    log2 = "Question asked by anonymous IP '5.6.7.8': What is his email address?"
    q2 = extract_question_info(log2)
    assert q2 is not None
    assert q2["requester"] == "anonymous IP '5.6.7.8'"
    assert q2["question"] == "What is his email address?"

    # Contact form format
    log3 = "Question asked via contact form by user 'hr@tech.io' (IP: 9.9.9.9): Do you relocate?"
    q3 = extract_question_info(log3)
    assert q3 is not None
    assert q3["requester"] == "user 'hr@tech.io' (IP: 9.9.9.9)"
    assert q3["question"] == "Do you relocate?"

    # Non-question log should return None
    log_none = "GET /healthz -> 200 (1.20ms)"
    assert extract_question_info(log_none) is None


def test_parse_since_durations():
    """Verify duration parsing for logs and account query scripts."""
    assert parse_log_since("24h") == timedelta(hours=24)
    assert parse_log_since("1d") == timedelta(days=1)
    assert parse_log_since("7d") == timedelta(days=7)
    assert parse_log_since("30m") == timedelta(minutes=30)
    assert parse_log_since("12") == timedelta(hours=12)

    assert parse_account_since("24h") == timedelta(hours=24)
    assert parse_account_since("7d") == timedelta(days=7)
    assert parse_account_since("30d") == timedelta(days=30)


def test_get_account_creation_time_fallback():
    """Verify resolution of account creation timestamp with created_at, snapshot create_time, and last_login."""
    now_utc = datetime(2026, 10, 13, 10, 0, 0, tzinfo=timezone.utc)

    # 1. Explicit created_at
    mock_doc1 = MagicMock()
    data1 = {"created_at": "2026-10-10T12:00:00Z"}
    dt1 = get_account_creation_time(mock_doc1, data1)
    assert dt1 == datetime(2026, 10, 10, 12, 0, 0, tzinfo=timezone.utc)

    # 2. Snapshot metadata create_time
    mock_doc2 = MagicMock()
    mock_doc2.create_time = now_utc
    data2 = {"email": "test@test.com"}
    dt2 = get_account_creation_time(mock_doc2, data2)
    assert dt2 == now_utc

    # 3. Fallback to last_login
    mock_doc3 = MagicMock()
    mock_doc3.create_time = None
    data3 = {"last_login": "2026-10-08T15:00:00Z"}
    dt3 = get_account_creation_time(mock_doc3, data3)
    assert dt3 == datetime(2026, 10, 8, 15, 0, 0, tzinfo=timezone.utc)
