# ADR-009: LangGraph Stateful Agent Graph vs Linear RAG Pipelines

## Status
Accepted

## Context & Problem Statement
Basic RAG pipelines follow a rigid linear flow:
$$\text{Query} \longrightarrow \text{Embedding} \longrightarrow \text{Top-K Retrieval} \longrightarrow \text{LLM Synthesis}$$

While adequate for simple factual lookups, linear RAG fails when handling complex, multi-hop engineering questions, such as:
* *"Compare Brandon's Kubernetes migrations on AWS with his Kafka streaming architectures, and verify if he built any custom providers in Go."*
* Queries that require iterative query reformulation, context sufficiency checks, or adversarial defense screening before calling expensive LLM APIs.

Vanilla LangChain introduces excessive abstraction overhead, while custom monolithic loops quickly become hard to trace, test, and checkpoint.

## Decision
We implement a **LangGraph (`langgraph`) Stateful Multi-Agent Cognitive Graph** in `backend/app/services/langgraph_agent.py`:

1. **Typed State Machine (`AgentState`):**
   * Manages conversation turns, safety flags, decomposed sub-queries, retrieved knowledge nodes, reasoning traces, and the synthesized response.
2. **Cyclic Graph Architecture:**
   * **Node 1: `GuardrailNode`:** Evaluates input query safety, detecting prompt injection attempts and deflecting adversarial jailbreaks before triggering retrieval.
   * **Node 2: `HybridRetrieverNode`:** Interrogates the in-memory BM25 + Dense vector store to retrieve high-relevance chunks.
   * **Node 3: `ContextSufficiencyNode`:** Assesses whether the retrieved knowledge is sufficient to answer the prompt. If context is missing, it dynamically reformulates the query terms.
   * **Node 4: `SynthesisNode`:** Synthesizes the grounded answer, attributing citations and source anchors.
3. **Pluggable Architecture:**
   * The backend offers both direct low-latency linear streaming (for standard portfolio chat) and LangGraph multi-step reasoning (for deep cross-domain queries).

## Consequences & Trade-offs

### Positive
* **Cyclic Reasoning:** Allows the agent to loop and reformulate search strategies if initial retrieval results are insufficient.
* **Deterministic Guardrails:** Hard-coded security checks at the entry point of the graph guarantee zero tokens or API costs are wasted on prompt injection attacks.
* **Modern AI Engineering Signal:** Demonstrates proficiency in stateful graph checkpointing, conditional branching, and agentic workflows using industry-standard LangGraph.

### Negative / Mitigations
* **Latency Overhead:** Multi-step graph loops can introduce ~200–500ms additional cognitive latency compared to direct single-turn RAG.
  * *Mitigation:* The primary chat endpoint defaults to direct hybrid streaming, with LangGraph activated for multi-hop or analytical prompts.
