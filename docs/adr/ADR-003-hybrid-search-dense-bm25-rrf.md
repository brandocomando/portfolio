# ADR-003: Hybrid Retrieval (Dense Vector + BM25) with Reciprocal Rank Fusion (RRF)

## Status
Accepted

## Context & Problem Statement
Naive RAG architectures rely exclusively on dense vector similarity (cosine similarity over embedding vectors). In technical engineering portfolios, visitors frequently query specific acronyms, tool names, and library identifiers (e.g., `neo4j`, `node_exporter`, `App Mesh`, `mTLS`, `ArgoCD`, `EKS`).

Dense embeddings frequently suffer from:
1. **Semantic drift on rare/technical tokens:** Embedding models map niche technical tokens into generic semantic clusters (e.g., confusing `node_exporter` with generic Node.js web frameworks or general Prometheus queries).
2. **Missing exact keyword recall:** When a recruiter explicitly asks *"Does Brandon know Go?"*, semantic search may return Python microservices if the semantic distance is close, ignoring the exact language filter.

## Decision
We implement a **Hybrid Retrieval Engine** combining:
1. **Dense Retrieval:** Semantic similarity powered by text embedding models (`text-embedding-004` or fast local embeddings).
2. **Sparse Retrieval:** Exact keyword matching via BM25 (Okapi BM25 with term frequency, document frequency, and document length normalization).
3. **Rank Fusion:** **Reciprocal Rank Fusion (RRF)** to merge and rerank candidate sets without requiring arbitrary score normalization:

$$RRF\_Score(d \in D) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$

Where:
* $M = \{\text{Dense}, \text{Sparse}\}$ (the set of retrieval systems)
* $r_m(d)$ is the rank of document $d$ in system $m$ (1-indexed)
* $k = 60$ (standard smoothing constant to prevent top-ranked outliers from dominating)

## Consequences & Trade-offs

### Positive
* **Best of Both Worlds:** Captures high-level conceptual questions (e.g. *"What is Brandon's philosophy on platform engineering?"*) while guaranteeing exact keyword hits for specific tooling (e.g. *"Has Brandon built a Terraform provider in Go?"*).
* **Robust to Out-of-Vocabulary Terms:** BM25 guarantees that rare identifiers (`wezterm-agent-deck`, `app-mesh-controller`) are indexed and retrieved with 100% precision.

### Negative / Mitigations
* **Double Index Storage:** We maintain both dense embeddings and an inverted index dictionary.
  * *Mitigation:* Given the portfolio corpus size (~50–200 chunks), the combined index size is <5MB, fitting comfortably in-memory in the Cloud Run instance.
