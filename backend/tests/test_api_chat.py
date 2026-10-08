"""Integration tests for Health and Chat Endpoints."""

import json
import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.core.config import settings
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
    """Verify that private personal questions (family, age, salary, street address) deflect to contact page."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        questions = [
            "What is his home address?",
            "What is his phone number?",
            "What is Brandon's email address?",
            "Who is his wife?",
            "How old is he?",
            "What is his salary?",
            "What is his religion?",
        ]
        for q in questions:
            rate_limiter._buckets.clear()
            resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": q})
            assert resp.status_code == 200
            streamed = extract_streamed_text(resp.text)

            # Must mention Contact Page or redirect
            assert "Contact Page" in streamed or "#contact" in streamed
            # Zero personal contact info leaked
            if settings.NOTIFICATION_EMAIL_TO:
                assert settings.NOTIFICATION_EMAIL_TO not in streamed
            assert "gmail.com" not in streamed


@pytest.mark.asyncio
async def test_approved_personal_profile_answers():
    """Verify that authorized personal data in personal.yaml is accurately and delightfully answered."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        cases = [
            ("Where does Brandon live?", ["Southern California"]),
            ("What are his work preferences?", ["remote", "Orange County", "not willing to relocate"]),
            ("How many years of devops experience does he have?", ["14+"]),
            ("Where has Brandon worked?", ["Life360", "Persefoni AI", "Melrok", "Lakeshore", "Liferay"]),
            ("What is his favorite color?", ["Blue"]),
            ("Coffee or tea?", ["COFFEE"]),
            ("Cats or dogs?", ["Cats"]),
            ("Where did he go to school?", ["Biola University", "Computer Science"]),
            ("Tabs or spaces?", ["Tabs"]),
            ("Night owl or early bird?", ["early bird"]),
            ("Does pineapple belong on pizza?", ["YES"]),
            ("What is his favorite season?", ["Fall"]),
            ("Does he like dad jokes?", ["All the time"]),
            ("Beach or mountains?", ["Mountains"]),
            ("What is his favorite place?", ["Yosemite"]),
            ("What emojis does he use most?", ["ThumbsUp", "Roger roger", "Facepalm"]),
            ("What are his socials?", ["linkedin.com/in/brandon-foster", "github.com/brandocomando"]),
        ]
        for question, expected_tokens in cases:
            rate_limiter._buckets.clear()
            resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": question})
            assert resp.status_code == 200
            streamed = extract_streamed_text(resp.text)
            assert "I don't know—maybe you should ask him!" not in streamed, f"Failed for '{question}': was deflected"
            for token in expected_tokens:
                assert token.lower() in streamed.lower(), f"Expected '{token}' in answer to '{question}', got: {streamed}"



@pytest.mark.asyncio
async def test_off_topic_general_deflection():
    """Verify that off-topic trivia deflects with 'not something I'm configured to answer' and suggests ChatGPT / Claude."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/chat/stream",
            json={"messages": [], "question": "What is the capital of France?"}
        )
        streamed = extract_streamed_text(resp.text)
        assert "not something I'm configured to answer" in streamed
        assert "ChatGPT" in streamed or "Claude" in streamed
        assert "maybe you should ask him" not in streamed


@pytest.mark.asyncio
async def test_casual_greetings_whats_up():
    """Verify that 'whats up' and casual greetings return a greeting rather than deflection."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for q in ["whats up", "what's up", "What's up?", "how are you", "how's it going"]:
            rate_limiter._buckets.clear()
            resp = await ac.post(
                "/api/v1/chat/stream",
                json={"messages": [], "question": q}
            )
            assert resp.status_code == 200
            streamed = extract_streamed_text(resp.text)
            assert "maybe you should ask him" not in streamed
            assert "Brandon Foster's AI Assistant" in streamed


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


@pytest.mark.asyncio
async def test_chat_stream_cicd_queries():
    """Verify that CI/CD questions answer conversationally and never deflect to the contact page."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        cicd_questions = [
            "hows his CICD chops?",
            "Has brandon configured CICD piplines from scratch?",
            "What experience does Brandon have with GitHub Actions and CI/CD pipelines?",
        ]
        for q in cicd_questions:
            resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": q})
            assert resp.status_code == 200
            streamed = extract_streamed_text(resp.text)
            # Must NOT deflect to contact page
            assert "I don't know—maybe you should ask him!" not in streamed
            # Must discuss CI/CD chops, GitHub Actions, and migration from scratch
            assert "CI/CD" in streamed or "pipeline" in streamed.lower()
            assert "GitHub Actions" in streamed
            assert "100+" in streamed or "Bitbucket" in streamed
            assert "99.8%" in streamed or "reusable" in streamed.lower()


@pytest.mark.asyncio
async def test_chat_stream_jenkins_experience():
    """Verify that asking about Jenkins directly answers conversationally with CI/CD experience."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/api/v1/chat/stream",
            json={"messages": [], "question": "does he have jenkins experience?"}
        )
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Jenkins" in streamed
        assert "Yes, Brandon has hands-on experience with **Jenkins**" in streamed
        assert "GitHub Actions" in streamed or "ArgoCD" in streamed


@pytest.mark.asyncio
async def test_chat_stream_upstream_forks_disclaimer():
    """Verify that FirstMate and Agent Deck queries clarify they are upstream forks."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for q in ["Tell me about FirstMate CLI", "What is WezTerm Agent Deck?"]:
            resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": q})
            assert resp.status_code == 200
            streamed = extract_streamed_text(resp.text)
            assert "forks" in streamed.lower() or "upstream" in streamed.lower()
            assert "not" in streamed.lower() and "original work" in streamed.lower()
            assert "My Agentic Team" in streamed


@pytest.mark.asyncio
async def test_chat_stream_temporal_experience():
    """Verify Temporal questions explain conceptual workflow orchestration and event-driven background."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "Does Brandon have experience with Temporal?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Temporal" in streamed
        assert "event-driven" in streamed.lower() or "kafka" in streamed.lower()


@pytest.mark.asyncio
async def test_chat_stream_pulumi_cdk_experience():
    """Verify Pulumi / AWS CDK questions explain programmatic IaC concepts and Terraform expertise."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "What about Pulumi or AWS CDK?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Pulumi" in streamed or "CDK" in streamed
        assert "Terraform" in streamed


@pytest.mark.asyncio
async def test_chat_stream_fluxcd_experience():
    """Verify FluxCD questions bridge to ArgoCD GitOps expertise and Flux reconciliation concepts."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "Has he used FluxCD?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "FluxCD" in streamed
        assert "ArgoCD" in streamed


@pytest.mark.asyncio
async def test_chat_stream_backstage_port_experience():
    """Verify Backstage / Port questions highlight developer CLIs and paved roads while looking forward to IDP rollout."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "Does he have experience with Backstage or Port?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Backstage" in streamed or "Port" in streamed
        assert "Internal Developer Platform" in streamed or "IDP" in streamed


@pytest.mark.asyncio
async def test_chat_stream_databricks_spark_airflow():
    """Verify Databricks, Spark, and Airflow questions return hands-on lakehouse and pipeline experience."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "Has he worked with Databricks or Spark or Airflow?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Databricks" in streamed
        assert "Spark" in streamed or "Airflow" in streamed


@pytest.mark.asyncio
async def test_chat_stream_cassandra_aerospike_nosql():
    """Verify Cassandra and Aerospike questions confirm direct hands-on NoSQL experience."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "What about Cassandra or Aerospike?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Aerospike" in streamed
        assert "Cassandra" in streamed


@pytest.mark.asyncio
async def test_chat_stream_clickhouse_redshift():
    """Verify ClickHouse and Redshift questions explain analytical warehouse focus on Snowflake/Databricks."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "Does he have experience with ClickHouse or Redshift?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Snowflake" in streamed or "Databricks" in streamed


@pytest.mark.asyncio
async def test_chat_stream_soc2_hipaa_iso27001():
    """Verify SOC 2, HIPAA, and ISO 27001 questions confirm compliance audit evidence experience."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "Does Brandon have experience with SOC 2 or HIPAA or ISO 27001?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "SOC 2" in streamed
        assert "HIPAA" in streamed
        assert "ISO 27001" in streamed


@pytest.mark.asyncio
async def test_chat_stream_certifications_cka():
    """Verify certification questions explain that Brandon previously held CKA and prioritizes production systems."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "Does he have any certifications like CKA?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "CKA" in streamed
        assert "Kubernetes" in streamed


@pytest.mark.asyncio
async def test_chat_stream_azure_oracle_cloud():
    """Verify Azure and Oracle Cloud (OCI) questions address multi-cloud architecture without deflecting."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for q in ["What about Azure?", "Does he know Oracle Cloud?"]:
            resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": q})
            assert resp.status_code == 200
            streamed = extract_streamed_text(resp.text)
            assert "I don't know—maybe you should ask him!" not in streamed
            assert "AWS" in streamed
            assert "Terraform" in streamed


@pytest.mark.asyncio
async def test_chat_stream_sre_slo_observability():
    """Verify SRE and SLO questions return Prometheus, Datadog, OpenTelemetry, and error budgets."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "What is his experience with SRE, SLOs, or incident management?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "SLO" in streamed or "SLI" in streamed
        assert "postmortem" in streamed.lower()


@pytest.mark.asyncio
async def test_chat_stream_devex_paved_roads():
    """Verify developer experience and paved roads return self-service tooling and CLIs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "What about developer experience, CLIs, or paved roads?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "paved" in streamed.lower() or "golden" in streamed.lower()
        assert "Docker Compose" in streamed or "CLI" in streamed


@pytest.mark.asyncio
async def test_chat_stream_in_office_work_preferences():
    """Verify in-office, hybrid, and onsite workplace queries return work preferences without cloud confusion, specifying OC not LA."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        queries = [
            "is he open to in office work?",
            "is he open to in-office work?",
            "would he work in an office?",
            "is he open to onsite work?",
        ]
        for q in queries:
            rate_limiter._buckets.clear()
            resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": q})
            assert resp.status_code == 200
            streamed = extract_streamed_text(resp.text)
            assert "I don't know—maybe you should ask him!" not in streamed
            assert "remote" in streamed.lower()
            assert "orange county" in streamed.lower()
            assert "not los angeles" in streamed.lower() or "not la" in streamed.lower()
            assert "relocate" in streamed.lower()
            # Ensure it didn't confuse with cloud/AWS/GCP
            assert "[technical skills" not in streamed.lower()
            assert "amazon web services" not in streamed.lower()

        # Specific query for LA
        rate_limiter._buckets.clear()
        la_resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "is he open to working in LA?"})
        assert la_resp.status_code == 200
        la_streamed = extract_streamed_text(la_resp.text)
        assert "not open to working in or commuting to los angeles" in la_streamed.lower()
        assert "orange county" in la_streamed.lower()


@pytest.mark.asyncio
async def test_chat_stream_clean_bullet_headers():
    """Verify technical skill highlights never leak bracketed internal headers like [TECHNICAL SKILLS:...]."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "Tell me about your multi-cloud architecture experience."})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "[technical skills" not in streamed.lower()
        assert "• [technical" not in streamed.lower()
        assert "Amazon Web Services (AWS)" in streamed


@pytest.mark.asyncio
async def test_chat_stream_multi_turn_followup_affirmation():
    """Verify multi-turn conversations where user says 'yes' to a technical follow-up prompt expand the technical topic."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        history = [
            {"role": "user", "content": "how did he migrate from bitbucket to github?"},
            {
                "role": "assistant",
                "content": (
                    "Brandon has deep, battle-tested expertise in CI/CD... "
                    "Would you like to know more about his reusable workflow design, runner scaling, or GitOps deployment strategies?"
                ),
            },
        ]
        resp = await ac.post("/api/v1/chat/stream", json={"messages": history, "question": "yes"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "reusable workflow" in streamed.lower()
        assert "runner" in streamed.lower()
        assert "brandon foster personal profile" not in streamed.lower()
        assert "location: southern california" not in streamed.lower()


@pytest.mark.asyncio
async def test_chat_stream_multi_turn_in_office_then_cats():
    """Verify topic transitions across multiple turns (work preferences followed by cats)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        # Turn 1
        resp1 = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "is he open to in office work?"})
        assert resp1.status_code == 200
        text1 = extract_streamed_text(resp1.text)
        assert "remote" in text1.lower()
        assert "orange county" in text1.lower()
        assert "not los angeles" in text1.lower() or "not la" in text1.lower()

        # Turn 2
        rate_limiter._buckets.clear()
        history = [
            {"role": "user", "content": "is he open to in office work?"},
            {"role": "assistant", "content": text1},
        ]
        resp2 = await ac.post("/api/v1/chat/stream", json={"messages": history, "question": "does he like cats?"})
        assert resp2.status_code == 200
        text2 = extract_streamed_text(resp2.text)
        assert "cats" in text2.lower()
        assert "brandon foster personal profile" not in text2.lower()
        assert "location: southern california" not in text2.lower()


@pytest.mark.asyncio
async def test_chat_stream_code_authorship_ai_collaboration():
    """Verify code authorship inquiries explain Brandon's architectural direction and AI pair-programming."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "did he write any of your code? or ws it all AI?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Brandon architected" in streamed or "architected and engineered" in streamed
        assert "pair-programmer" in streamed or "force multiplier" in streamed
        assert "quality gates" in streamed or "unit and integration tests" in streamed


@pytest.mark.asyncio
async def test_chat_stream_how_brandon_built_ai_assistant():
    """Verify inquiries about how the AI assistant was built explain FastAPI, Cloud Run, Hybrid RAG, and Gemini."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "how did he make you?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "FastAPI" in streamed
        assert "Cloud Run" in streamed
        assert "Hybrid" in streamed or "BM25" in streamed
        assert "Gemini" in streamed


@pytest.mark.asyncio
async def test_chat_stream_scale_to_zero_gcp_infra():
    """Verify scale-to-zero infra questions explain FinOps design and Cloud Run without raw metadata labels."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "tell me about this scale to zero GCP infra"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "min-instances: 0" in streamed or "scale-to-zero" in streamed.lower()
        assert "$0/month" in streamed or "$0 idle cost" in streamed
        assert "Firebase Hosting" in streamed
        assert "Tagline:" not in streamed
        assert "Overview:" not in streamed


@pytest.mark.asyncio
async def test_chat_stream_personal_hobbies_list():
    """Verify personal hobbies inquiries return Hiking, Camping, and Cooking."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "What are his hobbies?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Hiking" in streamed
        assert "Camping" in streamed
        assert "Cooking" in streamed


@pytest.mark.asyncio
async def test_chat_stream_personal_hobby_cooking():
    """Verify specific inquiry about cooking returns Brandon's cooking hobby."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "Does he like cooking?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Cooking" in streamed


@pytest.mark.asyncio
async def test_chat_stream_personal_hobby_hiking_camping():
    """Verify inquiry about hiking and camping returns outdoor hobbies."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": "Does Brandon enjoy hiking or camping?"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Hiking" in streamed
        assert "Camping" in streamed


@pytest.mark.asyncio
async def test_chat_stream_verification_keyless_cloud_auth_oidc():
    """Verify specific claim challenge 'did he really do this? Keyless Cloud Auth...' directly confirms and explains OIDC."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        query = "did he really do this? Keyless Cloud Auth (OIDC / WIF): Eliminated static credentials across CI runners by implementing Workload Identity Federation between GitHub Actions, AWS, and GCP."
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": query})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Yes, Brandon really did this!" in streamed
        assert "Workload Identity Federation" in streamed
        assert "OpenID Connect" in streamed or "OIDC" in streamed
        # Ensure it does NOT dump unrelated broad CI/CD bullets
        assert "Enterprise Migration from Scratch (100+ Repos)" not in streamed


@pytest.mark.asyncio
async def test_chat_stream_verification_bitbucket_migration():
    """Verify claim challenge 'did he really migrate 100+ repos from bitbucket' directly confirms and explains Bitbucket migration."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        query = "did he really migrate 100+ repos from bitbucket to github?"
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": query})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Yes, Brandon really did this!" in streamed
        assert "Bitbucket" in streamed
        assert "GitHub Actions" in streamed


@pytest.mark.asyncio
async def test_chat_stream_keyless_cloud_auth_direct():
    """Verify direct inquiry about keyless cloud auth returns focused OIDC/WIF architecture."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        query = "How does keyless cloud auth work in his CI/CD setup?"
        resp = await ac.post("/api/v1/chat/stream", json={"messages": [], "question": query})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Workload Identity Federation" in streamed
        assert "OIDC" in streamed
        assert "Enterprise Migration from Scratch" not in streamed


@pytest.mark.asyncio
async def test_chat_stream_multi_turn_continuation_yea_tell_me_more_rag_platform():
    """Verify 'yea tell me more' seamlessly continues previous conversation about RAG, Medallion, and cold starts."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        history = [
            {"role": "user", "content": "tell me about this scale to zero GCP infra"},
            {
                "role": "assistant",
                "content": (
                    "This portfolio platform is engineered specifically around strict FinOps principles... "
                    "Are you curious about the hybrid RAG engine, the Medallion data pipeline, or how cold starts are handled?"
                ),
            },
        ]
        resp = await ac.post("/api/v1/chat/stream", json={"messages": history, "question": "yea tell me more"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "Hybrid RAG" in streamed
        assert "Medallion" in streamed
        assert "cold start" in streamed.lower()


@pytest.mark.asyncio
async def test_chat_stream_multi_turn_continuation_yes_tell_me_more_about_the_process():
    """Verify 'yes tell me more about the process' continues previous EKS conversation instead of personal profile."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        history = [
            {"role": "user", "content": "does he know much about eks?"},
            {
                "role": "assistant",
                "content": (
                    "Brandon has extensive hands-on experience with Kubernetes, especially leading enterprise migrations and GitOps adoption. "
                    "As Lead Platform Engineer, he architected and led the zero-downtime migration of mission-critical microservices from legacy AWS ECS to Amazon EKS. "
                    "Are you curious about the migration process, the GitOps workflow, or his observability tooling?"
                ),
            },
        ]
        resp = await ac.post("/api/v1/chat/stream", json={"messages": history, "question": "yes tell me more about the process"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "zero-downtime migration" in streamed.lower()
        assert "Route 53" in streamed
        assert "Pineapple on Pizza" not in streamed
        assert "personal preferences" not in streamed.lower()


@pytest.mark.asyncio
async def test_chat_stream_multi_turn_continuation_gitops_workflow():
    """Verify 'tell me more about the gitops workflow' continues with ArgoCD details."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        history = [
            {"role": "user", "content": "does he know much about eks?"},
            {
                "role": "assistant",
                "content": (
                    "Brandon has extensive hands-on experience with Kubernetes, especially leading enterprise migrations and GitOps adoption. "
                    "Are you curious about the migration process, the GitOps workflow, or his observability tooling?"
                ),
            },
        ]
        resp = await ac.post("/api/v1/chat/stream", json={"messages": history, "question": "tell me more about the gitops workflow"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "ArgoCD" in streamed
        assert "ApplicationSets" in streamed
        assert "Pineapple on Pizza" not in streamed


@pytest.mark.asyncio
async def test_chat_stream_multi_turn_short_topic_reply_gitopss_typo():
    """Verify 'gitopss' typo smoothly resolves to GitOps architecture when offered by assistant."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        history = [
            {"role": "user", "content": "does he know much about eks?"},
            {
                "role": "assistant",
                "content": (
                    "Brandon has extensive hands-on experience with Kubernetes, especially leading enterprise migrations and GitOps adoption. "
                    "Are you curious about the migration process, the GitOps workflow, or his observability tooling?"
                ),
            },
        ]
        resp = await ac.post("/api/v1/chat/stream", json={"messages": history, "question": "gitopss"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "ArgoCD" in streamed
        assert "ApplicationSets" in streamed
        assert "Pineapple on Pizza" not in streamed


@pytest.mark.asyncio
async def test_chat_stream_multi_turn_short_topic_reply_the_process():
    """Verify 'the process' resolves to the zero-downtime migration playbook without conversational filler."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        history = [
            {"role": "user", "content": "does he know much about eks?"},
            {
                "role": "assistant",
                "content": (
                    "Brandon has extensive hands-on experience with Kubernetes, especially leading enterprise migrations and GitOps adoption. "
                    "Are you curious about the migration process, the GitOps workflow, or his observability tooling?"
                ),
            },
        ]
        resp = await ac.post("/api/v1/chat/stream", json={"messages": history, "question": "the process"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "zero-downtime migration" in streamed.lower()
        assert "Route 53" in streamed


@pytest.mark.asyncio
async def test_chat_stream_multi_turn_short_topic_reply_securirty_typo():
    """Verify 'securirty' resolves to service mesh & zero-trust security when security was offered."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        rate_limiter._buckets.clear()
        history = [
            {"role": "user", "content": "does he know much about eks?"},
            {
                "role": "assistant",
                "content": (
                    "Brandon has extensive hands-on experience with Kubernetes... "
                    "Are there specific Kubernetes networking, security (mTLS), or storage patterns you'd like to dive into?"
                ),
            },
        ]
        resp = await ac.post("/api/v1/chat/stream", json={"messages": history, "question": "securirty"})
        assert resp.status_code == 200
        streamed = extract_streamed_text(resp.text)
        assert "I don't know—maybe you should ask him!" not in streamed
        assert "zero-trust" in streamed.lower() or "mTLS" in streamed or "App Mesh" in streamed













