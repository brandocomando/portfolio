import React from 'react';
import { FolderGit2, ArrowUpRight } from 'lucide-react';
import { Project } from '../types';

const PROJECTS: Project[] = [
  {
    id: "proj-my-agentic-team",
    name: "My Agentic Team",
    repo: "brandocomando/my_agentic_team",
    url: "https://github.com/brandocomando/my_agentic_team",
    category: "AI Infra & Autonomous Agents",
    tagline: "A production-minded, local-first compilation of autonomous AI agents automating real-world daily workflows.",
    summary: "Multi-agent system featuring local LLMs via Ollama and Chrome DevTools Protocol (CDP) web automation. Includes Campsite Finder, Gmail Inbox Triage (sub-50ms priority labeling), Personal Finance categorization, and Laya fast-inference integration.",
    highlights: [
      "Local-first LLMs eliminating external API latency and privacy risks",
      "Headless browser automation via Chrome DevTools Protocol (CDP)",
      "System-1 fast inference via Laya for rapid decision scoring"
    ],
    technologies: ["Python", "Ollama", "Local LLMs", "CDP", "Docker", "OAuth2", "Laya"]
  },
  {
    id: "proj-prometheus-ingress-exporter",
    name: "Prometheus Ingress Status Exporter",
    repo: "brandocomando/prometheus-ingress-status-exporter",
    url: "https://github.com/brandocomando/prometheus-ingress-status-exporter",
    category: "Distributed Systems & Kubernetes",
    tagline: "Kubernetes controller & exporter that discovers Ingress endpoints dynamically and exports response metrics to Prometheus.",
    summary: "High-performance Go daemon that connects to the Kubernetes API, watches Ingress resources dynamically, performs synthetic HTTP/HTTPS health checks, and exports Prometheus-compatible availability metrics.",
    highlights: [
      "Written in Go using official Kubernetes client-go and Prometheus client libraries",
      "Asynchronous worker pool preventing target probing denial-of-service",
      "Provides instant cluster-wide edge health observability"
    ],
    technologies: ["Go (Golang)", "Kubernetes (client-go)", "Prometheus", "Docker", "SRE"]
  },
  {
    id: "proj-terraform-provider-neo4j",
    name: "Terraform Provider for Neo4j",
    repo: "brandocomando/terraform-provider-neo4j",
    url: "https://github.com/brandocomando/terraform-provider-neo4j",
    category: "Platform Engineering & IaC",
    tagline: "Forked and customized Terraform provider written in Go for managing Neo4j graph database topologies and role-based access.",
    summary: "Forked and customized a native Terraform provider plugin in Go to declare and manage Neo4j graph database resources, user permissions, database instances, and cluster configurations declaratively within Terraform GitOps workflows.",
    highlights: [
      "Implemented official Terraform Plugin SDK specifications",
      "State management with full CRUD lifecycle operations and schema validation",
      "Bridges graph database provisioning into standard IaC pipelines"
    ],
    technologies: ["Go", "Terraform Plugin SDK", "Neo4j", "Graph Databases", "GitOps"]
  },
  {
    id: "proj-portfolio-platform",
    name: "FinOps Portfolio & AI MLOps Platform",
    repo: "brandocomando/portfolio",
    url: "https://github.com/brandocomando/portfolio",
    category: "Cloud Platform & MLOps",
    tagline: "Scale-to-zero GCP portfolio featuring hybrid RAG, Medallion data pipeline, CI/CD, and Terraform.",
    summary: "This exact platform: React SPA on Firebase Hosting (CDN), FastAPI backend on Cloud Run scaling to zero, and in-memory Hybrid RAG engine (Dense + BM25 + RRF) answering queries via Gemini Flash. Features Workload Identity Federation (WIF) and MLOps CI evaluation gate.",
    highlights: [
      "FinOps compliance: $0/month idle cost via Cloud Run and Firebase Hosting",
      "Workload Identity Federation (OIDC) eliminating static keys in CI/CD",
      "Continuous evaluation CI gate testing context recall and answer faithfulness"
    ],
    technologies: ["Terraform", "Google Cloud Run", "Firebase Hosting", "FastAPI", "React", "Gemini Flash"]
  }
];

export const ProjectsGallery: React.FC = () => {
  return (
    <section id="projects" className="py-16 md:py-24 border-t border-slate-800/80 bg-slate-900/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto mb-16">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono bg-cyan-950/60 border border-cyan-800/60 text-cyan-300 mb-3">
            <FolderGit2 className="w-3.5 h-3.5" />
            <span>Featured Open Source & Systems</span>
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
            Engineering Projects & Open Source
          </h2>
          <p className="mt-3 text-slate-400 text-sm sm:text-base">
            Autonomous agent fleets, custom Kubernetes controllers, Go Terraform providers, and scale-to-zero cloud platforms.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {PROJECTS.map((p) => (
            <div
              key={p.id}
              className="p-6 sm:p-7 rounded-2xl bg-slate-900/60 hover:bg-slate-900 border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between group shadow-sm"
            >
              <div>
                <div className="flex items-center justify-between gap-3 mb-3">
                  <span className="inline-flex items-center text-xs font-mono text-indigo-300 font-medium px-2.5 py-1 rounded bg-indigo-950/60 border border-indigo-800/50">
                    {p.category}
                  </span>
                  <a
                    href={p.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-slate-400 hover:text-cyan-400 transition-colors p-1"
                    title="View GitHub Repository"
                  >
                    <ArrowUpRight className="w-4 h-4" />
                  </a>
                </div>

                <h3 className="text-lg font-bold text-white group-hover:text-cyan-300 transition-colors mb-1">
                  {p.name}
                </h3>

                <p className="text-xs text-cyan-400/90 font-mono mb-3">
                  {p.tagline}
                </p>

                <p className="text-xs text-slate-300 leading-relaxed mb-4">
                  {p.summary}
                </p>

                {/* Highlights */}
                <div className="space-y-1 mb-4 text-xs text-slate-400">
                  {p.highlights.map((h, i) => (
                    <div key={i} className="flex items-start gap-1.5">
                      <span className="text-cyan-400 font-bold">•</span>
                      <span>{h}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Technologies */}
              <div className="pt-3 border-t border-slate-800/60 flex flex-wrap gap-1.5">
                {p.technologies.map((t) => (
                  <span
                    key={t}
                    className="px-2 py-0.5 text-[10px] font-mono text-slate-400 bg-slate-800/60 rounded border border-slate-700/40"
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
