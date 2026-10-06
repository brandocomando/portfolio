import React from 'react';
import { Terminal, Github } from 'lucide-react';

interface FooterProps {
  onOpenContact?: () => void;
}

export const Footer: React.FC<FooterProps> = ({ onOpenContact }) => {
  return (
    <footer className="border-t border-slate-800 bg-[#070a12] py-12 text-xs text-slate-400">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white font-bold">
              <Terminal className="w-4 h-4" />
            </div>
            <div>
              <div className="font-bold text-white text-sm">Brandon Foster</div>
              <p className="text-slate-500 text-[11px]">Senior Platform & MLOps Engineer</p>
            </div>
          </div>

          <div className="flex flex-wrap items-center justify-center gap-6 text-slate-400">
            <a href="#architecture" className="hover:text-cyan-400 transition-colors">Architecture</a>
            <a href="#experience" className="hover:text-cyan-400 transition-colors">Experience</a>
            <a href="#projects" className="hover:text-cyan-400 transition-colors">Projects</a>
            <a href="#skills" className="hover:text-cyan-400 transition-colors">Skills</a>
            <button
              onClick={onOpenContact}
              className="hover:text-cyan-400 transition-colors cursor-pointer"
            >
              Contact
            </button>
            <a
              href="https://github.com/brandocomando"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 hover:text-cyan-400 transition-colors"
            >
              <Github className="w-3.5 h-3.5" />
              <span>GitHub</span>
            </a>
          </div>

          <div className="text-center md:text-right font-mono text-[11px] text-slate-500">
            <p className="flex items-center justify-center md:justify-end gap-1">
              <span>Terraform</span> • <span>Cloud Run</span> • <span>Firebase</span> • <span>Gemini</span>
            </p>
            <p className="text-slate-600 mt-1">© {new Date().getFullYear()} Brandon Foster. Scale-to-Zero GCP.</p>
          </div>
        </div>
      </div>
    </footer>
  );
};
