import React, { useState } from 'react';
import {
  Database,
  Search,
  Cloud,
  CheckCircle2,
  Layers,
  ShieldCheck,
  Cpu,
  Zap,
  GitBranch,
  Bot,
  FileText,
  Lock,
  ArrowUpRight
} from 'lucide-react';

type TabKey =
  | 'dual_process'
  | 'context_agents'
  | 'lakehouse'
  | 'hybrid'
  | 'finops'
  | 'ci_temporal'
  | 'adr_registry';

interface AdrEntry {
  id: string;
  title: string;
  category: string;
  summary: string;
  file: string;
}

const ALL_ADRS: AdrEntry[] = [
  {
    id: "ADR-001",
    title: "Serverless Cloud Run vs GKE for Portfolio Platform",
    category: "Cloud Infrastructure",
    summary: "Selected serverless Google Cloud Run over managed GKE to achieve true scale-to-zero compute ($0.00/mo idle cost) while handling instantaneous traffic bursts with sub-second cold starts.",
    file: "docs/adr/ADR-001-serverless-cloud-run-vs-gke.md"
  },
  {
    id: "ADR-002",
    title: "Medallion Lakehouse Architecture for Profile Knowledge Store",
    category: "Data Engineering",
    summary: "Structured data pipelines into Bronze (raw immutable ingestion), Silver (Pydantic v2 validation & semantic chunking), and Gold (sparse BM25 + dense vector artifact) with cryptographic SHA-256 manifests.",
    file: "docs/adr/ADR-002-medallion-lakehouse-architecture.md"
  },
  {
    id: "ADR-003",
    title: "Hybrid Search with Reciprocal Rank Fusion (RRF)",
    category: "AI & Retrieval",
    summary: "Combined Okapi BM25 sparse keyword indexing with dense vector embeddings via Reciprocal Rank Fusion (k=60), ensuring exact technical term hits ('neo4j', 'App Mesh') alongside semantic intent.",
    file: "docs/adr/ADR-003-hybrid-search-dense-bm25-rrf.md"
  },
  {
    id: "ADR-004",
    title: "In-Memory Artifact Vector Store & Subword Embeddings",
    category: "AI Infrastructure",
    summary: "Bundled the pre-computed hybrid index and vector matrices directly inside Cloud Run container memory, achieving sub-2ms retrieval latency with zero external database network hops.",
    file: "docs/adr/ADR-004-in-memory-artifact-vector-store.md"
  },
  {
    id: "ADR-005",
    title: "Keyless CI/CD Deployment via Workload Identity Federation",
    category: "DevSecOps & IAM",
    summary: "Configured Workload Identity Federation between GitHub Actions and GCP IAM, authenticating via short-lived OIDC tokens and eliminating 100% of static JSON service account keys.",
    file: "docs/adr/ADR-005-workload-identity-federation.md"
  },
  {
    id: "ADR-006",
    title: "Server-Sent Events (SSE) Streaming for Agent Interaction",
    category: "API & Frontend",
    summary: "Selected Server-Sent Events (SSE) over WebSockets for one-way LLM token streaming, simplifying edge proxying and reducing connection state overhead over HTTP/2.",
    file: "docs/adr/ADR-006-server-sent-events-streaming.md"
  },
  {
    id: "ADR-007",
    title: "Tiered In-Memory Rate Limiting & Recruiter Lead Capture",
    category: "Security & FinOps",
    summary: "Implemented sliding window token-bucket rate limiting (5 queries/24h for anonymous visitors, 30 queries/24h for authenticated users via Firebase Auth) with Firestore lead persistence.",
    file: "docs/adr/ADR-007-tiered-rate-limiting-lead-capture.md"
  },
  {
    id: "ADR-008",
    title: "Durable Execution with Temporal for MLOps Pipelines & Sagas",
    category: "Distributed Systems",
    summary: "Adopted Temporal.io Python SDK for deterministic MLOps pipeline orchestration, automatic retries with jitter, stateful queries, and human-in-the-loop approval gates for $0/mo in CI/CD.",
    file: "docs/adr/ADR-008-durable-execution-temporal-agent-workflows.md"
  },
  {
    id: "ADR-009",
    title: "LangGraph Stateful Agent Graph vs Linear RAG Pipelines",
    category: "Agentic AI",
    summary: "Engineered a stateful multi-agent cognitive graph using LangGraph (GuardrailNode -> HybridRetrieverNode -> ContextSufficiencyNode -> SynthesisNode) with cyclic query reformulation for complex prompts.",
    file: "docs/adr/ADR-009-langgraph-stateful-multi-agent-reasoning.md"
  },
  {
    id: "ADR-010",
    title: "Dual-Process Cognitive Architecture (System 1 & System 2)",
    category: "Cognitive AI & FinOps",
    summary: "Separated sub-5ms in-memory deterministic routing and FinOps relevance gating (System 1) from grounded Gemini 3.8 Flash generative streaming (System 2), blocking 100% of LLM costs on off-topic and bot traffic.",
    file: "docs/adr/ADR-010-dual-process-cognitive-architecture.md"
  },
  {
    id: "ADR-011",
    title: "Conversational Context Continuity & Retrieval Query De-Pollution",
    category: "Context Engine",
    summary: "Built an asymmetric contextual query engine that isolates user selections, prevents historical assistant text from poisoning retrieval ranking, and normalizes 12-turn dialog schema.",
    file: "docs/adr/ADR-011-conversational-context-continuity.md"
  }
];

export const ArchitectureShowcase: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabKey>('dual_process');

  return (
    <section id="architecture" className="py-16 md:py-24 border-t border-slate-800/80 bg-slate-900/30">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-12">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-indigo-950/60 border border-indigo-800/60 text-indigo-300 mb-3">
            <Layers className="w-3.5 h-3.5" />
            <span>Production System Design</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            How This Platform Is Engineered
          </h2>
          <p className="mt-3 text-slate-400 text-sm sm:text-base">
            Zero toy scripts. Engineered as an enterprise distributed system following strict FinOps,
            DataOps contracts, dual-process cognitive routing, and formal Architecture Decision Records (ADRs).
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex flex-wrap justify-center gap-2 p-1.5 bg-slate-900/80 rounded-2xl border border-slate-800 max-w-5xl mx-auto mb-8 shadow-sm">
          <button
            onClick={() => setActiveTab('dual_process')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all ${
              activeTab === 'dual_process'
                ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Zap className="w-4 h-4" />
            <span>System 1 & 2 Cognitive Design</span>
          </button>

          <button
            onClick={() => setActiveTab('context_agents')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all ${
              activeTab === 'context_agents'
                ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Bot className="w-4 h-4" />
            <span>Context Continuity & Agent Graph</span>
          </button>

          <button
            onClick={() => setActiveTab('lakehouse')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all ${
              activeTab === 'lakehouse'
                ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Database className="w-4 h-4" />
            <span>Medallion Lakehouse</span>
          </button>

          <button
            onClick={() => setActiveTab('hybrid')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all ${
              activeTab === 'hybrid'
                ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Search className="w-4 h-4" />
            <span>Hybrid Search (Dense+BM25)</span>
          </button>

          <button
            onClick={() => setActiveTab('finops')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all ${
              activeTab === 'finops'
                ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Cloud className="w-4 h-4" />
            <span>Scale-to-Zero GCP Infra</span>
          </button>

          <button
            onClick={() => setActiveTab('ci_temporal')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all ${
              activeTab === 'ci_temporal'
                ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>MLOps CI & Temporal Sagas</span>
          </button>

          <button
            onClick={() => setActiveTab('adr_registry')}
            className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs sm:text-sm font-medium transition-all ${
              activeTab === 'adr_registry'
                ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Full ADR Registry (001–011)</span>
          </button>
        </div>

        {/* Tab Content Cards */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 sm:p-8 backdrop-blur-sm max-w-5xl mx-auto shadow-xl">
          {/* TAB 1: DUAL-PROCESS COGNITIVE ARCHITECTURE (ADR-010) */}
          {activeTab === 'dual_process' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-2">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Zap className="w-5 h-5 text-indigo-400" />
                    Dual-Process Cognitive Architecture (System 1 & System 2)
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Ref: docs/adr/ADR-010-dual-process-cognitive-architecture.md</p>
                </div>
                <span className="self-start sm:self-auto px-2.5 py-1 text-xs font-mono rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800/60">
                  Cognitive AI / FinOps
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-xs text-slate-300 leading-relaxed">
                <p>
                  Inspired by Daniel Kahneman's cognitive framework, this platform completely decouples instantaneous,
                  deterministic decision-making (<strong className="text-indigo-300 font-semibold">System 1</strong>) from
                  probabilistic generative LLM synthesis (<strong className="text-cyan-300 font-semibold">System 2</strong>).
                  This guarantees rigorous security guardrails and prevents Denial-of-Wallet attacks on public traffic.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {/* System 1 Card */}
                <div className="p-5 rounded-xl bg-slate-950/60 border border-indigo-900/40 flex flex-col justify-between">
                  <div>
                    <div className="text-indigo-400 font-bold text-sm mb-3 flex items-center gap-2">
                      <Cpu className="w-4 h-4 text-indigo-400" />
                      System 1: Sub-5ms In-Memory Fast Path & Gating
                    </div>
                    <ul className="space-y-2 text-slate-300">
                      <li className="flex items-start gap-2">
                        <Lock className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                        <span><strong>Security Guardrails:</strong> Regex and AST checks intercept prompt injection, roleplay escape, and jailbreak payloads before any retrieval or external API invocations.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <ShieldCheck className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                        <span><strong>Strict Privacy Boundary:</strong> Redacts inquiries about private personal contacts, salary, and home address, redirecting visitors to the audited contact modal.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Bot className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                        <span><strong>Anti-Hijacking Code Gate:</strong> Rejects arbitrary script-writing, LeetCode, or generic algorithm requests, steering conversations strictly to Brandon's engineering domain.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <CheckCircle2 className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                        <span><strong>Verified Profile Facts:</strong> Instantly streams verified facts from <code>personal.yaml</code> (location preferences, remote/hybrid criteria, pets, hobbies) with &lt;5ms TTFT.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Zap className="w-3.5 h-3.5 text-indigo-400 shrink-0 mt-0.5" />
                        <span><strong>FinOps Relevance Gating:</strong> Deflects out-of-scope non-engineering queries (dense score &lt; 0.135 and no BM25 hit) with 0 external Gemini API calls.</span>
                      </li>
                    </ul>
                  </div>
                  <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] font-mono text-indigo-300">
                    Latency: &lt;5ms | Cost: $0.00 | Handled locally in RAM
                  </div>
                </div>

                {/* System 2 Card */}
                <div className="p-5 rounded-xl bg-slate-950/60 border border-cyan-900/40 flex flex-col justify-between">
                  <div>
                    <div className="text-cyan-400 font-bold text-sm mb-3 flex items-center gap-2">
                      <Bot className="w-4 h-4 text-cyan-400" />
                      System 2: Grounded Gemini 3.8 Flash Orchestration
                    </div>
                    <ul className="space-y-2 text-slate-300">
                      <li className="flex items-start gap-2">
                        <Database className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                        <span><strong>Context-Grounded Synthesis:</strong> Invoked only after System 1 relevance validation, streaming responses strictly grounded in the top Gold retrieval chunks.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <GitBranch className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                        <span><strong>Turn Normalization:</strong> Enforces a strict 12-turn sliding window, cleans leading greeting turns, and merges same-role turns into the required alternating schema.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <Layers className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                        <span><strong>Zero Hallucination Anchors:</strong> System prompt boundaries restrict claims strictly to verified career proof-points and technical architectural choices.</span>
                      </li>
                      <li className="flex items-start gap-2">
                        <ShieldCheck className="w-3.5 h-3.5 text-cyan-400 shrink-0 mt-0.5" />
                        <span><strong>Deterministic Local Fallback:</strong> If Google GenAI upstream drops or rate limits, the backend automatically transitions to local in-memory synthesis.</span>
                      </li>
                    </ul>
                  </div>
                  <div className="mt-4 pt-3 border-t border-slate-800 text-[11px] font-mono text-cyan-300">
                    Engine: Gemini 3.8 Flash | Token Stream: SSE over HTTP/2
                  </div>
                </div>
              </div>

              <div className="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-xl text-xs text-emerald-300 flex items-center gap-2 font-mono">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>FinOps Impact: 100% of bot spam, adversarial jailbreaks, and off-topic queries deflected with zero LLM billing.</span>
              </div>
            </div>
          )}

          {/* TAB 2: CONTEXT CONTINUITY & AGENT GRAPH (ADR-011 & ADR-009) */}
          {activeTab === 'context_agents' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-2">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Bot className="w-5 h-5 text-indigo-400" />
                    Conversational Context Continuity & Stateful Agent Graph
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Ref: docs/adr/ADR-011-conversational-context-continuity.md & ADR-009</p>
                </div>
                <span className="self-start sm:self-auto px-2.5 py-1 text-xs font-mono rounded bg-indigo-950/80 text-indigo-300 border border-indigo-800/60">
                  Context Engine / LangGraph
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-5 rounded-xl bg-slate-950/60 border border-indigo-900/40">
                  <h4 className="font-bold text-indigo-300 text-sm mb-3 flex items-center gap-2">
                    <Search className="w-4 h-4 text-indigo-400" />
                    Asymmetric Query De-Pollution (ADR-011)
                  </h4>
                  <p className="text-slate-400 mb-3">
                    Naive RAG concatenates entire chat histories into search queries, causing previous assistant responses
                    to drown out the topic the user just clicked. Our asymmetric engine isolates user intent:
                  </p>
                  <div className="p-3 bg-slate-900 rounded-lg border border-slate-800 font-mono text-[11px] text-indigo-200 mb-3 space-y-1">
                    <div>// Topic selection query formula:</div>
                    <code className="text-cyan-300">Query = SelectedOption * 2 + InitialUserQuery</code>
                    <div className="text-slate-500">// Prior assistant narrative body is strictly excluded</div>
                  </div>
                  <ul className="space-y-1.5 text-slate-300">
                    <li>• <strong>Affirmative Continuations:</strong> Handles bare <em>"yes"</em> or <em>"tell me more"</em> by harvesting offered topics without expensive LLM query-rewriter hops.</li>
                    <li>• <strong>Fuzzy Typo Matching:</strong> In-memory SequenceMatcher (≥ 0.8) accommodates typos like <em>"gitopss"</em> or <em>"securirty"</em>.</li>
                    <li>• <strong>Sub-Millisecond Speed:</strong> Resolves in &lt;1ms in Cloud Run memory.</li>
                  </ul>
                </div>

                <div className="p-5 rounded-xl bg-slate-950/60 border border-indigo-900/40">
                  <h4 className="font-bold text-indigo-300 text-sm mb-3 flex items-center gap-2">
                    <GitBranch className="w-4 h-4 text-indigo-400" />
                    LangGraph Stateful Cognitive Graph (ADR-009)
                  </h4>
                  <p className="text-slate-400 mb-3">
                    For multi-hop questions requiring cross-domain comparisons, the backend switches from linear RAG to a stateful
                    LangGraph state machine (<code>AgentState</code>):
                  </p>
                  <div className="space-y-2 font-mono text-[11px]">
                    <div className="p-2 rounded bg-slate-900/80 border border-slate-800 text-slate-300 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-sky-200" />
                      <span>Node 1: <strong>GuardrailNode</strong> (Pre-retrieval safety screening)</span>
                    </div>
                    <div className="p-2 rounded bg-slate-900/80 border border-slate-800 text-slate-300 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-cyan-400" />
                      <span>Node 2: <strong>HybridRetrieverNode</strong> (BM25 + Dense RRF)</span>
                    </div>
                    <div className="p-2 rounded bg-slate-900/80 border border-slate-800 text-slate-300 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-indigo-400" />
                      <span>Node 3: <strong>ContextSufficiencyNode</strong> (Query reformulation loop)</span>
                    </div>
                    <div className="p-2 rounded bg-slate-900/80 border border-slate-800 text-slate-300 flex items-center gap-2">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      <span>Node 4: <strong>SynthesisNode</strong> (Grounded response generation)</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: MEDALLION LAKEHOUSE (ADR-002) */}
          {activeTab === 'lakehouse' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-2">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Database className="w-5 h-5 text-cyan-400" />
                    Medallion Architecture (Bronze → Silver → Gold)
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Ref: docs/adr/ADR-002-medallion-lakehouse-architecture.md</p>
                </div>
                <span className="self-start sm:self-auto px-2.5 py-1 text-xs font-mono rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                  Data Platform
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-800">
                  <div className="text-sky-400 font-bold text-sm mb-2 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-sky-400" /> Bronze (Raw)
                  </div>
                  <p className="text-slate-400 mb-2">Immutable ingestion of GitHub REST API & raw profile YAMLs with SHA-256 source hashing.</p>
                  <div className="text-slate-500">mlops/data/bronze/</div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-700/60">
                  <div className="text-slate-200 font-bold text-sm mb-2 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-slate-400" /> Silver (DataOps)
                  </div>
                  <p className="text-slate-400 mb-2">Pydantic v2 data contract validation, AST semantic chunking, and metadata tagging.</p>
                  <div className="text-slate-500">mlops/data/silver/</div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-cyan-900/30">
                  <div className="text-cyan-400 font-bold text-sm mb-2 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-cyan-400" /> Gold (Retrieval)
                  </div>
                  <p className="text-slate-400 mb-2">Sparse Okapi BM25 index + subword dense embeddings bundled with cryptographic manifest.</p>
                  <div className="text-slate-500">mlops/data/gold/</div>
                </div>
              </div>

              <p className="text-sm text-slate-300 leading-relaxed">
                By strictly isolating raw ingestion from chunking and vectorization, any schema change or re-indexing
                is 100% deterministic, reproducible, and verifiable via cryptographic checksums without hitting external APIs.
              </p>
            </div>
          )}

          {/* TAB 4: HYBRID SEARCH & RRF (ADR-003 & ADR-004) */}
          {activeTab === 'hybrid' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-2">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Search className="w-5 h-5 text-indigo-400" />
                    Hybrid Search with Reciprocal Rank Fusion (RRF)
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Ref: docs/adr/ADR-003-hybrid-search-dense-bm25-rrf.md & ADR-004</p>
                </div>
                <span className="self-start sm:self-auto px-2.5 py-1 text-xs font-mono rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                  AI Infra
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 font-mono text-xs text-indigo-300">
                <div className="text-slate-400 mb-2">// Reciprocal Rank Fusion Algorithm (k = 60)</div>
                <code>RRF_Score(d) = ∑ [ 1 / (60 + Rank_dense(d)) + 1 / (60 + Rank_sparse(d)) ]</code>
                <div className="mt-2 text-slate-400">Combines Dense Semantic Vector Similarity + Okapi BM25 Inverted Index without arbitrary score normalization.</div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs text-slate-300">
                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800">
                  <h4 className="font-bold text-white mb-1">Why BM25 is Crucial</h4>
                  <p className="text-slate-400">Dense vectors fail on niche tech terms (e.g. "neo4j", "node_exporter", "App Mesh"). BM25 guarantees 100% exact keyword hits.</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-800/40 border border-slate-800">
                  <h4 className="font-bold text-white mb-1">In-Memory Sub-2ms Latency</h4>
                  <p className="text-slate-400">Pre-computed NumPy dot-products and memory-mapped inverted index run directly in Cloud Run memory with zero DB network hops.</p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: SCALE-TO-ZERO INFRA & FINOPS (ADR-001 & ADR-005) */}
          {activeTab === 'finops' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-2">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Cloud className="w-5 h-5 text-emerald-400" />
                    FinOps Serverless Scale-to-Zero Architecture
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Ref: docs/adr/ADR-001-serverless-cloud-run-vs-gke.md & ADR-005</p>
                </div>
                <span className="self-start sm:self-auto px-2.5 py-1 text-xs font-mono rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                  Platform Eng
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-slate-950/60 border border-emerald-900/30">
                  <div className="text-emerald-400 font-bold mb-1">Firebase Hosting (CDN)</div>
                  <p className="text-slate-400">Global edge caching, free managed SSL, zero $18/mo Google Cloud Load Balancer idle fee trap.</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-emerald-900/30">
                  <div className="text-emerald-400 font-bold mb-1">FastAPI on Cloud Run</div>
                  <p className="text-slate-400">Scales strictly to 0 instances when idle. Free tier includes 2M requests and 360k vCPU-seconds/mo.</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-emerald-900/30">
                  <div className="text-emerald-400 font-bold mb-1">Workload Identity (WIF)</div>
                  <p className="text-slate-400">Short-lived OIDC tokens for GitHub Actions CI/CD. Zero static JSON service account keys.</p>
                </div>
              </div>

              <div className="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-xl text-xs text-emerald-300 flex items-center gap-2 font-mono">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Total Fixed Infrastructure Idle Cost: $0.00/month | True serverless FinOps architecture.</span>
              </div>
            </div>
          )}

          {/* TAB 6: MLOPS EVALUATION GATES & TEMPORAL SAGAS (ADR-008) */}
          {activeTab === 'ci_temporal' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-2">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-cyan-400" />
                    Automated Continuous Evaluation & Temporal Durable Sagas
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Ref: docs/adr/ADR-008-durable-execution-temporal-agent-workflows.md</p>
                </div>
                <span className="self-start sm:self-auto px-2.5 py-1 text-xs font-mono rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                  MLOps & Reliability
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                {/* Continuous Evaluation Benchmark */}
                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 font-mono space-y-2">
                  <div className="text-cyan-400 font-bold text-sm mb-2 flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4" /> Golden Dataset Quality Gate
                  </div>
                  <div className="text-slate-400">// Checked on every commit via evaluate_agent.py:</div>
                  <div className="flex justify-between text-slate-200">
                    <span>• Top-3 Retrieval Hit Rate:</span>
                    <span className="text-emerald-400 font-bold">92.9% (Target ≥ 85%)</span>
                  </div>
                  <div className="flex justify-between text-slate-200">
                    <span>• Mean Reciprocal Rank (MRR):</span>
                    <span className="text-emerald-400 font-bold">0.821 (Target ≥ 0.70)</span>
                  </div>
                  <div className="flex justify-between text-slate-200">
                    <span>• Keyword & Entity Recall:</span>
                    <span className="text-emerald-400 font-bold">95.4%</span>
                  </div>
                  <div className="flex justify-between text-slate-200">
                    <span>• Adversarial Guardrail Deflection:</span>
                    <span className="text-emerald-400 font-bold">100.0% (Target 100%)</span>
                  </div>
                </div>

                {/* Temporal Sagas */}
                <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 space-y-2">
                  <div className="text-cyan-400 font-bold text-sm mb-2 flex items-center gap-1.5">
                    <Layers className="w-4 h-4" /> Temporal.io Durable Sagas (ADR-008)
                  </div>
                  <p className="text-slate-300">
                    Orchestrates MLOps synchronization across distributed steps (<code>ingest_bronze</code> → <code>transform_silver</code> → <code>build_gold</code> → <code>evaluate</code>):
                  </p>
                  <ul className="space-y-1.5 text-slate-400">
                    <li>• <strong>Exponential Retry with Jitter:</strong> Automatically overcomes transient network & API rate limits.</li>
                    <li>• <strong>Human-in-the-Loop Gate:</strong> Borderline evaluation scores suspend execution and wait up to 24h for signed approval signals before deploying.</li>
                    <li>• <strong>$0/mo Ephemeral CI/CD Runner:</strong> Runs in GitHub Actions via <code>temporalio.testing</code>.</li>
                  </ul>
                </div>
              </div>

              <p className="text-sm text-slate-300 leading-relaxed">
                If an index update causes retrieval accuracy or guardrail safety to degrade, the GitHub Actions
                quality gate automatically halts deployment, preventing silent retrieval regressions.
              </p>
            </div>
          )}

          {/* TAB 7: COMPLETE ARCHITECTURE DECISION RECORD REGISTRY */}
          {activeTab === 'adr_registry' && (
            <div className="space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-800 pb-4 gap-2">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <FileText className="w-5 h-5 text-indigo-400" />
                    Architecture Decision Records Registry (ADR-001 to ADR-011)
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Formal architectural governance and immutable trade-off evaluations</p>
                </div>
                <span className="self-start sm:self-auto px-2.5 py-1 text-xs font-mono rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                  11 Accepted Records
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {ALL_ADRS.map((adr) => (
                  <div
                    key={adr.id}
                    className="p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-center justify-between mb-1.5">
                        <span className="text-xs font-mono font-bold text-cyan-400 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/40">
                          {adr.id}
                        </span>
                        <span className="text-[11px] font-mono text-slate-400">
                          {adr.category}
                        </span>
                      </div>
                      <h4 className="text-sm font-bold text-white mb-1.5">
                        {adr.title}
                      </h4>
                      <p className="text-xs text-slate-400 leading-relaxed">
                        {adr.summary}
                      </p>
                    </div>
                    <div className="mt-3 pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] font-mono text-slate-500">
                      <span>Status: Accepted</span>
                      <span className="text-slate-400 flex items-center gap-1">
                        {adr.file.split('/').pop()}
                        <ArrowUpRight className="w-3 h-3 text-cyan-400" />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
