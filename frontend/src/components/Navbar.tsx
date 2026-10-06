import React from 'react';
import { Terminal, LogOut, Github, ShieldCheck } from 'lucide-react';
import { QuotaStatus } from '../types';

interface NavbarProps {
  quota: QuotaStatus | null;
  onLogout: () => void;
  onOpenContact?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ quota, onLogout, onOpenContact }) => {
  return (
    <header className="sticky top-0 z-40 w-full backdrop-blur-md bg-[#090d16]/80 border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-cyan-500/20">
            <Terminal className="w-5 h-5 text-white" />
          </div>
          <div>
            <a href="#" className="font-bold text-base sm:text-lg tracking-tight hover:text-cyan-400 transition-colors">
              Brandon Foster
            </a>
            <span className="hidden sm:inline-block ml-2 text-xs font-mono text-cyan-400/90 bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-800/50">
              Staff / Senior Platform & MLOps
            </span>
          </div>
        </div>

        {/* Navigation Links & Optional Auth Status */}
        <div className="flex items-center gap-6">
          <nav className="hidden md:flex items-center gap-6 text-sm text-slate-300 font-medium">
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
              href="https://github.com/brandocomando/portfolio"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1.5 hover:text-cyan-400 transition-colors"
            >
              <Github className="w-4 h-4" />
              <span>Source Code</span>
            </a>
          </nav>

          {quota?.authenticated && (
            <div className="flex items-center gap-2">
              <span className="hidden sm:inline-flex items-center gap-1 text-xs text-emerald-400 font-mono bg-emerald-950/50 border border-emerald-800/40 px-2.5 py-1 rounded-full">
                <ShieldCheck className="w-3 h-3" />
                {quota.user_name?.split(' ')[0] || 'Unlocked'}
              </span>
              <button
                onClick={onLogout}
                title="Sign Out"
                className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-800/60 rounded-md transition-colors cursor-pointer"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
