import React from 'react';
import { Cpu } from 'lucide-react';
import { SkillCategory } from '../types';

const SKILL_GROUPS: SkillCategory[] = [
  {
    name: "Languages & Core Systems",
    skills: [
      { name: "Go (Golang)", proficiency: "Expert", context: "Kubernetes controllers (client-go), Terraform providers (Plugin SDK), Prometheus exporters, CLI daemons." },
      { name: "Python", proficiency: "Expert", context: "FastAPI, PyTorch, Pydantic, data pipelines, automated browser agents (CDP)." },
      { name: "Bash / POSIX Shell", proficiency: "Expert", context: "Production Linux systems, CI/CD runner environments, POSIX automation." },
      { name: "TypeScript / React", proficiency: "Proficient", context: "Vite, React 19, modern component architectures, state management." },
      { name: "SQL", proficiency: "Proficient", context: "PostgreSQL query tuning, Aurora RDS, Snowflake modeling." },
      { name: "Lua", proficiency: "Proficient", context: "WezTerm plugins, Neovim configuration, terminal event hooks." }
    ]
  },
  {
    name: "Cloud & Multi-Cloud Architecture",
    skills: [
      { name: "Amazon Web Services (AWS)", proficiency: "Expert", context: "Multi-account AWS Organizations, EKS, ECS Fargate, VPC, Transit Gateway, ALB, RDS Aurora, S3, IAM, SQS." },
      { name: "Google Cloud Platform (GCP)", proficiency: "Expert", context: "Cloud Run, Artifact Registry, Firebase Hosting, Workload Identity Federation (WIF), IAM, Cloud Storage." },
      { name: "Microsoft Azure", proficiency: "Familiar", context: "Cloud-agnostic architecture, AKS, Azure Blob, Azure DevOps, multi-cloud Terraform patterns." },
      { name: "Multi-Cloud Governance & IAM", proficiency: "Expert", context: "Unified IAM policies, cross-cloud state orchestration, egress cost mitigation, multi-account isolation." }
    ]
  },
  {
    name: "Containers & Orchestration",
    skills: [
      { name: "Kubernetes (K8s) & EKS", proficiency: "Expert", context: "EKS/GKE cluster administration, controllers/operators (client-go), ingress, HPA, Karpenter, CRDs (previously CKA certified)." },
      { name: "ArgoCD / GitOps", proficiency: "Expert", context: "Declarative continuous delivery, multi-cluster application sets, automated sync, rollbacks, ArgoCD Image Updater." },
      { name: "Docker & Container Runtimes", proficiency: "Expert", context: "Multi-stage distroless/slim builds, rootless containers, OCI optimization, Docker Compose local dev." },
      { name: "Helm", proficiency: "Expert", context: "Parameterized chart authoring, dependency management, GitOps releases." },
      { name: "Cluster Autoscaling (Karpenter/HPA)", proficiency: "Expert", context: "Dynamic node provisioning, horizontal pod autoscaling, disruption budgets, graceful termination." }
    ]
  },
  {
    name: "CI/CD & Delivery Engineering",
    skills: [
      { name: "GitHub Actions", proficiency: "Expert", context: "Enterprise pipeline authoring from scratch, reusable workflows, Linux runners, keyless OIDC/WIF." },
      { name: "Jenkins & Legacy Migration", proficiency: "Proficient", context: "Jenkins build environments, runner scaling, migrated 100+ repos from Bitbucket & Jenkins to GitHub Actions (99.8% reliability)." },
      { name: "GitLab CI & Alternative Runners", proficiency: "Proficient", context: "Declarative pipeline-as-code, runner autoscaling, containerized testing stages." }
    ]
  },
  {
    name: "Infrastructure as Code & Automation",
    skills: [
      { name: "Terraform / OpenTofu", proficiency: "Expert", context: "Enterprise module authoring, multi-cloud state orchestration (AWS, GCP, Datadog, Snowflake), custom Go providers." },
      { name: "Pulumi & AWS CDK", proficiency: "Familiar", context: "Programmatic IaC concepts, TypeScript/Python IaC SDKs, rapid adoption capability." },
      { name: "Ansible & Config Management", proficiency: "Proficient", context: "Host provisioning and system automation; emphasizes modern immutable infrastructure (Terraform + Docker + K8s)." }
    ]
  },
  {
    name: "Data Platforms & Distributed Storage",
    skills: [
      { name: "Apache Kafka & Confluent", proficiency: "Expert", context: "Enterprise event streaming, schema registry governance (Avro/Protobuf), broker migration from MSK." },
      { name: "Snowflake & Databricks", proficiency: "Proficient", context: "Data lakehouse infrastructure, Spark pipelines, role-based access control, Terraform automation." },
      { name: "NoSQL (Aerospike & Cassandra)", proficiency: "Proficient", context: "High-throughput distributed NoSQL data stores with Aerospike and Apache Cassandra; Redis caching." },
      { name: "PostgreSQL & AWS Aurora", proficiency: "Proficient", context: "Relational schema design, query tuning, Aurora cluster provisioning, replication, failover." }
    ]
  },
  {
    name: "Cloud Security, DevSecOps & Compliance",
    skills: [
      { name: "Zero-Trust & Identity (WIF / OIDC)", proficiency: "Expert", context: "Keyless cloud authentication, least-privilege IAM policies, AWS Organizations SCPs, mTLS encryption." },
      { name: "Software Supply Chain Security", proficiency: "Expert", context: "Container vulnerability scanning (Trivy, Snyk), Software Bill of Materials (SBOM), image provenance." },
      { name: "Compliance (SOC 2, HIPAA, ISO 27001)", proficiency: "Proficient", context: "Engineered automated controls and supplied technical audit evidence to meet SOC 2 Type 2, HIPAA, and ISO 27001." }
    ]
  },
  {
    name: "Observability, SRE & Reliability",
    skills: [
      { name: "Prometheus & Exporters", proficiency: "Expert", context: "Custom Go exporters, synthetic ingress probing, PromQL alerting rules, metric aggregations." },
      { name: "Datadog", proficiency: "Expert", context: "APM tracing, log management, synthetics, Terraform Datadog automation." },
      { name: "Grafana", proficiency: "Expert", context: "Custom dashboards, dashboard-as-code provisioning, LogQL/PromQL visualizations, and multi-datasource alerting." },
      { name: "OpenTelemetry (OTel)", proficiency: "Expert", context: "Distributed trace context propagation (W3C traceparent), OTel collector pipelines, and span creation for microservices." },
      { name: "SRE & Incident Management", proficiency: "Expert", context: "SLOs/SLIs, error budgets, blameless postmortems, automated runbooks, on-call rotation leadership." }
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
    name: "Platform Engineering & DevEx",
    skills: [
      { name: "Internal Developer Platforms & Paved Roads", proficiency: "Expert", context: "Opinionated self-service infrastructure ('easy path is safe path'), service templates, PR preview environments." },
      { name: "Developer Tooling & CLIs", proficiency: "Expert", context: "Authoring high-performance developer CLIs, SDKs, and automation tooling in Go and Python." },
      { name: "Developer Portals (Backstage / Port)", proficiency: "Familiar", context: "Architectural understanding of developer portals and service catalogs; eager to lead a full IDP rollout." }
    ]
  },
  {
    name: "Networking, Service Mesh & Traffic",
    skills: [
      { name: "AWS App Mesh & Envoy Proxy", proficiency: "Expert", context: "Mutual TLS (mTLS) enforcement, service graph cryptographic identity, circuit breakers, Envoy access logging." },
      { name: "Kubernetes Ingress & Gateway API", proficiency: "Expert", context: "Declarative ingress routing, ALB/NLB controllers, automated TLS cert management with cert-manager." },
      { name: "Cloud Network Topologies (VPC / TGW)", proficiency: "Expert", context: "Multi-account VPC peering, AWS Transit Gateway, PrivateLink endpoints, and Route 53 private zones." }
    ]
  },
  {
    name: "FinOps & Cloud Cost Optimization",
    skills: [
      { name: "Karpenter & Dynamic Spot Scaling", proficiency: "Expert", context: "Just-in-time worker node provisioning, graceful Spot interruption handling, bin-packing optimization." },
      { name: "FOCUS Spec & Unit Economics", proficiency: "Expert", context: "FinOps Open Cost and Usage Specification, showback/chargeback tagging, Datadog FinOps dashboards." },
      { name: "Scale-to-Zero Architectures", proficiency: "Expert", context: "Serverless Cloud Run concurrency tuning, multi-tier rate limiting, zero-idle cost GCP infrastructure." },
      { name: "Cloud Cost Rationalization ($10K+/mo)", proficiency: "Expert", context: "Compute rightsizing, data retention lifecycle policies, eliminated $10K+/mo in cloud infrastructure costs." }
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
