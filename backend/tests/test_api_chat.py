"""Integration tests for Health and Chat Endpoints."""

import json
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.rate_limiter import rate_limiter


@pytest.fixture(autouse=True)
def reset_rate_limiter_buckets():
    rate_limiter._buckets.clear()
    yield
    rate_limiter._buckets.clear()


def extract_streamed_text(sse_body: str) -> str:
    tokens = []
    for line in sse_body.splitlines():
        if line.startswith("data: ") and '"token"' in line:
            try:
                data = json.loads(line[6:])
                tokens.append(data.get("token", ""))
            except Exception:
                pass
    return "".join(tokens)


@pytest.mark.asyncio
async def test_health_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Liveness
        resp = await ac.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

        # Readiness
        resp = await ac.get("/readyz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ready"
        assert resp.json()["chunks_loaded"] > 0

        # Metrics
        resp = await ac.get("/metrics")
        assert resp.status_code == 200
        assert resp.json()["total_chunks_indexed"] > 0


@pytest.mark.asyncio
async def test_chat_stream_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "messages": [],
            "question": "What is Brandon's experience with Kubernetes and EKS?"
        }
        resp = await ac.post("/api/v1/chat/stream", json=payload)
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]
        body = resp.text
        assert "event: sources" in body
        assert "event: token" in body
        assert "event: done" in body

        streamed = extract_streamed_text(body)
        assert "Kubernetes" in streamed
        assert "Amazon EKS" in streamed
        # Ensure it does NOT dump raw internal tags
        assert "[TECHNICAL" not in streamed
        assert "[CAREER" not in streamed
        assert "GitHub Stars: 0" not in streamed


@pytest.mark.asyncio
async def test_chat_stream_conversational_ping():
    """Verify that 'test' returns conversational dialogue without dumping document sources."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "messages": [],
            "question": "test"
        }
        resp = await ac.post("/api/v1/chat/stream", json=payload)
        assert resp.status_code == 200
        body = resp.text
        assert "event: sources" in body
        assert '"sources": []' in body

        streamed = extract_streamed_text(body)
        assert "operational" in streamed.lower() or "systems" in streamed.lower()
        assert "[TECHNICAL SKILLS" not in streamed


@pytest.mark.asyncio
async def test_chat_stream_conversational_greeting():
    """Verify that 'hello' greets warmly without attaching document hits."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "messages": [],
            "question": "hello"
        }
        resp = await ac.post("/api/v1/chat/stream", json=payload)
        assert resp.status_code == 200
        body = resp.text
        assert '"sources": []' in body

        streamed = extract_streamed_text(body)
        assert "Brandon Foster's AI Assistant" in streamed


@pytest.mark.asyncio
async def test_chat_stream_conversational_python():
    """Verify that asking about Python directly answers conversationally."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "messages": [],
            "question": "Does Brandon know Python?"
        }
        resp = await ac.post("/api/v1/chat/stream", json=payload)
        assert resp.status_code == 200
        body = resp.text

        streamed = extract_streamed_text(body)
        assert "Yes, Brandon works with Python regularly" in streamed
        assert "FastAPI" in streamed


@pytest.mark.asyncio
async def test_contact_form_submission_success():
    """Verify that visitors can submit their contact question and email."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "name": "Alex Recruiter",
            "email": "alex@techrecruiting.com",
            "question": "Are you interested in a Principal Platform Engineer role?"
        }
        resp = await ac.post("/api/v1/leads/contact", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert "forwarded directly to Brandon" in data["message"]


@pytest.mark.asyncio
async def test_contact_form_submission_validation():
    """Verify that invalid submissions are rejected with 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Invalid email
        resp = await ac.post("/api/v1/leads/contact", json={
            "email": "not-an-email",
            "question": "Hello there"
        })
        assert resp.status_code == 422

        # Too short question
        resp = await ac.post("/api/v1/leads/contact", json={
            "email": "valid@email.com",
            "question": "hi"
        })
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_personal_questions_deflection_and_privacy():
    """Verify that personal questions not in docs deflect to contact page and never leak email/phone."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        questions = [
            "Where does Brandon live?",
            "What is his phone number?",
            "What is Brandon's email address?",
            "Who is his wife?",
            "How old is he?",
        ]
        for q in questions:
            resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": q})
            assert resp.status_code == 200
            streamed = extract_streamed_text(resp.text)

            # Must mention Contact Page or redirect
            assert "Contact Page" in streamed or "#contact" in streamed
            # Zero personal contact info leaked
            assert "brandocomando8@gmail.com" not in streamed
            assert "gmail.com" not in streamed


@pytest.mark.asyncio
async def test_off_topic_general_deflection():
    """Verify that off-topic trivia deflects with 'I don't know—maybe you should ask him!'."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/chat/stream",
            json={"messages": [], "question": "What is the capital of France?"}
        )
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" in streamed
        assert "Contact Page" in streamed or "#contact" in streamed


@pytest.mark.asyncio
async def test_chat_stream_mlops_query():
    """Verify that asking about ML ops returns MLOps and AI Infrastructure experience."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/chat/stream",
            json={"messages": [], "question": "what about ML ops?"}
        )
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "MLOps" in streamed or "AI Infrastructure" in streamed
        # Ensure it doesn't give Containers & Orchestration or robotic dump
        assert "Regarding Containers & Orchestration" not in streamed


@pytest.mark.asyncio
async def test_chat_stream_kids_query():
    """Verify that asking 'how many kids does brandon have?' deflects to the contact page."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/chat/stream",
            json={"messages": [], "question": "how many kids does brandon have?"}
        )
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" in streamed
        assert "Contact Page" in streamed or "#contact" in streamed
        assert "Regarding Brandon Foster Professional Overview" not in streamed

