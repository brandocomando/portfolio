import React, { useState } from 'react';
import { Database, Search, Cloud, CheckCircle2, Layers, ShieldCheck } from 'lucide-react';

export const ArchitectureShowcase: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'lakehouse' | 'hybrid' | 'finops' | 'ci_gate'>('lakehouse');

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
            Zero toy scripts. Built as an end-to-end distributed system following strict FinOps,
            DataOps contracts, and automated evaluation gates.
          </p>
        </div>

        {/* Tab Navigation */}
        <div className="flex flex-wrap justify-center gap-2 p-1.5 bg-slate-900/80 rounded-2xl border border-slate-800 max-w-3xl mx-auto mb-8">
          <button
            onClick={() => setActiveTab('lakehouse')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-all ${
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
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-all ${
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
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-all ${
              activeTab === 'finops'
                ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <Cloud className="w-4 h-4" />
            <span>Scale-to-Zero GCP Infra</span>
          </button>

          <button
            onClick={() => setActiveTab('ci_gate')}
            className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs sm:text-sm font-medium transition-all ${
              activeTab === 'ci_gate'
                ? 'bg-cyan-500 text-white shadow-md shadow-cyan-500/20'
                : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
            }`}
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>MLOps Evaluation Gate</span>
          </button>
        </div>

        {/* Tab Content Cards */}
        <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 sm:p-8 backdrop-blur-sm max-w-4xl mx-auto shadow-xl">
          {activeTab === 'lakehouse' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Database className="w-5 h-5 text-cyan-400" />
                    Medallion Architecture (Bronze → Silver → Gold)
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Ref: docs/adr/ADR-002-medallion-lakehouse-architecture.md</p>
                </div>
                <span className="px-2.5 py-1 text-xs font-mono rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                  Data Platform
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 font-mono text-xs">
                <div className="p-4 rounded-xl bg-slate-950/60 border border-amber-900/30">
                  <div className="text-amber-400 font-bold text-sm mb-2 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-amber-400" /> Bronze (Raw)
                  </div>
                  <p className="text-slate-400 mb-2">Immutable ingestion of GitHub REST API & raw YAML career files with SHA-256 source hashing.</p>
                  <div className="text-slate-500">mlops/data/bronze/</div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-slate-700/60">
                  <div className="text-slate-200 font-bold text-sm mb-2 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-slate-400" /> Silver (DataOps)
                  </div>
                  <p className="text-slate-400 mb-2">Pydantic v2 data contract validation, AST semantic chunking, and tag normalization.</p>
                  <div className="text-slate-500">mlops/data/silver/</div>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-cyan-900/30">
                  <div className="text-cyan-400 font-bold text-sm mb-2 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-cyan-400" /> Gold (Retrieval)
                  </div>
                  <p className="text-slate-400 mb-2">Sparse BM25 index + subword dense embeddings bundled with cryptographic manifest.</p>
                  <div className="text-slate-500">mlops/data/gold/</div>
                </div>
              </div>

              <p className="text-sm text-slate-300 leading-relaxed">
                By isolating raw ingestion from chunking and vectorization, any schema change or re-indexing
                is 100% deterministic and reproducible without hitting external APIs.
              </p>
            </div>
          )}

          {activeTab === 'hybrid' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Search className="w-5 h-5 text-indigo-400" />
                    Hybrid Search with Reciprocal Rank Fusion (RRF)
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Ref: docs/adr/ADR-003-hybrid-search-dense-bm25-rrf.md</p>
                </div>
                <span className="px-2.5 py-1 text-xs font-mono rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
                  AI Infra
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 font-mono text-xs text-indigo-300">
                <div className="text-slate-400 mb-2">// Reciprocal Rank Fusion Algorithm</div>
                <code>RRF_Score(d) = ∑ ( 1 / (60 + Rank_system(d)) )</code>
                <div className="mt-2 text-slate-400">Combines Dense Vector Ranking + Okapi BM25 Sparse Ranking without arbitrary score normalization.</div>
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

          {activeTab === 'finops' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <Cloud className="w-5 h-5 text-emerald-400" />
                    FinOps Serverless Scale-to-Zero Architecture
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Ref: docs/adr/ADR-001-serverless-cloud-run-vs-gke.md</p>
                </div>
                <span className="px-2.5 py-1 text-xs font-mono rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                  Platform Eng
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                <div className="p-4 rounded-xl bg-slate-950/60 border border-emerald-900/30">
                  <div className="text-emerald-400 font-bold mb-1">Firebase Hosting (CDN)</div>
                  <p className="text-slate-400">Global edge caching, free managed SSL, zero $18/mo HTTPS forwarding rule trap.</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-emerald-900/30">
                  <div className="text-emerald-400 font-bold mb-1">FastAPI on Cloud Run</div>
                  <p className="text-slate-400">Scales to 0 instances when idle. Free tier includes 2M requests and 360k vCPU-seconds/mo.</p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/60 border border-emerald-900/30">
                  <div className="text-emerald-400 font-bold mb-1">Workload Identity (WIF)</div>
                  <p className="text-slate-400">Short-lived OIDC tokens for GitHub Actions. Zero static JSON service account keys.</p>
                </div>
              </div>

              <div className="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-xl text-xs text-emerald-300 flex items-center gap-2 font-mono">
                <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                <span>Total Monthly Fixed Cost: $0.00 | Pay only for active Gemini token streaming.</span>
              </div>
            </div>
          )}

          {activeTab === 'ci_gate' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-4">
                <div>
                  <h3 className="text-xl font-bold text-white flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-cyan-400" />
                    Automated Continuous Evaluation CI Gate
                  </h3>
                  <p className="text-xs text-slate-400 font-mono mt-1">Ref: mlops/eval/evaluate_agent.py</p>
                </div>
                <span className="px-2.5 py-1 text-xs font-mono rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                  MLOps
                </span>
              </div>

              <div className="p-4 rounded-xl bg-slate-950/80 border border-slate-800 font-mono text-xs space-y-2">
                <div className="text-slate-400">// Benchmark Metrics Checked on Every Push to Main:</div>
                <div className="flex justify-between text-slate-200">
                  <span>• Top-3 Retrieval Hit Rate:</span>
                  <span className="text-emerald-400 font-bold">90.9% (Target ≥ 85%)</span>
                </div>
                <div className="flex justify-between text-slate-200">
                  <span>• Mean Reciprocal Rank (MRR):</span>
                  <span className="text-emerald-400 font-bold">0.864 (Target ≥ 0.70)</span>
                </div>
                <div className="flex justify-between text-slate-200">
                  <span>• Keyword & Entity Recall:</span>
                  <span className="text-emerald-400 font-bold">98.0%</span>
                </div>
                <div className="flex justify-between text-slate-200">
                  <span>• Adversarial Guardrail Deflection:</span>
                  <span className="text-emerald-400 font-bold">100.0% (Target 100%)</span>
                </div>
              </div>

              <p className="text-sm text-slate-300 leading-relaxed">
                If an index update causes retrieval accuracy or guardrail safety to degrade, the GitHub Actions
                pipeline triggers a non-zero exit code and automatically aborts the Cloud Run deployment.
              </p>
            </div>
          )}
        </div>
      </div>
    </section>
  );
};
