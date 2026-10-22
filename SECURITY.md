# Security Policy & Baseline Threat Model

Security, least privilege, and defense-in-depth are foundational architectural priorities for Brandon Foster's portfolio and associated cloud infrastructure. This document defines our **Vulnerability Disclosure Policy**, **System Data Flow Diagram (DFD)**, and **Baseline STRIDE Threat Model**.

---

## Supported Versions

Only the latest commit on the `main` branch deployed to the production environment is actively supported and monitored for security issues.

| Version / Branch | Supported |
| :--- | :--- |
| `main` (Production Deployment) | :white_check_mark: |
| Historical releases & experimental branches | :x: |

---

## System Architecture & Trust Boundary Data Flow Diagram (DFD)

The application runs on Google Cloud Platform (GCP) and Firebase with a scale-to-zero serverless architecture provisioned via Terraform (`infra/envs/prod/`) and a FastAPI backend (`backend/app/`):

```text
+---------------------------------------------------------------------------------------------------+
| TB-1: Untrusted Public Internet                                                                   |
|   [ Visitor Browser / Firebase Web App ]   [ External API Caller / Automated Bot ]                |
+---------------------------------------------------------------------------------------------------+
                     │                                           │
                     │ HTTPS (TLS 1.3 via Managed Cert)          │ Direct HTTPS Probe
                     ▼                                           ▼
+---------------------------------------------------------------------------------------------------+
| TB-2: Edge & Application Ingress Boundary (Cloud Run: INGRESS_TRAFFIC_ALL / allUsers)             |
|                                                                                                   |
|   1. RequestTracingMiddleware       -> Assigns X-Trace-ID & structured audit telemetry            |
|   2. CORSMiddleware                 -> Enforces strict origin allowlist (settings.CORS_ORIGINS)   |
|   3. ClientVerificationMiddleware   -> Enforces X-Portfolio-Client shared secret on /api/* (403)  |
|   4. Firebase JWT Auth & Rate Gate  -> Verifies RS256 ID Token + Persistent Firestore Quota (429) |
|                                                                                                   |
|   [ FastAPI Application Endpoints: /api/v1/chat/stream, /api/v1/chat/graph, /quota, /contact ]    |
+---------------------------------------------------------------------------------------------------+
                     │                                           │
                     │ Identity: sa-portfolio-backend-prod       │ Secret Key Ref (Startup/Runtime)
                     ▼                                           ▼
+---------------------------------------------------+ +---------------------------------------------+
| TB-3: Data Persistence & LLM Service Boundary     | | TB-4: Managed Secrets Boundary              |
|   - GCP Firestore Native (roles/datastore.user)   | |   - GCP Secret Manager                      |
|   - Google Gemini API (LangGraph RAG Agent)       | |     (roles/secretmanager.secretAccessor)    |
|   - ChromaDB Local Vector Store (Read-Only Embed) | |   - GEMINI_API_KEY, SMTP_PASSWORD           |
+---------------------------------------------------+ +---------------------------------------------+

+---------------------------------------------------------------------------------------------------+
| TB-5: Control Plane & CI/CD Deployment Boundary (Keyless OIDC Workload Identity Federation)       |
|   [ GitHub Actions Workflow ] --(OIDC Token: assertion.repository == 'brandocomando/portfolio')-->|
|   [ google_iam_workload_identity_pool_provider.github_provider ]                                  |
|         └── Impersonates: sa-github-actions (Artifact Registry, Cloud Run Deploy, Terraform)      |
+---------------------------------------------------------------------------------------------------+
```

---

## Baseline STRIDE Threat Model & Context-Aware Risk Register

This threat model documents the architectural risks across our five trust boundaries (`TB-1` through `TB-5`), incorporating infrastructure reachability, IAM blast radius, and application security controls:

| ID | STRIDE Category | Trust Boundary & Component | Threat Description | Raw Severity | Contextual Severity | Context Adjustment Rationale (Terraform + Application Controls) |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| **TM-01** | **Spoofing** | `TB-1 -> TB-2`<br/>`ClientVerificationMiddleware` & `security.py` | Unauthenticated external clients spoofing origin headers, `X-Forwarded-For` IP addresses, or forging Bearer tokens to bypass identity checks on `/api/v1/*`. | `High` | **`Low`** | **Downgraded:** `ClientVerificationMiddleware` enforces `X-Portfolio-Client` secret verification (`HTTP 403`) before route execution, and `verify_firebase_token()` cryptographically validates RS256 signatures against Google's public certs with audience locked to `FIREBASE_PROJECT_ID`. |
| **TM-02** | **Tampering** | `TB-2 -> TB-3`<br/>`POST /api/v1/chat/stream` & `langgraph_agent.py` | Adversarial prompt injection or history payload tampering attempting to override system instructions or poison RAG context. | `High` | **`Low`** | **Downgraded:** ChromaDB vector store is read-only at runtime, Pydantic schemas strictly cap message/history length, and the runtime Service Account (`sa-portfolio-backend-prod`) has zero IAM permissions to mutate infrastructure or code artifacts. |
| **TM-03** | **Repudiation** | `TB-2 -> TB-3`<br/>`RequestTracingMiddleware` & `firestore_service.py` | Anonymous or authenticated callers submitting abusive queries or contact spam without an auditable trail. | `Medium` | **`Low`** | **Downgraded:** Every request is assigned a correlation `X-Trace-ID`, and question/contact events are logged to Cloud Logging and persisted in Firestore with requester identity and client IP metadata. |
| **TM-04** | **Information Disclosure** | `TB-2 -> TB-4`<br/>`infra/modules/cloud_run` & `infra/modules/secrets` | Exposure of `GEMINI_API_KEY` or `SMTP_PASSWORD` via container image layers, environment dumps, or Terraform state leakage. | `Critical` | **`Low`** | **Downgraded:** Terraform (`infra/modules/secrets/main.tf`) provisions empty secret containers (values added out-of-band via `gcloud`) and injects them at runtime via `value_source.secret_key_ref`. No plaintext secrets exist in `.tf` files or git history. |
| **TM-05** | **Denial of Service** | `TB-1 -> TB-2`<br/>`google_cloud_run_v2_service.backend` & `rate_limiter.py` | Volumetric request flooding against public Cloud Run ingress (`INGRESS_TRAFFIC_ALL`, `allUsers`) aiming to exhaust Gemini API quotas or trigger runaway cloud billing. | `High` | **`Medium`** | **Adjusted:** While `INGRESS_TRAFFIC_ALL` exposes the endpoint publicly, Terraform enforces `max_instance_count = 5`, `cpu_limit = "1"`, and `memory_limit = "512Mi"` (`infra/envs/prod/main.tf`), while Firestore-backed daily token quotas (`ANON_DAILY_LIMIT` / `AUTH_DAILY_LIMIT`) reject excess calls with `HTTP 429`. |
| **TM-06** | **Elevation of Privilege** | `TB-5 (CI/CD Control Plane)`<br/>`infra/modules/iam_wif/main.tf` | Compromised GitHub Actions workflow or unauthorized fork attempting to assume `sa-github-actions` (which holds `roles/editor`, `roles/resourcemanager.projectIamAdmin`, and `roles/secretmanager.admin`). | `Critical` | **`Medium`** | **Contextual Watch Item:** The CI/CD SA holds broad project-level roles (`roles/editor`, `roles/secretmanager.admin`) to execute Terraform, which elevates blast radius if compromised. However, OIDC Workload Identity Federation enforces `attribute_condition = "assertion.repository == 'brandocomando/portfolio'"` with zero static JSON keys. |
| **TM-07** | **Tampering / Data Loss** | `TB-3 (Data Layer)`<br/>`infra/modules/firestore/main.tf` | Accidental or malicious Terraform destroy deleting the production Firestore database. | `Medium` | **`Medium`** | **Maintained:** `google_firestore_database.database` currently specifies `delete_protection_state = "DELETE_PROTECTION_DISABLED"` and `deletion_policy = "DELETE"`. Recommended hardening target (`DELETE_PROTECTION_ENABLED` in prod). |

---

## Automated DevSecOps Security Pipelines

The repository operates two complementary DevSecOps workflows:

### 1. PR Diff-Scoped Security Inspector (`.github/workflows/appsec-agent.yml`)
Triggered on every pull request to evaluate **only the newly added or modified code/infrastructure lines** in the PR diff:
1. **Material-Change Detection (`scripts/security/filter_diff.py`):** Filters out non-material documentation/styling changes and triggers analysis when `.tf`, dependency, auth/middleware, or application code is modified.
2. **Infrastructure & Route Context Extraction (`scripts/security/extract_context.py`):** Parses co-located Terraform HCL2 definitions and FastAPI routes to supply background architectural context (reachability, IAM scope, middleware gates) without flagging untouched files.
3. **Diff-Scoped STRIDE Threat Modeling & Test Synthesis (`scripts/security/run_agentic_eval.py`):** Evaluates the PR diff within its runtime context to produce context-adjusted severity ratings and runnable `pytest` verification stubs.
4. **PR Security Action Card (`scripts/security/post_pr_comment.py`):** Minimizes outdated assessment comments and posts the latest Context Summary, STRIDE Threat Model, and Generated Verification Test Suite to the pull request.

### 2. Full-Repository Security Audit & Issue Creator (`.github/workflows/appsec-full-scan.yml`)
Triggered on a weekly schedule (`cron`) or manually (`workflow_dispatch`) to audit the entire repository (`infra/`, `backend/`, `.github/workflows/`) and automatically open deduplicated GitHub Issues (`scripts/security/run_full_repo_audit.py`) labeled `security` for architectural or IAM hardening findings.

---

## Reporting a Vulnerability

If you believe you have discovered a security vulnerability in this repository or the live deployed infrastructure, please report it responsibly. **Do not create public GitHub issues, discussions, or pull requests for security vulnerabilities.**

### How to Report

Please submit a private report using **GitHub Private Vulnerability Reporting**:
1. Navigate to the repository's [Security Advisories](https://github.com/brandocomando/portfolio/security/advisories) tab.
2. Click **Report a vulnerability**.
3. Fill in the advisory details, potential impact, and reproduction steps.

This ensures the report is triaged privately and securely. For non-technical inquiries or if you are unable to use GitHub Private Vulnerability Reporting, you may connect via [LinkedIn](https://linkedin.com/in/brando-foster).

### Information to Include

To help triage and resolve the issue quickly, please include:
- A clear description of the vulnerability and potential impact.
- Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
- Affected endpoints, files, or cloud components (e.g., Cloud Run API routes, Firebase Auth token validation, Firestore security rules).
- Any proposed remediations or patches (conceptual; see [CONTRIBUTING.md](CONTRIBUTING.md)).

---

## Scope & Architectural Context

### In Scope
- Cryptographic bypasses or vulnerabilities in Firebase Auth JWT verification.
- Server-Side Request Forgery (SSRF) or Local File Inclusion (LFI).
- Injection flaws (command injection, Firestore NoSQL injection).
- Insecure direct object references (IDOR) or unauthorized data access in Firestore.
- Secret exposure or credential leakage in git history or CI/CD pipelines.
- Workload Identity Federation (WIF) / OIDC misconfigurations enabling unauthorized role assumption.

### Out of Scope
- Distributed Denial of Service (DDoS) or volumetric traffic flooding against rate-limited endpoints.
- Spamming public recruiter lead forms or token-bucket rate limiter exhaustion without proof of technical compromise.
- Theoretical issues without demonstrable impact or working PoC.
- Attacks requiring physical device access or social engineering (phishing).
- Vulnerabilities in third-party services (GitHub, Google Cloud, Firebase) outside this project's administrative configuration.

---

## Response & Disclosure Process

1. **Acknowledgment:** Vulnerability reports will be acknowledged within **48 hours**.
2. **Investigation & Triage:** The issue will be investigated and severity assessed.
3. **Remediation:** A fix will be developed, tested, and deployed to production.
4. **Coordinated Disclosure:** We kindly request that you maintain confidentiality until a fix has been deployed to production.

---

## Safe Harbor

Any security research conducted in good faith that respects visitor privacy, avoids data destruction or system degradation, and complies with this policy will be considered authorized. We will not pursue legal action against researchers acting in accordance with these guidelines.
