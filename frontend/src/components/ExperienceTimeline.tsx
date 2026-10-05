import React from 'react';
import { Briefcase, Check } from 'lucide-react';
import { Milestone } from '../types';

const MILESTONES: Milestone[] = [
  {
    id: "exp-eks-migration",
    category: "Distributed Systems & Kubernetes",
    title: "Large-Scale Microservices Migration to EKS & GitOps",
    role: "Lead Platform Engineer",
    summary: "Architected and led the migration of 30+ mission-critical microservices from legacy AWS ECS to Amazon EKS, establishing ArgoCD for declarative GitOps delivery, automated canary deployments, and dynamic horizontal pod autoscaling.",
    impact_metrics: [
      "30+ microservices migrated with zero customer downtime",
      "Deployment lead time reduced from hours to under 10 minutes via GitOps (ArgoCD)",
      "Consolidated multi-account AWS and acquisition workloads into unified architectures"
    ],
    technologies: ["Kubernetes", "AWS EKS", "ArgoCD", "Terraform", "Docker", "Helm"]
  },
  {
    id: "exp-finops-optimization",
    category: "Cloud FinOps & Infrastructure",
    title: "Enterprise Cloud FinOps & Cost Rationalization",
    role: "Lead Platform Engineer",
    summary: "Initiated and executed comprehensive cloud cost-optimization across compute, storage, and networking tiers. Eliminated idle resources, rightsized Kubernetes workloads, and rationalized vendor SaaS agreements.",
    impact_metrics: [
      "Saved over $10,000/month in cloud infrastructure costs within the first 60 days",
      "Implemented automated cost allocation tagging and anomaly alerts in Datadog and AWS Cost Explorer"
    ],
    technologies: ["AWS Cost Explorer", "Kubernetes Karpenter", "Terraform", "Datadog FinOps"]
  },
  {
    id: "exp-cicd-github-migration",
    category: "Platform Engineering",
    title: "Enterprise CI/CD Migration: Bitbucket to GitHub Actions",
    role: "Principal Infrastructure Lead",
    summary: "Engineered and executed an enterprise migration of 100+ repositories from Bitbucket to GitHub and GitHub Actions. Designed reusable workflow templates, automated linting, security scans, and scalable container build runners.",
    impact_metrics: [
      "100+ repositories seamlessly migrated with unified CI/CD standards",
      "Build reliability increased to 99.8% across engineering teams"
    ],
    technologies: ["GitHub Actions", "Bitbucket", "Docker", "Bash", "Python", "Trivy"]
  },
  {
    id: "exp-terraform-platform",
    category: "Platform Engineering",
    title: "Enterprise Terraform Module Platform & Multi-Cloud Automation",
    role: "Senior Platform Architect",
    summary: "Authored and maintained a suite of reusable, hardened Terraform modules managing infrastructure across AWS, Snowflake, Datadog, Confluent Cloud, Databricks, and GitHub at scale. Standardized multi-region deployments.",
    impact_metrics: [
      "Unified infrastructure provisioning across 6 enterprise SaaS/Cloud platforms",
      "Developed custom Terraform provider in Go (terraform-provider-neo4j) to manage graph databases"
    ],
    technologies: ["Terraform", "Go (Golang)", "AWS", "Snowflake", "Confluent Cloud", "Databricks"]
  },
  {
    id: "exp-security-appmesh-mtls",
    category: "Distributed Systems & Security",
    title: "Zero-Trust Service Mesh & mTLS with AWS App Mesh",
    role: "Senior Distributed Systems Engineer",
    summary: "Architected and deployed AWS App Mesh (Envoy-based proxy) to enforce mutual TLS (mTLS) service-to-service cryptographic authentication and fine-grained traffic policies across 30+ Kubernetes microservices.",
    impact_metrics: [
      "100% encrypted in-transit mTLS traffic across internal microservice mesh",
      "Centralized cryptographic identity without modifying application code"
    ],
    technologies: ["AWS App Mesh", "Envoy Proxy", "mTLS", "Kubernetes", "ACM"]
  },
  {
    id: "exp-kafka-confluent-migration",
    category: "Data Platforms & Streaming",
    title: "Streaming Platform Modernization: AWS MSK to Confluent Cloud",
    role: "Staff Data Infrastructure Engineer",
    summary: "Led the strategic migration from self-managed AWS MSK to Confluent Cloud, reducing broker maintenance toil, improving schema registry governance, and streamlining Terraform automation.",
    impact_metrics: [
      "Eliminated broker patch downtime and storage rebalancing toil",
      "Enforced Avro/Protobuf schema evolution governance across producers and consumers"
    ],
    technologies: ["Apache Kafka", "Confluent Cloud", "AWS MSK", "Schema Registry", "Terraform"]
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

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {MILESTONES.map((m) => (
            <div
              key={m.id}
              className="p-6 rounded-2xl bg-slate-900/40 hover:bg-slate-900/70 border border-slate-800/80 hover:border-slate-700 transition-all flex flex-col justify-between group shadow-sm"
            >
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs font-mono text-cyan-400 font-medium px-2 py-0.5 rounded bg-cyan-950/60 border border-cyan-800/40">
                    {m.category}
                  </span>
                  <span className="text-xs text-slate-400 font-medium">
                    {m.role}
                  </span>
                </div>

                <h3 className="text-lg font-bold text-white group-hover:text-cyan-300 transition-colors mb-2">
                  {m.title}
                </h3>

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
