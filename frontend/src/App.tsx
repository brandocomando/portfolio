import React, { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import { Navbar } from './components/Navbar';
import { Hero } from './components/Hero';
import { ArchitectureShowcase } from './components/ArchitectureShowcase';
import { ExperienceTimeline } from './components/ExperienceTimeline';
import { ProjectsGallery } from './components/ProjectsGallery';
import { SkillsMatrix } from './components/SkillsMatrix';
import { Footer } from './components/Footer';
import { AiChatDrawer } from './components/AiChatDrawer';
import { AuthModal } from './components/AuthModal';
import { ContactModal } from './components/ContactModal';
import { QuotaStatus } from './types';
import { fetchQuota } from './lib/api';
import { auth, logout } from './lib/firebase';
import { onAuthStateChanged } from 'firebase/auth';

export const App: React.FC = () => {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [isContactModalOpen, setIsContactModalOpen] = useState(false);
  const [contactInitialQuestion, setContactInitialQuestion] = useState<string | undefined>();
  const [initialPrompt, setInitialPrompt] = useState<string | undefined>();
  const [quota, setQuota] = useState<QuotaStatus | null>(null);
  const [authToken, setAuthToken] = useState<string | null>(() => localStorage.getItem('portfolio_auth_token'));

  const refreshQuota = async (token?: string | null) => {
    const q = await fetchQuota(token !== undefined ? token : authToken);
    setQuota(q);
  };

  useEffect(() => {
    refreshQuota(authToken);

    // Listen to Firebase Auth state
    const unsubscribe = onAuthStateChanged(auth, async (user) => {
      if (user) {
        try {
          const token = await user.getIdToken();
          setAuthToken(token);
          localStorage.setItem('portfolio_auth_token', token);
          refreshQuota(token);
        } catch (e) {
          console.error("Token retrieval failed:", e);
        }
      }
    });

    return () => unsubscribe();
  }, []);

  useEffect(() => {
    const checkHash = () => {
      if (window.location.hash === '#contact') {
        setIsContactModalOpen(true);
      }
    };
    window.addEventListener('hashchange', checkHash);
    checkHash();
    return () => window.removeEventListener('hashchange', checkHash);
  }, []);

  const handleOpenChat = (prompt?: string) => {
    setInitialPrompt(prompt);
    setIsChatOpen(true);
  };

  const handleOpenContact = (question?: string) => {
    setContactInitialQuestion(question);
    setIsContactModalOpen(true);
  };

  const handleAuthSuccess = (token: string, _user: any) => {
    setAuthToken(token);
    localStorage.setItem('portfolio_auth_token', token);
    refreshQuota(token);
  };

  const handleLogout = async () => {
    await logout();
    setAuthToken(null);
    localStorage.removeItem('portfolio_auth_token');
    refreshQuota(null);
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-['Plus_Jakarta_Sans',sans-serif]">
      {/* Top Navbar */}
      <Navbar
        quota={quota}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        onLogout={handleLogout}
        onOpenChat={() => handleOpenChat()}
        onOpenContact={() => handleOpenContact()}
      />

      {/* Main Sections */}
      <main className="flex-1">
        <Hero onOpenChat={handleOpenChat} />
        <ArchitectureShowcase />
        <ExperienceTimeline />
        <ProjectsGallery />
        <SkillsMatrix />
      </main>

      {/* Footer */}
      <Footer onOpenContact={() => handleOpenContact()} />

      {/* Floating Action Button (AI Assistant) */}
      {!isChatOpen && (
        <button
          onClick={() => handleOpenChat()}
          className="fixed bottom-6 right-6 z-40 flex items-center gap-2.5 px-4 py-3 rounded-full bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-semibold text-xs sm:text-sm shadow-xl shadow-cyan-500/25 transition-all transform hover:scale-105 cursor-pointer"
        >
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-200 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-white"></span>
          </span>
          <Sparkles className="w-4 h-4 text-cyan-200" />
          <span>Ask Brandon's AI Agent</span>
          {quota && (
            <span className="ml-1 text-[11px] font-mono px-2 py-0.5 rounded-full bg-black/30 border border-white/20">
              {quota.remaining}/{quota.limit}
            </span>
          )}
        </button>
      )}

      {/* AI Assistant Chat Drawer */}
      <AiChatDrawer
        isOpen={isChatOpen}
        onClose={() => {
          setIsChatOpen(false);
          setInitialPrompt(undefined);
        }}
        quota={quota}
        onRefreshQuota={() => refreshQuota(authToken)}
        onOpenAuth={() => setIsAuthModalOpen(true)}
        initialPrompt={initialPrompt}
        authToken={authToken}
        onOpenContact={handleOpenContact}
      />

      {/* Recruiter / Visitor Auth Modal */}
      <AuthModal
        isOpen={isAuthModalOpen}
        onClose={() => setIsAuthModalOpen(false)}
        onAuthSuccess={handleAuthSuccess}
      />

      {/* Direct Contact Modal */}
      <ContactModal
        isOpen={isContactModalOpen}
        onClose={() => {
          setIsContactModalOpen(false);
          setContactInitialQuestion(undefined);
          if (window.location.hash === '#contact') {
            history.replaceState(null, '', window.location.pathname + window.location.search);
          }
        }}
        initialQuestion={contactInitialQuestion}
      />
    </div>
  );
};

