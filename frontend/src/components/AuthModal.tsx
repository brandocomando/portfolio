import React, { useState } from 'react';
import { X, ShieldCheck, Github, Sparkles, AlertCircle, Loader2 } from 'lucide-react';
import { loginWithGoogle, loginWithGithub, loginAsDevDemo } from '../lib/firebase';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAuthSuccess: (token: string, user: any) => void;
  authLimit?: number;
  onOpenLegal?: (doc: 'privacy' | 'terms') => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onAuthSuccess, authLimit, onOpenLegal }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const targetLimit = authLimit || Number(import.meta.env.VITE_AUTH_DAILY_LIMIT) || 10;

  const handleGoogleLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const { token, user } = await loginWithGoogle();
      onAuthSuccess(token, user);
      onClose();
    } catch (err: any) {
      if (err?.message?.includes('Popup was closed before completion')) {
        // User closed the popup, silently reset
        return;
      }
      setError(err?.message || "Google authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const handleGithubLogin = async () => {
    setLoading(true);
    setError(null);
    try {
      const { token, user } = await loginWithGithub();
      onAuthSuccess(token, user);
      onClose();
    } catch (err: any) {
      if (err?.message?.includes('Popup was closed before completion')) {
        return;
      }
      setError(err?.message || "GitHub authentication failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDevLogin = () => {
    const { token, user } = loginAsDevDemo('recruiter');
    onAuthSuccess(token, user);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-md p-6 bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 p-1 text-slate-400 hover:text-white rounded-md"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="text-center mb-6">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center mx-auto mb-3 shadow-lg shadow-cyan-500/25">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h3 className="text-xl font-bold text-white tracking-tight">
            Unlock {targetLimit} Daily AI Questions
          </h3>
          <p className="mt-2 text-xs text-slate-400 leading-relaxed">
            Are you a technical recruiter, hiring manager, or fellow engineer? Sign in with 1 click to unlock {targetLimit} daily questions with Brandon's AI Agent and let Brandon know you checked out his portfolio.
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-300 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span className="leading-snug">{error}</span>
          </div>
        )}

        <div className="space-y-3">
          <button
            onClick={handleGoogleLogin}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 px-4 py-2.5 rounded-xl bg-white hover:bg-slate-100 text-slate-900 font-semibold text-xs sm:text-sm transition-all shadow-md disabled:opacity-60 cursor-pointer"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin text-slate-700" />
            ) : (
              <svg className="w-4 h-4" viewBox="0 0 24 24">
                <path
                  fill="#EA4335"
                  d="M12 5c1.6 0 3 .6 4.1 1.7l3.1-3.1C17.3 1.8 14.8 1 12 1 7.4 1 3.5 3.6 1.6 7.4l3.7 2.9C6.2 7.5 8.9 5 12 5z"
                />
                <path
                  fill="#4285F4"
                  d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.6h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.9z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.3 14.7c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3L1.6 7.2C.6 9.2 0 10.6 0 12.4s.6 3.2 1.6 5.2l3.7-2.9z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3.1 0-5.8-2.5-6.7-5.3L1.6 16C3.5 19.8 7.4 23 12 23z"
                />
              </svg>
            )}
            <span>{loading ? "Authenticating..." : "Continue with Google"}</span>
          </button>

          <button
            onClick={handleGithubLogin}
            disabled={loading}
            className="w-full flex items-center justify-center gap-3 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-semibold text-xs sm:text-sm border border-slate-700 transition-all shadow-md disabled:opacity-60 cursor-pointer"
          >
            <Github className="w-4 h-4" />
            <span>Continue with GitHub</span>
          </button>

          {(import.meta.env.DEV || import.meta.env.VITE_ENABLE_DEV_LOGIN === 'true') && (
            <button
              onClick={handleDevLogin}
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-semibold transition-all cursor-pointer mt-2"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-400" />
              <span>Dev Mode: Quick Demo Login (Skip OAuth)</span>
            </button>
          )}
        </div>

        <div className="mt-3.5 text-center text-[10px] text-slate-500">
          <span>By signing in, you agree to our </span>
          <button
            type="button"
            onClick={() => onOpenLegal?.('terms')}
            className="text-cyan-400 hover:underline cursor-pointer"
          >
            Terms
          </button>
          <span> and </span>
          <button
            type="button"
            onClick={() => onOpenLegal?.('privacy')}
            className="text-cyan-400 hover:underline cursor-pointer"
          >
            Privacy Policy
          </button>
          <span>.</span>
        </div>

        <div className="mt-4 pt-3.5 border-t border-slate-800 text-center">
          <div className="flex items-center justify-center gap-1.5 text-[11px] text-slate-500 font-mono">
            <ShieldCheck className="w-3.5 h-3.5 text-cyan-400" />
            <span>Authenticated via Firebase Auth (Google Cloud)</span>
          </div>
        </div>
      </div>
    </div>
  );
};
