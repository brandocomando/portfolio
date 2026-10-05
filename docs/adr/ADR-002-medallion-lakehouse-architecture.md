# ADR-002: Medallion Lakehouse Architecture for Unstructured Knowledge

## Status
Accepted

## Context & Problem Statement
The AI agent must answer nuanced questions about Brandon's career, technical projects, architecture decisions, and skill sets. Information originates from multiple heterogeneous sources:
1. Live GitHub API metadata (repositories, commit history, releases, star counts)
2. Structured YAML files (career history, company milestones, quantified impact)
3. Deep-dive technical markdown documents (system designs, incident reviews)

Feeding raw documents directly into an LLM or using naive character-based text splitting leads to data corruption, lost context boundaries, duplicated facts, and hallucinated timelines.

## Decision
We implement a **Medallion Data Lakehouse Pattern (Bronze -> Silver -> Gold)** for data processing and index construction:

1. **Bronze Layer (Raw Ingestion):**
   * Stores immutable, raw payloads extracted from upstream sources (GitHub REST API, raw markdown files) with ingestion metadata (`source_uri`, `ingested_at`, `payload_hash`).
   * No transformations applied. Serves as the source of truth for full replayability.
2. **Silver Layer (Cleaned & Schema-Enforced Entities):**
   * Validated using strict **Pydantic v2 data contracts** (`CareerMilestone`, `TechnicalProject`, `CoreSkill`, `SystemArchitecture`).
   * Markdown documents parsed via AST-aware chunking (respecting semantic header levels `#`, `##`, `###`) rather than fixed-character slicing.
   * Data quality assertions: deduplication, schema validation, and missing-tag detection.
3. **Gold Layer (Feature & Retrieval Indices):**
   * Dual-representation retrieval assets: Dense embeddings + Sparse BM25 vocabulary.
   * Versioned index package with a signed manifest (`manifest.json` containing chunk count, token count, git commit SHA, and SHA-256 artifact checksum).

## Consequences & Trade-offs

### Positive
* **Deterministic & Replayable:** Any schema change or chunking logic update can be tested from Bronze without hitting external APIs.
* **Data Quality Gates:** Silver layer Pydantic validation rejects malformed entries before generating costly embeddings.
* **Separation of Concerns:** Clear boundary between ingestion, cleaning, and model-specific vectorization.

### Negative / Mitigations
* **Pipeline Complexity:** Requires a multi-stage execution pipeline rather than a 1-file script.
  * *Mitigation:* Encapsulated into a single CLI tool (`python -m mlops.pipeline`) with explicit stage flags (`--stage bronze|silver|gold|all`).
