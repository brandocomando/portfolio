# ADR-008: Durable Execution with Temporal for MLOps Pipelines & Agent Sagas

## Status
Accepted

## Context & Problem Statement
Data ingestion, vector index generation, and continuous evaluation pipelines involve multi-stage distributed tasks:
1. Fetching external APIs (GitHub REST API, external knowledge sources) subject to rate limits and network transient errors.
2. Long-running CPU-bound feature extraction, semantic chunking, and embedding generation.
3. Offline continuous evaluation against golden benchmarks with quality gates.
4. Human-in-the-loop approvals when evaluation scores are marginal or when sensitive achievements are published.

Standard cron jobs or linear Python scripts fail unpredictably on network timeouts, lack state recovery, cannot easily resume from intermediate checkpoints, and have no built-in mechanism for durable timers or asynchronous human-in-the-loop signals.

## Decision
We adopt **Temporal.io (`temporalio` Python SDK)** for durable workflow orchestration across our MLOps and agent pipelines:

1. **KnowledgeSyncWorkflow:**
   * **Durable Sagas:** Decomposes the pipeline into deterministic activities (`ingest_bronze`, `transform_silver`, `build_gold_index`, `evaluate_benchmark`, `publish_artifacts`).
   * **Exponential Retry with Jitter:** Configured on external I/O activities to gracefully survive transient API rate limits.
   * **Stateful Signals & Queries:** Allows querying workflow progress in real-time (`get_pipeline_status`) and receiving external approval signals (`approve_deployment`).
   * **Human-in-the-Loop Gate:** If the evaluation benchmark yields a score between 85% and 90% (borderline pass), the workflow suspends execution and waits up to 24 hours for a cryptographically verified approval signal before publishing the index.
2. **FinOps & CI/CD Strategy ($0 Cost):**
   * Rather than maintaining an idle 24/7 self-hosted Temporal cluster on Cloud SQL, we leverage Temporal's ephemeral test environment (`temporalio.testing.WorkflowEnvironment`) and `temporal server start-dev` in GitHub Actions CI/CD runners.
   * Enables 100% durable execution testing and automated saga verification for **$0/month**.

## Consequences & Trade-offs

### Positive
* **Crash Resilience:** Workflows resume execution from the exact step of failure without re-running completed, costly upstream tasks.
* **Deterministic Event History:** Full replayability and auditable execution history for every knowledge sync.
* **Distributed Systems Showcase:** Demonstrates production-grade saga patterns, durable timers, and human-in-the-loop approval workflows.

### Negative / Mitigations
* **Workflow Determinism Rules:** Temporal workflows must remain strictly deterministic (no direct non-deterministic I/O inside workflow definitions).
  * *Mitigation:* All network I/O, file reading, and random generation are isolated strictly inside Temporal `@activity.defn` functions.
