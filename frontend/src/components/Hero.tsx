import React from 'react';
import { Sparkles } from 'lucide-react';

interface HeroProps {
  onOpenChat: (initialPrompt?: string) => void;
}

export const Hero: React.FC<HeroProps> = ({ onOpenChat }) => {
  return (
    <section className="relative pt-12 pb-20 md:pt-20 md:pb-28 overflow-hidden">
      {/* Background Glow Orbs */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[350px] bg-gradient-to-tr from-cyan-600/15 via-indigo-600/15 to-purple-600/10 blur-[130px] rounded-full pointer-events-none -z-10" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-3xl mx-auto">
          {/* Headline */}
          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-[1.15]">
            Engineering Resilient <br className="hidden sm:inline" />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 via-sky-300 to-indigo-400">
              Distributed Systems & MLOps
            </span>
          </h1>

          {/* Subtitle */}
          <p className="mt-6 text-base sm:text-lg text-slate-300 leading-relaxed font-normal">
            Hi, I'm <strong className="text-white font-semibold">Brandon Foster</strong>. I build high-throughput Kubernetes platforms,
            hardened Terraform modules, enterprise streaming architectures, and sovereign AI agent workflows.
          </p>

          {/* Interactive CTA Buttons */}
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <button
              onClick={() => onOpenChat("Tell me about Brandon's engineering background and top achievements.")}
              className="flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold text-sm shadow-lg shadow-cyan-500/25 transition-all transform hover:-translate-y-0.5"
            >
              <Sparkles className="w-4 h-4 text-cyan-200" />
              <span>Ask My AI Agent</span>
            </button>
          </div>

          {/* Suggested Prompts Pill Tray */}
          <div className="mt-6 flex flex-wrap items-center justify-center gap-2 text-xs">
            <span className="text-slate-400 font-mono">Try asking:</span>
            <button
              onClick={() => onOpenChat("How did Brandon migrate mission-critical microservices from ECS to EKS?")}
              className="px-2.5 py-1 rounded-md bg-slate-800/50 hover:bg-slate-800 text-slate-300 border border-slate-700/60 transition-colors"
            >
              "ECS to EKS Migration"
            </button>
            <button
              onClick={() => onOpenChat("Tell me about Brandon's forked and customized Neo4j Terraform provider in Go.")}
              className="px-2.5 py-1 rounded-md bg-slate-800/50 hover:bg-slate-800 text-slate-300 border border-slate-700/60 transition-colors"
            >
              "Go Terraform Provider"
            </button>
            <button
              onClick={() => onOpenChat("How did Brandon save $10K+/month in cloud FinOps?")}
              className="px-2.5 py-1 rounded-md bg-slate-800/50 hover:bg-slate-800 text-slate-300 border border-slate-700/60 transition-colors"
            >
              "$10K/mo FinOps Savings"
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};
