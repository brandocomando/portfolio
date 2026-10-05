# ADR-004: In-Memory Packaged Vector Store vs Dedicated Managed Vector DB

## Status
Accepted

## Context & Problem Statement
Vector databases (Pinecone, Weaviate Cloud, Vertex AI Vector Search, Qdrant Cloud) are widely promoted for vector retrieval. However, evaluating infrastructure selection requires assessing **scale, latency, operational overhead, and FinOps**:
* **Vertex AI Vector Search:** Minimum index endpoint provisioning costs **~\$0.30/hour (~$210/month)**.
* **Serverless Vector DBs (Pinecone/Qdrant):** Introduce external network hops (30–80ms round-trip latency), vendor lock-in, and another API key to manage.
* **Portfolio Corpus Scale:** The knowledge base contains between 50 and 500 documents/chunks.

## Decision
We package the vectorized Gold index and BM25 dictionary as an **immutable, versioned artifact bundle** (`gold_index.tar.gz` or binary file) stored in Google Cloud Storage (GCS) and loaded directly into Cloud Run memory upon container initialization.

1. **Build Time:** The MLOps pipeline compiles chunks, computes embeddings, builds the BM25 index, and generates `gold_index.bin`.
2. **Deploy Time:** The artifact is either bundled into the container image or pulled from GCS during container cold start.
3. **Run Time:** Retrieval operations execute in-memory using vectorized NumPy dot-products and memory-mapped BM25 lookups.

## Consequences & Trade-offs

### Positive
* **Cost:** $0/month. No recurring database instance fees.
* **Latency:** In-memory vector dot-products over hundreds of vectors execute in **< 1.5 milliseconds** (vs. 50ms+ network calls to external DBs).
* **Deterministic Deployments:** The retrieval index is tied to a specific Git commit SHA and MLOps build artifact, guaranteeing 100% reproducibility.
* **Zero Network Failure Modes:** Container has zero runtime dependency on an external vector database connection pool or socket timeouts.

### Negative / Mitigations
* **Scalability Horizon:** If the knowledge base grew to >1,000,000 vectors, in-memory storage would exceed container RAM.
  * *Mitigation:* For a personal portfolio and technical documentation corpus, the total token count is well under 100k tokens. If scaling is ever required, the `HybridRetriever` interface abstracts the storage backend, allowing seamless migration to pgvector or Qdrant without refactoring application code.
