import React, { useState, useRef, useEffect } from 'react';
import { Sparkles, X, Send, Bot, User as UserIcon, Mail } from 'lucide-react';
import { ChatMessage, QuotaStatus } from '../types';
import { streamChat } from '../lib/api';

interface AiChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  quota: QuotaStatus | null;
  onRefreshQuota: () => void;
  onOpenAuth: () => void;
  initialPrompt?: string;
  authToken?: string | null;
  onOpenContact?: (initialQuestion?: string) => void;
}

export const AiChatDrawer: React.FC<AiChatDrawerProps> = ({
  isOpen,
  onClose,
  quota,
  onRefreshQuota,
  onOpenAuth,
  initialPrompt,
  authToken,
  onOpenContact
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I am Brandon Foster's AI Agent. I'm connected to a live Hybrid RAG retrieval engine indexing Brandon's platform engineering, Kubernetes, Terraform, Kafka, and MLOps experience. What would you like to know?",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [rateLimitExceeded, setRateLimitExceeded] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
    }
    if (initialPrompt && isOpen) {
      handleSendPrompt(initialPrompt);
    }
  }, [isOpen, initialPrompt]);

  const getLastUserQuestion = (assistantMsgId: string): string | undefined => {
    const idx = messages.findIndex((msg) => msg.id === assistantMsgId);
    if (idx >= 0) {
      for (let i = idx - 1; i >= 0; i--) {
        if (messages[i].role === 'user') {
          return messages[i].content;
        }
      }
    }
    const userMsgs = messages.filter((m) => m.role === 'user');
    return userMsgs.length > 0 ? userMsgs[userMsgs.length - 1].content : undefined;
  };

  const renderBoldSegments = (text: string, keyPrefix: string) => {
    const parts: React.ReactNode[] = [];
    let lastIdx = 0;
    const boldRegex = /\*\*([^*]+)\*\*/g;
    let match;

    while ((match = boldRegex.exec(text)) !== null) {
      if (match.index > lastIdx) {
        parts.push(text.substring(lastIdx, match.index));
      }
      parts.push(
        <strong key={`${keyPrefix}-b-${match.index}`} className="font-semibold text-white">
          {match[1]}
        </strong>
      );
      lastIdx = boldRegex.lastIndex;
    }
    if (lastIdx < text.length) {
      parts.push(text.substring(lastIdx));
    }
    return <React.Fragment key={keyPrefix}>{parts}</React.Fragment>;
  };

  const renderFormattedContent = (content: string, assistantMsgId: string) => {
    const parts: React.ReactNode[] = [];
    let lastIdx = 0;
    const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
    let match;

    while ((match = linkRegex.exec(content)) !== null) {
      if (match.index > lastIdx) {
        parts.push(renderBoldSegments(content.substring(lastIdx, match.index), `txt-${lastIdx}`));
      }
      const linkText = match[1];
      const linkUrl = match[2];

      if (linkUrl === '#contact' || linkUrl.includes('contact')) {
        parts.push(
          <button
            key={`contact-${match.index}`}
            type="button"
            onClick={() => onOpenContact?.(getLastUserQuestion(assistantMsgId))}
            className="text-cyan-400 underline font-semibold hover:text-cyan-300 inline cursor-pointer"
          >
            {linkText}
          </button>
        );
      } else {
        parts.push(
          <a
            key={`link-${match.index}`}
            href={linkUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="text-cyan-400 underline hover:text-cyan-300"
          >
            {linkText}
          </a>
        );
      }
      lastIdx = linkRegex.lastIndex;
    }

    if (lastIdx < content.length) {
      parts.push(renderBoldSegments(content.substring(lastIdx), `txt-${lastIdx}`));
    }

    return parts;
  };

  const handleSendPrompt = async (promptText: string) => {
    if (!promptText.trim() || isStreaming) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: promptText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    const assistantMsgId = `assistant-${Date.now()}`;
    const initialAssistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      sources: []
    };

    setMessages((prev) => [...prev, userMsg, initialAssistantMsg]);
    setInput('');
    setIsStreaming(true);
    await streamChat({
      question: promptText,
      history: messages.map((m) => ({ role: m.role, content: m.content })),
      authToken,
      onSources: (sources) => {
        setMessages((prev) =>
          prev.map((msg) => (msg.id === assistantMsgId ? { ...msg, sources } : msg))
        );
      },
      onToken: (token) => {
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMsgId ? { ...msg, content: msg.content + token } : msg
          )
        );
      },
      onDone: () => {
        setIsStreaming(false);
        onRefreshQuota();
      },
      onError: (err) => {
        setIsStreaming(false);
        if (err?.error === 'rate_limit_exceeded') {
          setRateLimitExceeded(true);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content:
                      err?.message ||
                      "⚠️ **Daily Query Limit Reached.** You've used all 10 questions available to anonymous visitors. Sign in with Google or GitHub to unlock 30 daily questions and connect directly with Brandon!"
                  }
                : msg
            )
          );
        } else {
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId
                ? {
                    ...msg,
                    content: "An error occurred while streaming the response. Please try again."
                  }
                : msg
            )
          );
        }
        onRefreshQuota();
      }
    });
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[480px] bg-[#090d16] border-l border-slate-800 shadow-2xl flex flex-col animate-in slide-in-from-right duration-300">
      {/* Drawer Header */}
      <div className="px-4 py-3.5 border-b border-slate-800 flex items-center justify-between bg-slate-900/80 backdrop-blur-md">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-md shadow-cyan-500/20">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div>
            <h3 className="font-bold text-sm text-white flex items-center gap-1.5">
              Brandon's AI Agent
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400" />
            </h3>
            <p className="text-[11px] font-mono text-cyan-400">
              Gemini 2.0 Flash • Hybrid RAG (Dense+BM25)
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {quota && (
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
              {quota.remaining}/{quota.limit} left
            </span>
          )}
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Quota Upgrade Banner (if anonymous or low) */}
      {!quota?.authenticated && (
        <div className="px-4 py-2 bg-gradient-to-r from-cyan-950/60 to-indigo-950/60 border-b border-cyan-800/40 flex items-center justify-between text-xs">
          <span className="text-cyan-300 font-medium">
            Anonymous visitor limit: {quota?.limit ?? 10} questions
          </span>
          <button
            onClick={onOpenAuth}
            className="text-white bg-cyan-600 hover:bg-cyan-500 px-2 py-0.5 rounded text-[11px] font-semibold transition-colors"
          >
            Unlock 30
          </button>
        </div>
      )}

      {/* Messages Thread */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m) => (
          <div
            key={m.id}
            className={`flex gap-3 text-xs sm:text-sm ${
              m.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {m.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-indigo-600/30 border border-indigo-500/40 flex items-center justify-center shrink-0 mt-0.5 text-indigo-300">
                <Bot className="w-4 h-4" />
              </div>
            )}

            <div
              className={`max-w-[85%] rounded-2xl px-4 py-3 leading-relaxed ${
                m.role === 'user'
                  ? 'bg-cyan-600 text-white rounded-tr-none'
                  : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none shadow-sm'
              }`}
            >
              <div className="whitespace-pre-wrap">
                {m.role === 'assistant' ? renderFormattedContent(m.content, m.id) : m.content}
              </div>

              {/* Direct Contact CTA if redirected to contact page or off-topic */}
              {m.role === 'assistant' &&
                (m.content.includes('#contact') ||
                  m.content.toLowerCase().includes('contact page') ||
                  m.content.includes('maybe you should ask him')) && (
                  <div className="mt-3 pt-2.5 border-t border-slate-800/80">
                    <button
                      onClick={() => onOpenContact?.(getLastUserQuestion(m.id))}
                      className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500/20 to-indigo-500/20 hover:from-cyan-500/30 hover:to-indigo-500/30 border border-cyan-500/40 text-cyan-300 hover:text-white text-xs font-semibold transition-all shadow-sm cursor-pointer group"
                    >
                      <Mail className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-110 transition-transform" />
                      <span>Send Question Directly to Brandon</span>
                    </button>
                  </div>
                )}

              {/* Referenced Topics */}
              {m.sources && m.sources.length > 0 && (
                <div className="mt-2.5 pt-2 border-t border-slate-800/60 flex items-center gap-1.5 flex-wrap">
                  <span className="text-[10px] font-mono text-slate-500">Related:</span>
                  {m.sources.map((s, idx) => (
                    <span
                      key={idx}
                      className="px-2 py-0.5 rounded-full bg-slate-800/80 text-[10px] text-cyan-300 font-medium border border-slate-700/60"
                    >
                      {s.title}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {m.role === 'user' && (
              <div className="w-7 h-7 rounded-full bg-cyan-600/30 border border-cyan-500/40 flex items-center justify-center shrink-0 mt-0.5 text-cyan-300">
                <UserIcon className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {isStreaming && (
          <div className="flex items-center gap-2 text-xs text-slate-400 font-mono">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            <span>Streaming tokens from Gemini 2.0 Flash...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Questions */}
      {messages.length <= 2 && (
        <div className="px-4 py-2 border-t border-slate-800/80 bg-slate-900/30 flex flex-wrap gap-1.5 text-[11px]">
          <button
            onClick={() => handleSendPrompt("What is Brandon's experience with Kubernetes and ArgoCD?")}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            "Kubernetes & ArgoCD"
          </button>
          <button
            onClick={() => handleSendPrompt("Tell me about Brandon's custom Go Prometheus exporter.")}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            "Go Prometheus Exporter"
          </button>
          <button
            onClick={() => handleSendPrompt("What AI agents did Brandon build in My Agentic Team?")}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
          >
            "My Agentic Team"
          </button>
        </div>
      )}

      {/* Chat Input Bar */}
      <div className="p-3.5 border-t border-slate-800 bg-slate-900/90">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendPrompt(input);
          }}
          className="flex items-center gap-2"
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={
              rateLimitExceeded
                ? "Daily limit reached. Sign in above to unlock."
                : "Ask about Kubernetes, Terraform, MLOps, Kafka..."
            }
            disabled={isStreaming || rateLimitExceeded}
            className="flex-1 px-3.5 py-2.5 text-xs sm:text-sm rounded-xl bg-slate-950 border border-slate-800 focus:border-cyan-500 focus:outline-none text-white placeholder-slate-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isStreaming || rateLimitExceeded}
            className="p-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>
    </div>
  );
};
