# Brandon Foster | Cloud Platform, Distributed Systems & MLOps Portfolio

[![MLOps Evaluation Gate](https://github.com/brandocomando/portfolio/actions/workflows/mlops-pipeline.yml/badge.svg)](https://github.com/brandocomando/portfolio/actions/workflows/mlops-pipeline.yml)
[![Terraform CI](https://github.com/brandocomando/portfolio/actions/workflows/terraform-ci.yml/badge.svg)](https://github.com/brandocomando/portfolio/actions/workflows/terraform-ci.yml)
[![Backend CI/CD](https://github.com/brandocomando/portfolio/actions/workflows/backend-ci-cd.yml/badge.svg)](https://github.com/brandocomando/portfolio/actions/workflows/backend-ci-cd.yml)
[![Frontend CI/CD](https://github.com/brandocomando/portfolio/actions/workflows/frontend-ci-cd.yml/badge.svg)](https://github.com/brandocomando/portfolio/actions/workflows/frontend-ci-cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> A production-grade personal website, conversational AI assistant, and data platform engineered to showcase senior/staff-level capabilities across **Platform Engineering**, **Distributed Systems**, **AI Infrastructure / MLOps**, and **Cloud FinOps** on Google Cloud Platform.
>
> **Core FinOps Constraint:** Effectively **$0.00/month idle cost** via serverless scale-to-zero compute (Cloud Run) and edge CDN (Firebase Hosting), with zero static service account credentials (Workload Identity Federation).

---

## 🏛️ System Architecture

```
                                ┌──────────────────────────────────────────────┐
                                │                 VISITOR BROWSER              │
                                │  • React 18/19 + Vite + TypeScript SPA       │
                                │  • Dark/Light Theme + Interactive Showcase   │
                                │  • Streaming AI Chat Drawer (SSE)            │
                                └───────┬───────────────────────────────┬──────┘
                                        │                               │
                      Static Assets &   │                               │ 1-Click Sign-in
                      Cached SPA Shell  │                               ▼
                                        │                     ┌────────────────────┐
                                        ▼                     │   Firebase Auth    │
                         ┌─────────────────────────────┐      │ (Google / GitHub)  │
                         │    Firebase Hosting (CDN)   │      └─────────┬──────────┘
                         │   • Free SSL & Global Edge  │                │
                         │   • Rewrites /api/* to Run  │                │ Bearer ID Token
                         └──────────────┬──────────────┘                │
                                        │                               │
                                        ▼                               ▼
                     ┌────────────────────────────────────────────────────────┐
                     │              FastAPI on Cloud Run (Scale-to-0)         │
                     │                                                        │
                     │  ┌──────────────────────────────────────────────────┐  │
                     │  │ Multi-Tier Token Bucket Rate Limiting           │  │
                     │  │  • Anonymous: 5 queries / day (IP Token Bucket)  │  │
                     │  │  • Authenticated: 30 queries / day (UID Bucket)  │  │
                     │  └──────────────────────────────────────────────────┘  │
                     │                                                        │
                     │  ┌──────────────────────────────────────────────────┐  │
                     │  │ Recruiter Lead Capture Service                  │  │
                     │  │  • Cryptographic Firebase JWT verification       │  │
                     │  │  • Stores visitor info & question logs in        │  │
                     │  │    Google Cloud Firestore (Free Tier: 20k/day)  │  │
                     │  │  • Optional real-time Discord / Slack Webhook    │  │
                     │  └──────────────────────────────────────────────────┘  │
                     │                                                        │
                     │  ┌──────────────────────────────────────────────────┐  │
                     │  │ Hybrid Retrieval Engine (BM25 + Dense RRF)       │  │
                     │  │  • Sub-2ms in-memory retrieval from Gold bundle  │  │
                     │  │  • Reciprocal Rank Fusion (RRF k=60)             │  │
                     │  │  • Gemini 2.0 Flash Streaming Token Client       │  │
                     │  └──────────────────────────────────────────────────┘  │
                     └─────────────────────────▲──────────────────────────────┘
                                               │
                                               │ In-Memory Artifact Bundle
                                               │
                        ┌──────────────────────┴──────────────────────┐
                        │         GitHub Actions MLOps CI/CD          │
                        │                                             │
                        │  1. Ingest GitHub API & raw YAML (Bronze)   │
                        │  2. Pydantic v2 validation & AST chunking   │
                        │     (Silver layer DataOps gates)            │
                        │  3. Build BM25 + subword dense index (Gold) │
                        │  4. Run Continuous Evaluation Benchmark     │
                        │     (Fail CI if Hit Rate < 85% or MRR < 0.7)│
                        │  5. Package signed immutable bundle & SHA   │
                        └─────────────────────────────────────────────┘
```

---

## 🎯 Architectural Highlights & Discipline Showcase

### 1. Data Platform: Medallion Lakehouse Pattern
* **Bronze Layer:** Immutable ingestion from raw sources (live GitHub REST API repos and structured career YAML files) with cryptographic SHA-256 source hashing.
* **Silver Layer:** Strict schema enforcement via **Pydantic v2 data contracts**, AST-aware semantic chunking (respecting markdown heading hierarchies rather than arbitrary character splits), and DataOps assertions.
* **Gold Layer:** Optimized dual-representation retrieval assets: an inverted BM25 vocabulary index + subword TF-IDF normalized dense embeddings packaged with a signed metadata manifest.

### 2. AI Infra & Retrieval: Hybrid Search + Reciprocal Rank Fusion (RRF)
* **The Problem:** Pure vector embeddings frequently hallucinate or miss exact technical tokens (e.g. `node_exporter`, `neo4j`, `App Mesh`, `mTLS`).
* **The Solution:** Combined dense semantic search with sparse **Okapi BM25** search using **Reciprocal Rank Fusion (RRF)**:
  $$RRF\_Score(d \in D) = \sum_{m \in \{\text{Dense}, \text{BM25}\}} \frac{1}{60 + \text{rank}_m(d)}$$
* **Performance:** Executes in **< 1.5ms** in Cloud Run memory without requiring expensive managed vector databases (saving \$70–\$200/mo).

### 3. MLOps: Automated CI Evaluation Gate (LLM-as-a-Judge)
* Any update to career history, skills, or projects triggers an **Offline Evaluation Suite** in GitHub Actions.
* Evaluates 12+ real-world interview scenarios against defined quality thresholds:
  * **Top-3 Retrieval Hit Rate:** **90.9%** (Gate: $\ge 85.0\%$)
  * **Mean Reciprocal Rank (MRR):** **0.864** (Gate: $\ge 0.700$)
  * **Keyword Recall:** **98.0%**
  * **Adversarial Guardrail Deflection:** **100.0%** (Gate: $100\%$)
* **Failure Gate:** If retrieval precision drops or a prompt injection bypasses guardrails, **the CI build fails and prevents deployment**.

### 4. Distributed Systems & Orchestration: Durable Execution with Temporal
* **KnowledgeSyncWorkflow:** Orchestrates the entire multi-stage ingestion, transformation, embedding, and continuous evaluation pipeline as a **Temporal Durable Workflow** (`temporalio`).
* **Saga Pattern & Exponential Retry:** Automatically handles transient GitHub API rate limits and network partitions with stateful retry policies.
* **Human-in-the-Loop Signals:** If evaluation results fall into a borderline threshold (85–90%), the workflow suspends execution and waits for an external approval signal (`approve_deployment`) before publishing the index.
* **FinOps ($0 Cost):** Tested in CI/CD using Temporal's in-process ephemeral test server (`temporalio.testing.WorkflowEnvironment`), proving distributed systems reliability without running 24/7 paid server clusters.

### 5. Advanced AI Reasoning: LangGraph Stateful Agent Graph
* **Cognitive StateGraph:** In addition to direct low-latency SSE streaming, the backend features an advanced **LangGraph** (`langgraph`) multi-step reasoning agent (`/api/v1/chat/graph`).
* **Graph Architecture:**
  $$\text{User Prompt} \longrightarrow \text{GuardrailNode} \longrightarrow \text{HybridRetrieverNode} \longrightarrow \text{ReasoningNode} \longrightarrow \text{SynthesisNode}$$
* **Deterministic Guardrails:** Rejects prompt injection and jailbreak attempts at the graph entrance, saving 100% of LLM API and compute costs on adversarial queries.

### 6. Platform Engineering & Security
* **FinOps Scale-to-Zero:** Cloud Run container scales to 0 instances when idle, taking advantage of GCP's free tier (2M requests, 360k vCPU-seconds/mo).
* **Workload Identity Federation (WIF):** 100% keyless CI/CD. GitHub Actions exchanges ephemeral OIDC JWT tokens with GCP STS—**zero long-lived service account keys stored in GitHub Secrets**.
* **Lead Capture & Anti-Abuse:** Multi-tier token bucket rate limiting (5 queries/day for anonymous visitors by IP; 30 queries/day for authenticated users via Firebase Auth), logging recruiter interactions in Firestore.

---

## 📑 Architecture Decision Records (ADRs)

Key engineering trade-offs and rationale are formally documented in [`docs/adr/`](docs/adr/):

| ADR | Title | Decision Summary |
| :--- | :--- | :--- |
| [**ADR-001**](docs/adr/ADR-001-serverless-cloud-run-vs-gke.md) | Serverless Cloud Run vs GKE | Selected Cloud Run scale-to-zero to avoid GKE's \$74.40/mo cluster fee while preserving container portability. |
| [**ADR-002**](docs/adr/ADR-002-medallion-lakehouse-architecture.md) | Medallion Lakehouse Architecture | Implemented Bronze/Silver/Gold pipeline with Pydantic contracts for deterministic, replayable indexing. |
| [**ADR-003**](docs/adr/ADR-003-hybrid-search-dense-bm25-rrf.md) | Hybrid Search (Dense + BM25 + RRF) | Combined semantic vector search with BM25 keyword matching to solve exact technical acronym retrieval. |
| [**ADR-004**](docs/adr/ADR-004-in-memory-artifact-vector-store.md) | In-Memory Vector Store vs Vector DB | Packaged index as an immutable artifact bundle yielding <2ms latency and \$0 idle cost. |
| [**ADR-005**](docs/adr/ADR-005-workload-identity-federation.md) | Workload Identity Federation (WIF) | Replaced static service account keys with short-lived OIDC token exchanges for zero-trust CI/CD. |
| [**ADR-006**](docs/adr/ADR-006-server-sent-events-streaming.md) | Server-Sent Events (SSE) Streaming | Used unidirectional SSE over HTTP/2 for low-latency token streaming without WebSocket state overhead. |
| [**ADR-007**](docs/adr/ADR-007-tiered-rate-limiting-lead-capture.md) | Tiered Rate Limiting & Lead Capture | Enforced 5-query anonymous IP bucket and 30-query authenticated UID bucket with Firestore lead logging. |
| [**ADR-008**](docs/adr/ADR-008-durable-execution-temporal-agent-workflows.md) | Durable Execution with Temporal | Orchestrated MLOps knowledge pipelines with retries, durable timers, and human-in-the-loop signals. |
| [**ADR-009**](docs/adr/ADR-009-langgraph-stateful-multi-agent-reasoning.md) | LangGraph Multi-Agent Reasoning | Implemented stateful cyclic reasoning graph for complex multi-hop queries and input guardrails. |


---

## 📂 Repository Structure

```
portfolio/
├── .github/
│   └── workflows/
│       ├── mlops-pipeline.yml    # Ingest, transform, build gold index & run CI eval gate
│       ├── terraform-ci.yml      # Format check, Trivy security scan, validate & plan
│       ├── terraform-cd.yml      # Terraform apply on merge to main
│       ├── backend-ci-cd.yml     # Pytest, multi-stage Docker build, push & Cloud Run deploy
│       └── frontend-ci-cd.yml    # TypeScript typecheck, Vite build & Firebase Hosting deploy
├── docs/
│   └── adr/                      # Formal Architecture Decision Records (ADR-001 to ADR-007)
├── mlops/                        # Data Platform & Continuous Evaluation
│   ├── raw_profile/              # Source YAML data (bio, experience, projects, skills)
│   ├── data/
│   │   ├── bronze/               # Raw immutable JSON payloads + GitHub API metadata
│   │   ├── silver/               # Schema-validated, chunked data contracts
│   │   └── gold/                 # Packed BM25 index + dense embeddings + signed manifest
│   ├── pipeline/                 # Medallion pipeline code (Bronze/Silver/Gold)
│   └── eval/                     # Golden benchmark dataset & evaluation runner
├── backend/                      # FastAPI Microservice on Cloud Run
│   ├── app/
│   │   ├── api/v1/               # Streaming SSE chat, lead quota, and health endpoints
│   │   ├── core/                 # Config, security (Firebase JWT), rate limiter, telemetry
│   │   └── services/             # Gemini 2.0 Flash client, hybrid retriever, Firestore logger
│   ├── Dockerfile                # Multi-stage, non-root, slim container
│   └── tests/                    # Pytest unit & integration test suite
├── frontend/                     # Modern React 18/19 SPA
│   ├── src/
│   │   ├── components/           # Hero, Architecture, Timeline, Projects, Skills, AiChatDrawer
│   │   └── lib/                  # Firebase Auth & SSE streaming client
│   └── vite.config.ts
├── infra/                        # 100% Terraform IaC
│   ├── modules/                  # Modular components: apis, artifact_registry, cloud_run, iam_wif, firestore, secrets
│   └── envs/prod/                # Production environment root configuration
├── scripts/
│   └── bootstrap_gcp.sh          # One-command idempotent GCP project bootstrapper
└── firebase.json                 # Firebase CDN edge proxy to Cloud Run backend
```

---

## 🚀 Local Development Quickstart

### Prerequisites
* Python 3.10+
* Node.js 20+
* Terraform 1.5+

### 1. Run the MLOps Pipeline & Evaluation Gate
```bash
# Set up virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r mlops/requirements.txt -r backend/requirements.txt

# Run the 3-stage Medallion Data Pipeline (Bronze -> Silver -> Gold)
python -m mlops.pipeline.run_pipeline --stage all

# Run the Continuous Evaluation Benchmark Gate
python mlops/eval/evaluate_agent.py
```

### 2. Run Backend Microservice & Tests
```bash
# Run test suite
pytest backend/tests/

# Start local FastAPI server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8080 --reload
```
Access interactive OpenAPI docs at `http://localhost:8080/docs`.

### 3. Run Frontend SPA
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` to explore the interactive portfolio and test the streaming AI Assistant.

---

## ☁️ Google Cloud Deployment

### 1. One-Command GCP Bootstrap
When ready to deploy to a new GCP project:
```bash
# Log in and run the idempotent bootstrapper
gcloud auth login
./scripts/bootstrap_gcp.sh
```
This script automatically:
1. Enables necessary Google Cloud APIs.
2. Provisions a versioned GCS bucket for Terraform remote state.
3. Sets up Secret Manager for the Gemini API key.
4. Generates `infra/envs/prod/terraform.tfvars`.

### 2. Terraform Apply
```bash
cd infra/envs/prod
terraform init -backend-config="bucket=portfolio-terraform-state-<PROJECT_ID>"
terraform apply
```

### 3. Configure GitHub Secrets for Keyless CI/CD
In your GitHub Repository (`Settings` > `Secrets and variables` > `Actions`), add:
* `GCP_PROJECT_ID`: Your GCP Project ID
* `GCP_TF_STATE_BUCKET`: `portfolio-terraform-state-<PROJECT_ID>`
* `GCP_WIF_PROVIDER`: The output from `terraform output workload_identity_provider`
* `GCP_WIF_SA_EMAIL`: The output from `terraform output github_actions_sa_email`

Any push to `main` will automatically build, test, and deploy across all pipelines!
