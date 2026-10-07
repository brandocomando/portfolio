import React from 'react';
import { X, Shield, FileText, CheckCircle2 } from 'lucide-react';

export type LegalDocType = 'privacy' | 'terms';

interface LegalModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialDoc?: LegalDocType;
}

export const LegalModal: React.FC<LegalModalProps> = ({
  isOpen,
  onClose,
  initialDoc = 'privacy'
}) => {
  const [activeDoc, setActiveDoc] = React.useState<LegalDocType>(initialDoc);

  React.useEffect(() => {
    setActiveDoc(initialDoc);
  }, [initialDoc]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="relative w-full max-w-2xl max-h-[85vh] flex flex-col bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-slate-800 bg-slate-950/60">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center text-white shadow-md shadow-cyan-500/20">
              {activeDoc === 'privacy' ? (
                <Shield className="w-5 h-5 text-white" />
              ) : (
                <FileText className="w-5 h-5 text-white" />
              )}
            </div>
            <div>
              <h3 className="text-base font-bold text-white tracking-tight">
                {activeDoc === 'privacy' ? 'Privacy Policy' : 'Terms of Service'}
              </h3>
              <p className="text-[11px] text-slate-400 font-mono">
                Brandon Foster Portfolio • Last updated: October 2026
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab navigation */}
        <div className="flex border-b border-slate-800 bg-slate-900/80 px-5 text-xs font-medium">
          <button
            onClick={() => setActiveDoc('privacy')}
            className={`py-3 px-4 border-b-2 transition-all flex items-center gap-2 cursor-pointer ${
              activeDoc === 'privacy'
                ? 'border-cyan-400 text-cyan-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <Shield className="w-3.5 h-3.5" />
            <span>Privacy Policy</span>
          </button>
          <button
            onClick={() => setActiveDoc('terms')}
            className={`py-3 px-4 border-b-2 transition-all flex items-center gap-2 cursor-pointer ${
              activeDoc === 'terms'
                ? 'border-cyan-400 text-cyan-300'
                : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <FileText className="w-3.5 h-3.5" />
            <span>Terms of Service</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-5 text-xs text-slate-300 leading-relaxed font-sans">
          {activeDoc === 'privacy' ? (
            <>
              <section className="space-y-2">
                <h4 className="text-sm font-semibold text-white">1. Introduction & Overview</h4>
                <p>
                  This Privacy Policy explains how Brandon Foster (&quot;we&quot;, &quot;us&quot;, or &quot;our&quot;) collects, uses, and safeguards information when you visit this personal engineering portfolio and interact with Brandon&apos;s AI Agent at <strong>brandonfoster.dev</strong> or related domains.
                </p>
                <p>
                  We believe in minimal data collection, transparency, and FinOps-driven security. We do not sell, rent, or monetize your personal data.
                </p>
              </section>

              <section className="space-y-2">
                <h4 className="text-sm font-semibold text-white">2. Information We Collect</h4>
                <ul className="list-disc pl-5 space-y-1.5 text-slate-400">
                  <li>
                    <strong className="text-slate-200">Authentication Data:</strong> When you choose to sign in via Google or GitHub, Firebase Authentication provides your name, email address, and OAuth user ID. This is solely used to unlock your daily AI question quota and recognize you upon return.
                  </li>
                  <li>
                    <strong className="text-slate-200">AI Agent Interactions:</strong> Questions submitted to the portfolio AI Agent are processed in real-time to generate contextual technical answers regarding Brandon&apos;s background and projects.
                  </li>
                  <li>
                    <strong className="text-slate-200">Direct Contact Messages:</strong> If you submit an inquiry through the contact modal, your name, email, and message are recorded to allow Brandon to reply directly to you.
                  </li>
                  <li>
                    <strong className="text-slate-200">Technical Logs & Rate Limiting:</strong> Anonymized client IP addresses and session hashes are processed solely in memory for sliding-window token bucket rate limiting (protecting LLM API quotas against abuse).
                  </li>
                </ul>
              </section>

              <section className="space-y-2">
                <h4 className="text-sm font-semibold text-white">3. Third-Party Service Providers</h4>
                <p>We leverage industry-standard cloud infrastructure to host and operate this site:</p>
                <ul className="list-disc pl-5 space-y-1 text-slate-400">
                  <li><strong>Google Cloud Platform & Firebase:</strong> Authentication, hosting, and Firestore database.</li>
                  <li><strong>Google Gemini API:</strong> Large language model inference for the portfolio AI Agent.</li>
                </ul>
              </section>

              <section className="space-y-2">
                <h4 className="text-sm font-semibold text-white">4. Data Retention & Deletion</h4>
                <p>
                  You may request the deletion of your contact records or authenticated account data at any time by emailing Brandon directly at <a href="mailto:brandocomando8@gmail.com" className="text-cyan-400 hover:underline">brandocomando8@gmail.com</a>.
                </p>
              </section>

              <section className="space-y-2">
                <h4 className="text-sm font-semibold text-white">5. Contact Information</h4>
                <p>
                  For any privacy inquiries or data requests, please contact:
                  <br />
                  <strong className="text-slate-200">Brandon Foster</strong>
                  <br />
                  Email: <a href="mailto:brandocomando8@gmail.com" className="text-cyan-400 hover:underline">brandocomando8@gmail.com</a>
                  <br />
                  Location: Phoenix, Arizona (Mountain Standard Time)
                </p>
              </section>
            </>
          ) : (
            <>
              <section className="space-y-2">
                <h4 className="text-sm font-semibold text-white">1. Acceptance of Terms</h4>
                <p>
                  By accessing and using this portfolio website and interacting with Brandon&apos;s AI Agent, you agree to comply with and be bound by these Terms of Service. If you do not agree, please do not use the application.
                </p>
              </section>

              <section className="space-y-2">
                <h4 className="text-sm font-semibold text-white">2. Purpose of the Application</h4>
                <p>
                  This application is a personal professional portfolio and technological demonstration showcasing platform engineering, Kubernetes, Terraform, Kafka, and MLOps architecture. The integrated AI Agent provides interactive answers regarding Brandon Foster&apos;s career milestones, open-source repositories, and technical skills.
                </p>
              </section>

              <section className="space-y-2">
                <h4 className="text-sm font-semibold text-white">3. Acceptable Use Policy</h4>
                <p>Users agree to use this site responsibly:</p>
                <ul className="list-disc pl-5 space-y-1.5 text-slate-400">
                  <li>Do not engage in automated scraping, denial-of-service attempts, or bypass rate-limiting controls.</li>
                  <li>Do not submit malicious prompts, prompt injections, or abusive/illegal content to the AI Agent.</li>
                  <li>Authentication via Google or GitHub is intended for legitimate technical recruiters, engineering managers, and peers.</li>
                </ul>
              </section>

              <section className="space-y-2">
                <h4 className="text-sm font-semibold text-white">4. AI Agent Disclaimer</h4>
                <p>
                  Brandon&apos;s AI Agent utilizes Google Gemini and a hybrid RAG knowledge engine. While grounded in verified project indexes, generative AI can produce inaccurate outputs or hallucinations. Information provided by the AI Agent is for informational showcase purposes only and should be confirmed directly with Brandon for formal recruitment or technical verification.
                </p>
              </section>

              <section className="space-y-2">
                <h4 className="text-sm font-semibold text-white">5. Intellectual Property</h4>
                <p>
                  All project summaries, architecture blueprints, diagrams, and custom code on this site are the intellectual property of Brandon Foster, unless otherwise noted as licensed open-source software.
                </p>
              </section>

              <section className="space-y-2">
                <h4 className="text-sm font-semibold text-white">6. Governing Law & Contact</h4>
                <p>
                  These terms are governed by the laws of the State of Arizona, United States.
                  <br />
                  Inquiries: <a href="mailto:brandocomando8@gmail.com" className="text-cyan-400 hover:underline">brandocomando8@gmail.com</a>
                </p>
              </section>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/80 flex items-center justify-between text-xs">
          <div className="flex items-center gap-1.5 text-slate-500">
            <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
            <span>Compliant with Google OAuth & Developer Policies</span>
          </div>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-white font-medium transition-colors cursor-pointer"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
