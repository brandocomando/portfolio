# ADR-001: Serverless Scale-to-Zero (Cloud Run) vs Managed Kubernetes (GKE)

## Status
Accepted

## Context & Problem Statement
The backend service hosts the FastAPI application serving the portfolio's RAG retrieval API, authentication verification, and visitor analytics. As a personal engineering showcase targeting Platform, Distributed Systems, and MLOps roles, we must demonstrate production-grade architecture while adhering to a strict **FinOps constraint: operating near $0/month idle cost**.

Managed Kubernetes (GKE) is the industry standard for distributed microservices, but Google Cloud charges a **$74.40/month cluster management fee** per standard GKE cluster, plus ongoing node compute and persistent volume charges even when traffic is zero.

## Decision
We deploy the backend service to **Google Cloud Run (Fully Managed Serverless Containers)** configured with:
* `min-instances: 0` (scale-to-zero when idle)
* `max-instances: 5` (hard ceiling against DDoS and bill exhaustion)
* Request-based billing (vCPU allocated only during active HTTP request processing)
* Container image packaged as an OCI-compliant, multi-stage distroless/slim Linux container.

## Consequences & Trade-offs

### Positive
* **Cost:** $0/month idle cost. Cloud Run's free tier provides 2 million requests, 360,000 vCPU-seconds, and 180 GiB-seconds free per month.
* **Operational Simplicity:** Zero control-plane or node-pool maintenance, automated TLS certificates, and out-of-the-box GCP Cloud Logging/Trace integration.
* **Portability:** The service is packaged as a standard Docker OCI container, maintaining 100% portability to GKE or EKS if traffic scales.

### Negative / Mitigations
* **Cold Starts:** Scaling from zero instances introduces a minor initial latency overhead (~800ms–1.2s for Python/FastAPI).
  * *Mitigation:* Kept container image slim (<100MB), pre-compiled bytecode, lazy-loaded heavy dependencies, and packaged the vector index as an in-memory binary format rather than connecting to an external database over a cold network socket.
