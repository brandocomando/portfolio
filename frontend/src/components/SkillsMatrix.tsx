import React from 'react';
import { Cpu } from 'lucide-react';
import { SkillCategory } from '../types';

const SKILL_GROUPS: SkillCategory[] = [
  {
    name: "Languages & Core Systems",
    skills: [
      { name: "Go (Golang)", proficiency: "Expert", context: "Kubernetes controllers (client-go), Terraform providers (Plugin SDK), Prometheus exporters." },
      { name: "Python", proficiency: "Expert", context: "FastAPI, PyTorch, Pydantic, data pipelines, automated browser agents (CDP)." },
      { name: "Bash / Shell", proficiency: "Expert", context: "Production Linux, CI/CD runner environments, POSIX automation." },
      { name: "TypeScript / React", proficiency: "Proficient", context: "Vite, React 19, modern component architectures, state management." },
      { name: "Lua", proficiency: "Proficient", context: "WezTerm plugins, Neovim configuration, terminal event hooks." }
    ]
  },
  {
    name: "Cloud & Infrastructure as Code",
    skills: [
      { name: "Terraform / OpenTofu", proficiency: "Expert", context: "Enterprise module authoring, multi-cloud state orchestration (AWS, GCP, Datadog, Snowflake, Confluent)." },
      { name: "Amazon Web Services (AWS)", proficiency: "Expert", context: "Multi-account AWS Organizations, EKS, VPC, App Mesh, MSK, IAM zero-trust." },
      { name: "Google Cloud Platform (GCP)", proficiency: "Expert", context: "Cloud Run, Artifact Registry, Firebase Hosting, Workload Identity Federation (WIF)." },
      { name: "FinOps & Cost Optimization", proficiency: "Expert", context: "Saved $10K+/month in enterprise infrastructure rationalization." }
    ]
  },
  {
    name: "Containers & Orchestration",
    skills: [
      { name: "Kubernetes (K8s)", proficiency: "Expert", context: "EKS cluster administration, ingress controllers, HPA, client-go operator authoring." },
      { name: "ArgoCD / GitOps", proficiency: "Expert", context: "Declarative continuous delivery, multi-cluster application sets, automated rollbacks." },
      { name: "Docker", proficiency: "Expert", context: "Multi-stage distroless/slim builds, rootless containers, OCI optimization." },
      { name: "Helm", proficiency: "Expert", context: "Parameterized chart authoring, dependency management, GitOps releases." },
      { name: "CI/CD & Automation", proficiency: "Expert", context: "GitHub Actions, Bitbucket migration (100+ repos, 99.8% reliability), reusable workflows, keyless OIDC/WIF." }
    ]
  },
  {
    name: "AI Infrastructure & MLOps",
    skills: [
      { name: "Autonomous Agent Fleets", proficiency: "Expert", context: "Local-first LLMs, multi-agent coordination (My Agentic Team), CDP web automation." },
      { name: "RAG & Retrieval Systems", proficiency: "Expert", context: "Hybrid search (BM25 sparse + dense embeddings), Reciprocal Rank Fusion (RRF), semantic chunking." },
      { name: "MLOps Evaluation Gates", proficiency: "Expert", context: "Continuous offline evaluation in CI/CD, LLM-as-a-judge, golden test datasets." },
      { name: "Local LLM Inference", proficiency: "Expert", context: "Ollama, quantization (GGUF), Laya sub-50ms decision engine." }
    ]
  },
  {
    name: "Data Platforms & Streaming",
    skills: [
      { name: "Apache Kafka & Confluent", proficiency: "Expert", context: "Enterprise event streaming, schema registry governance, broker migration from MSK." },
      { name: "Snowflake & Databricks", proficiency: "Proficient", context: "Data lakehouse infrastructure, role-based access control, Terraform automation." },
      { name: "DataOps & Data Contracts", proficiency: "Expert", context: "Medallion data architecture (Bronze/Silver/Gold), Pydantic v2 validation." }
    ]
  },
  {
    name: "Observability & Reliability (SRE)",
    skills: [
      { name: "Prometheus & Exporters", proficiency: "Expert", context: "Custom Go exporters, synthetic ingress probing, PromQL alerting rules, Grafana." },
      { name: "Datadog", proficiency: "Expert", context: "APM tracing, log management, synthetics, Terraform Datadog automation." },
      { name: "Service Mesh (App Mesh/Envoy)", proficiency: "Expert", context: "Mutual TLS (mTLS) enforcement, traffic routing, circuit breakers." }
    ]
  }
];

export const SkillsMatrix: React.FC = () => {
  return (
    <section id="skills" className="py-16 md:py-24 border-t border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 mb-3">
            <Cpu className="w-3.5 h-3.5" />
            <span>Technical Capabilities</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Production Skills & Domain Depth
          </h2>
          <p className="mt-3 text-slate-400 text-sm sm:text-base">
            Every skill backed by verifiable production proof-points, enterprise migrations, and open-source implementations.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {SKILL_GROUPS.map((group) => (
            <div
              key={group.name}
              className="p-6 rounded-2xl bg-slate-900/40 border border-slate-800/80 flex flex-col justify-between"
            >
              <div>
                <h3 className="text-base font-bold text-white mb-4 pb-2 border-b border-slate-800/60 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-cyan-400" />
                  {group.name}
                </h3>

                <div className="space-y-4">
                  {group.skills.map((s) => (
                    <div key={s.name} className="text-xs">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-semibold text-slate-200">{s.name}</span>
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                          s.proficiency === 'Expert'
                            ? 'bg-cyan-950 text-cyan-300 border border-cyan-800/50'
                            : 'bg-slate-800 text-slate-300'
                        }`}>
                          {s.proficiency}
                        </span>
                      </div>
                      <p className="text-slate-400 text-[11px] leading-relaxed">
                        {s.context}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
