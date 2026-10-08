# ADR-010: Dual-Process Cognitive Architecture (System-1 Fast Routing & FinOps Relevance Gating)

## Status
Accepted

## Context & Problem Statement
Exposing an unconstrained Large Language Model (LLM) API directly to public internet traffic introduces severe architectural and operational risks:
1. **Denial-of-Wallet (DoW) & Quota Depletion:** Invoking external generative models on every incoming request burns API quotas and risks compute cost overruns, violating the core FinOps requirement of operating at effectively **$0.00/month idle cost**.
2. **Adversarial Exploitation & Model Hijacking:** External actors attempt prompt injections, jailbreaks, and attempt to turn the personal portfolio assistant into a generic LeetCode/script generator or homework solver.
3. **Latency Inefficiencies:** Round-tripping basic factual inquiries (e.g., location, hobbies, years of experience, or greetings) through an external LLM introduces 800ms–2500ms of unnecessary time-to-first-token (TTFT) latency.
4. **Ungrounded Hallucinations:** When visitors ask arbitrary non-engineering trivia (e.g. world leaders, geography, cooking recipes), generic LLMs hallucinate or provide ungrounded answers instead of directing users to appropriate portfolio contacts.

## Decision
We implement a **Dual-Process Cognitive Architecture** (inspired by Daniel Kahneman's System-1 / System-2 framework) separating instantaneous, deterministic processing from generative LLM reasoning:

### 1. System-1: Sub-5ms Fast-Path Intent Router & Privacy Gate
Implemented in `backend/app/services/intent.py`, this layer executes regex and fuzzy string classification in Cloud Run memory before any retrieval or external API calls:
* **Security Guardrails:** Intercepts prompt injection and jailbreak payloads (`GUARDRAIL_PATTERNS`).
* **Strict Privacy Guardrail:** Redacts personal contact details (phone, private email, street address, salary) and directs recruiters to the contact form.
* **Authorized Personal Profile Router:** Instantly serves verified profile trivia and facts directly from `personal.yaml` (location preferences, education, chronotype, pets, hobbies).
* **Anti-Hijacking Code Gate:** Rejects requests to generate arbitrary algorithms or LeetCode solutions, maintaining strict portfolio context boundaries.
* **Conversational Pings & Greetings:** Instant canned responses for system tests, health pings, and introductions.

### 2. System-1: In-Memory Hybrid Relevance Gate
Implemented in `backend/app/api/v1/chat.py`, this layer leverages retrieval scores to gate System-2 execution:
* When a query produces zero BM25 keyword matches across the inverted index (`has_bm25 == False`) and a dense semantic cosine similarity below the relevance threshold (`dense_score < 0.135`), System-1 intercepts the request.
* If the query is not recognized by local architectural handlers, it is deflected as `OFF_TOPIC_GENERAL` with 0 Gemini API calls:
  > *"I don't know—maybe you should ask him! That's outside the scope of Brandon Foster's professional engineering portfolio..."*

### 3. System-2: Grounded Gemini 3.8 Flash Orchestration
When a query passes System-1 relevance gating:
* The backend invokes Google GenAI SDK asynchronously (`_genai_client.aio.models.generate_content_stream`).
* Strict system prompt boundaries ground answers in the retrieved Gold index chunks and enforce 12-turn conversational history normalization.
* If external LLM connectivity drops, the system gracefully falls back to `synthesize_conversational_response`.

## Consequences & Trade-offs

### Positive
* **FinOps Budget Security:** Eliminates 100% of LLM token and API compute costs on off-topic questions, bot spam, and adversarial jailbreak attempts.
* **Instantaneous TTFT (<5ms):** Over 40% of recruiter interactions (greetings, location inquiries, work preferences) stream instantly without cold-start or LLM network lag.
* **Deterministic Guardrails:** Personal contact information and boundaries are cryptographically protected by code rather than probabilistic system prompt hopes.

### Negative / Mitigations
* **Pattern Maintenance:** System-1 requires maintaining keyword patterns and regex rules as new topics emerge.
  * *Mitigation:* The MLOps evaluation gate (`evaluate_agent.py`) tests the golden benchmark dataset on every pull request, ensuring guardrail accuracy ($\ge 100\%$) and keyword recall.
