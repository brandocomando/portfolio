import React from 'react';
import { Briefcase, Check } from 'lucide-react';
import { Milestone } from '../types';

const MILESTONES: Milestone[] = [
  {
    id: "exp-eks-migration",
    category: "Distributed Systems & Kubernetes",
    title: "Large-Scale Microservices Migration to EKS & GitOps",
    role: "Lead Platform Engineer",
    summary: "Architected and led the migration of mission-critical microservices from legacy AWS ECS to Amazon EKS, establishing ArgoCD for declarative GitOps delivery, automated canary deployments, and dynamic horizontal pod autoscaling (HPA). Leveraged deep Kubernetes systems engineering (previously held Certified Kubernetes Administrator - CKA certification).",
    impact_metrics: [
      "Mission-critical microservices migrated with zero customer downtime",
      "Deployment lead time reduced from hours to under 10 minutes via GitOps (ArgoCD)",
      "Consolidated multi-account AWS and acquisition workloads into unified, secure architectures",
      "Helped teams move from deploying weekly to hourly"
    ],
    technologies: ["Kubernetes", "AWS EKS", "ArgoCD", "CKA (Previously Certified)", "Terraform", "Docker", "Helm", "Github Actions"]
  },
  {
    id: "exp-cicd-github-migration",
    category: "Platform Engineering",
    title: "Enterprise CI/CD Migration: Bitbucket & Jenkins to GitHub Actions",
    role: "Principal Infrastructure / DevOps Lead",
    summary: "Configured from scratch and engineered an enterprise CI/CD pipeline modernization across 100+ repositories, transitioning workloads from legacy Bitbucket and Jenkins setups to GitHub Actions. Designed reusable workflow templates, automated linting, security scans, and container build pipelines supporting thousands of concurrent Linux build runners.",
    impact_metrics: [
      "100+ repositories seamlessly migrated",
      "Build reliability increased to 99.8%",
      "Eliminated vendor fragmentation and boosted developer velocity across the organization"
    ],
    technologies: ["CI/CD", "CI/CD Pipelines", "GitHub Actions", "Bitbucket", "Jenkins", "Docker", "Bash", "Python", "Security Scanning (Trivy/Snyk)"]
  },
  {
    id: "exp-terraform-platform",
    category: "Platform Engineering",
    title: "Enterprise Terraform Module Platform & Multi-Cloud Automation",
    role: "Senior Platform Architect",
    summary: "Authored and maintained a suite of reusable, hardened Terraform modules managing infrastructure across AWS, Snowflake, Datadog, Confluent Cloud, Databricks, and GitHub at scale. Standardized multi-region deployments using automated state management and policy-as-code guardrails. And enabled self service infrastructure tracked in the same git repo as the teams applications.",
    impact_metrics: [
      "Unified infrastructure provisioning across 6 enterprise SaaS/Cloud platforms",
      "Automated compliance and drift detection for hundreds of cloud resources",
      "Enabled Self service infrastructure for development teams",
      "Forked and customized Terraform provider in Go (terraform-provider-neo4j) to manage graph database topologies"
    ],
    technologies: ["Terraform", "OpenTofu", "Go", "AWS", "Snowflake", "Confluent Cloud", "Databricks", "Datadog", "Platform Engineering", "Self Service"]
  },
  {
    id: "exp-kafka-confluent-migration",
    category: "Data Platforms & Streaming",
    title: "Streaming Platform Modernization: AWS MSK to Confluent Cloud",
    role: "Staff Data Infrastructure Engineer",
    summary: "Led the strategic migration from self-managed AWS Managed Streaming for Kafka (MSK) to Confluent Cloud, reducing operational maintenance, and streamlining Terraform automation for event-driven microservices. Consolidated Kafka environments to just PreProd and Prod to save costs.",
    impact_metrics: [
      "Eliminated broker patch downtime and storage rebalancing toil",
      "Cut cost of kafka spending by consolidating environments"
    ],
    technologies: ["Apache Kafka", "Confluent Cloud", "AWS MSK", "Schema Registry", "Aerospike", "Apache Cassandra", "Terraform", "FinOps"]
  },
  {
    id: "exp-security-compliance-audit",
    category: "Cloud Security & Compliance",
    title: "Enterprise Cloud Security, DevSecOps & Compliance Audit Governance",
    role: "Lead Platform & Infrastructure Security Engineer",
    summary: "Designed and enforced defense-in-depth security architectures across AWS and Kubernetes environments. Implemented least-privilege IAM policies, automated container vulnerability scanning (Trivy/Snyk) in CI/CD, deployed Falco for Kubernetes runtime threat detection and syscall monitoring, and provided technical evidence and controls to successfully satisfy SOC 2 Type 2, HIPAA, and ISO 27001 compliance audits.",
    impact_metrics: [
      "Supplied technical audit evidence and automated controls satisfying SOC 2 Type 2, HIPAA, and ISO 27001 compliance standards",
      "Deployed Falco runtime security across Kubernetes clusters to detect container anomalies, privilege escalations, and unexpected syscall behavior",
      "Eliminated static cloud credentials by enforcing Workload Identity Federation (WIF) and keyless OIDC across all CI/CD pipelines"
    ],
    technologies: ["Falco", "Runtime Security", "AWS IAM", "Workload Identity / OIDC", "SOC 2 Type 2", "HIPAA", "ISO 27001", "Security Scanning (Trivy/Snyk)", "AWS Config & Security Hub", "Kubernetes RBAC"]
  },
  {
    id: "exp-developer-tooling-paved-roads",
    category: "Platform Engineering & SRE",
    title: "Internal Developer Platform Tooling, Paved Roads & SRE Reliability",
    role: "Staff Platform & Reliability Engineer",
    summary: "Spearheaded internal developer platform initiatives by designing opinionated paved roads and self-service automation in Go and Python. Built developer CLIs, standard service templates, Docker Compose local development stacks.",
    impact_metrics: [
      "Reduced new service onboarding and developer provisioning time from days to under 2 hours via paved-road templates and CLIs",
      "Streamlined local developer workflows with containerized Docker Compose stacks replacing brittle shared preproduction environments"
    ],
    technologies: ["Go (Golang)", "Python", "Docker Compose", "Developer CLIs & SDKs", "SLOs / SLIs", "Datadog", "Prometheus & Grafana", "Incident Management & Blameless Postmortems"]
  },
  {
    id: "exp-security-appmesh-mtls",
    category: "Distributed Systems & Security",
    title: "Zero-Trust Service Mesh & mTLS with AWS App Mesh",
    role: "Senior Distributed Systems Engineer",
    summary: "Architected and deployed AWS App Mesh (Envoy-based proxy) to enforce mutual TLS (mTLS) service-to-service cryptographic authentication and fine-grained traffic policies across mission-critical Kubernetes microservices. Centralized secret rotation and enhanced zero-trust posture.",
    impact_metrics: [
      "100% encrypted in-transit mTLS traffic across internal service graph",
      "Centralized cryptographic identity without modifying application code",
      "Enhanced observability via Envoy distributed tracing headers"
    ],
    technologies: ["AWS App Mesh", "Envoy Proxy", "mTLS", "Kubernetes", "AWS Certificate Manager (ACM)"]
  },
  {
    id: "exp-finops-optimization",
    category: "Cloud FinOps & Infrastructure",
    title: "Cloud FinOps & Infrastructure Cost Rationalization",
    role: "Lead Platform Engineer",
    summary: "Initiated and executed comprehensive cloud cost-optimization across compute, storage, and networking tiers. Eliminated idle resources, rightsized Kubernetes requests/limits, rationalized third-party SaaS contracts, and tuned data retention policies.",
    impact_metrics: [
      "Saved over $10,000/month in cloud infrastructure costs within the first 60 days",
      "Implemented automated tagging, cost allocation budgets, and anomaly alerts"
    ],
    technologies: ["AWS Cost Explorer", "Kubernetes Karpenter / Cluster Autoscaler", "Terraform", "Datadog FinOps"]
  },
  {
    id: "exp-customer-service-tooling",
    category: "Platform Engineering & Internal Tooling",
    title: "Customer Support Automation & Streamlit Internal Tooling",
    role: "Senior Platform / DevOps Engineer",
    summary: "Engineered an internal Streamlit self-service web application used by customer service teams to diagnose and resolve common customer issues quickly. Enforced strict least-privilege access and role-based access control (RBAC), empowering support representatives to safely remediate issues through audited backend workflows without granting direct access to production databases or underlying systems.",
    impact_metrics: [
      "Accelerated customer issue resolution times by streamlining common troubleshooting workflows into an intuitive self-service portal",
      "Enforced least-privilege security posture by eliminating the need to grant customer service reps direct access to production systems",
      "Standardized automated resolution workflows for recurring customer support failure modes"
    ],
    technologies: ["Python", "Streamlit", "Internal Developer Tooling", "Least Privilege / RBAC", "REST APIs", "Docker"]
  }
];

export const ExperienceTimeline: React.FC = () => {
  return (
    <section id="experience" className="py-16 md:py-24 border-t border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 mb-3">
            <Briefcase className="w-3.5 h-3.5" />
            <span>Career Milestones</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Proven Production Impact at Scale
          </h2>
          <p className="mt-3 text-slate-400 text-sm sm:text-base">
            Quantified results leading distributed systems, cloud migrations, infrastructure automation, and cost rationalization.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {MILESTONES.map((m) => (
            <div
              key={m.id}
              className="p-6 rounded-2xl bg-slate-900/40 hover:bg-slate-900/70 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col justify-between group shadow-sm"
            >
              <div>
                <div className="mb-3">
                  <span className="inline-flex items-center text-xs font-mono text-cyan-400 font-medium px-2.5 py-1 rounded bg-cyan-950/60 border border-cyan-800/40">
                    {m.category}
                  </span>
                </div>

                <h3 className="text-lg font-bold text-white group-hover:text-cyan-300 transition-colors mb-1.5">
                  {m.title}
                </h3>

                <div className="text-xs text-slate-400 font-medium mb-3 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-cyan-400/80 shrink-0" />
                  <span>{m.role}</span>
                </div>

                <p className="text-xs sm:text-sm text-slate-300 leading-relaxed mb-4">
                  {m.summary}
                </p>

                {/* Metrics */}
                <div className="space-y-1.5 mb-4">
                  {m.impact_metrics.map((metric, i) => (
                    <div key={i} className="flex items-start gap-2 text-xs text-slate-300">
                      <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0 mt-0.5" />
                      <span>{metric}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Technologies */}
              <div className="pt-3 border-t border-slate-800/60 flex flex-wrap gap-1.5">
                {m.technologies.map((t) => (
                  <span
                    key={t}
                    className="px-2 py-0.5 text-[11px] font-mono text-slate-400 bg-slate-800/60 rounded border border-slate-700/40"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};
