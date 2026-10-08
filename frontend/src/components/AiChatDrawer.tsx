import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Sparkles, X, Send, Bot, User as UserIcon, Mail, Minus, Maximize2 } from 'lucide-react';
import { ChatMessage, QuotaStatus } from '../types';
import { streamChat } from '../lib/api';

interface AiChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  quota: QuotaStatus | null;
  onRefreshQuota: () => void;
  onOpenAuth: () => void;
  initialPrompt?: string;
  onClearInitialPrompt?: () => void;
  authToken?: string | null;
  onOpenContact?: (initialQuestion?: string) => void;
}

const STREAMING_PHRASES = [
  "Deep thinking...",
  "Consulting Claude...",
  "Brewing a fresh pot of coffee...",
  "Feeding the cats...",
  "Checking Brandon's resume...",
  "Untangling YAML indentation...",
  "Querying Hybrid RAG retrieval engine...",
  "Converting caffeine into tokens...",
  "Running terraform plan in memory...",
  "Grepping through git commit logs...",
  "Calibrating Kubernetes pods...",
  "Synthesizing distributed systems knowledge...",
  "Asking the terminal politely...",
  "Recalibrating Reciprocal Rank Fusion...",
  "Double-checking ArgoCD sync status...",
  "Optimizing scale-to-zero FinOps metrics...",
  "Pondering distributed consensus (Raft)...",
  "Petting the cats for extra compute..."
];

const getRandomPhrase = (current?: string): string => {
  const pool = STREAMING_PHRASES.filter((p) => p !== current);
  return pool[Math.floor(Math.random() * pool.length)];
};

export const AiChatDrawer: React.FC<AiChatDrawerProps> = ({
  isOpen,
  onClose,
  quota,
  onRefreshQuota,
  onOpenAuth,
  initialPrompt,
  onClearInitialPrompt,
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
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false);
  const [streamingPhrase, setStreamingPhrase] = useState<string>(() => getRandomPhrase());
  const [rateLimitExceeded, setRateLimitExceeded] = useState(false);
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
  const [isMinimized, setIsMinimized] = useState(false);

  const targetAuthLimit = quota?.auth_limit || Number(import.meta.env.VITE_AUTH_DAILY_LIMIT) || 10;
  const targetAnonLimit = quota?.anon_limit || quota?.limit || Number(import.meta.env.VITE_ANON_DAILY_LIMIT) || 5;

  // Adjustable Drawer Width
  const DEFAULT_DRAWER_WIDTH = 420;
  const MIN_DRAWER_WIDTH = 340;
  const [width, setWidth] = useState<number>(() => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('portfolio_chat_width');
        if (saved) {
          const parsed = parseInt(saved, 10);
          if (!isNaN(parsed) && parsed >= MIN_DRAWER_WIDTH) {
            return Math.min(parsed, window.innerWidth - 48);
          }
        }
      } catch {}
    }
    return DEFAULT_DRAWER_WIDTH;
  });

  const [isResizing, setIsResizing] = useState(false);
  const isResizingRef = useRef(false);
  const widthRef = useRef(width);
  widthRef.current = width;

  useEffect(() => {
    const handleWindowResize = () => {
      const maxW = Math.max(MIN_DRAWER_WIDTH, window.innerWidth - 48);
      setWidth((prev) => (prev > maxW ? maxW : prev));
    };
    window.addEventListener('resize', handleWindowResize);
    return () => window.removeEventListener('resize', handleWindowResize);
  }, []);

  const startResizing = useCallback((e: React.MouseEvent | React.TouchEvent) => {
    e.preventDefault();
    setIsResizing(true);
    isResizingRef.current = true;
    document.body.style.cursor = 'ew-resize';
    document.body.style.userSelect = 'none';
  }, []);

  const stopResizing = useCallback(() => {
    if (isResizingRef.current) {
      setIsResizing(false);
      isResizingRef.current = false;
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      try {
        localStorage.setItem('portfolio_chat_width', widthRef.current.toString());
      } catch {}
    }
  }, []);

  const resize = useCallback((e: MouseEvent | TouchEvent) => {
    if (!isResizingRef.current) return;
    const clientX = 'touches' in e ? e.touches[0].clientX : e.clientX;
    const maxW = Math.max(MIN_DRAWER_WIDTH, Math.min(900, window.innerWidth - 48));
    const calculatedWidth = window.innerWidth - clientX;
    const newWidth = Math.max(MIN_DRAWER_WIDTH, Math.min(calculatedWidth, maxW));
    setWidth(newWidth);
    widthRef.current = newWidth;
  }, []);

  useEffect(() => {
    window.addEventListener('mousemove', resize);
    window.addEventListener('mouseup', stopResizing);
    window.addEventListener('touchmove', resize);
    window.addEventListener('touchend', stopResizing);
    return () => {
      window.removeEventListener('mousemove', resize);
      window.removeEventListener('mouseup', stopResizing);
      window.removeEventListener('touchmove', resize);
      window.removeEventListener('touchend', stopResizing);
    };
  }, [resize, stopResizing]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const isStreamingRef = useRef(false);
  const handledInitialPromptRef = useRef<string | null>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isStreaming]);

  useEffect(() => {
    if (!isWaitingForResponse) return;
    setStreamingPhrase(getRandomPhrase());
    const interval = setInterval(() => {
      setStreamingPhrase((prev) => getRandomPhrase(prev));
    }, 2400);
    return () => clearInterval(interval);
  }, [isWaitingForResponse]);

  // Handle drawer open/close transitions
  useEffect(() => {
    if (!isOpen) {
      handledInitialPromptRef.current = null;
      setIsMinimized(false);
    } else if (initialPrompt) {
      setIsMinimized(false);
    }
  }, [isOpen, initialPrompt]);

  // Focus input on open or unminimize
  useEffect(() => {
    if (isOpen && !isMinimized && !rateLimitExceeded && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen, isMinimized, rateLimitExceeded]);

  // Send initial prompt strictly once per distinct prompt text
  useEffect(() => {
    if (isOpen && initialPrompt && handledInitialPromptRef.current !== initialPrompt) {
      handledInitialPromptRef.current = initialPrompt;
      handleSendPrompt(initialPrompt);
      onClearInitialPrompt?.();
    }
  }, [isOpen, initialPrompt, onClearInitialPrompt]);

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
    if (!promptText.trim() || isStreamingRef.current) return;

    isStreamingRef.current = true;
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
    setIsWaitingForResponse(true);
    try {
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
          setIsWaitingForResponse(false);
          setMessages((prev) =>
            prev.map((msg) =>
              msg.id === assistantMsgId ? { ...msg, content: msg.content + token } : msg
            )
          );
        },
        onDone: () => {
          isStreamingRef.current = false;
          setIsWaitingForResponse(false);
          setIsStreaming(false);
          onRefreshQuota();
          setTimeout(() => inputRef.current?.focus(), 10);
        },
        onError: (err) => {
          isStreamingRef.current = false;
          setIsWaitingForResponse(false);
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
                        `⚠️ **Daily Query Limit Reached.** You've used all ${targetAnonLimit} questions available to anonymous visitors. Sign in with Google or GitHub to unlock ${targetAuthLimit} daily questions and connect directly with Brandon!`
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
          setTimeout(() => inputRef.current?.focus(), 10);
        }
      });
    } catch {
      isStreamingRef.current = false;
      setIsWaitingForResponse(false);
      setIsStreaming(false);
    }
  };

  if (!isOpen) return null;

  if (isMinimized) {
    return (
      <div
        onClick={() => setIsMinimized(false)}
        className="fixed bottom-0 right-0 sm:right-6 z-40 w-full sm:w-[380px] h-12 bg-slate-900/95 backdrop-blur-md border border-b-0 border-slate-700/80 rounded-t-xl shadow-2xl flex items-center justify-between px-3.5 cursor-pointer transition-all hover:bg-slate-800/95 group animate-in slide-in-from-bottom duration-200"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-md shadow-cyan-500/20 shrink-0">
            <Sparkles className="w-3.5 h-3.5 text-white" />
          </div>
          <div className="min-w-0">
            <h4 className="font-bold text-xs text-white flex items-center gap-1.5 truncate">
              Brandon's AI Agent
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
            </h4>
            <p className="text-[10px] font-mono text-cyan-400 truncate">
              {isWaitingForResponse
                ? streamingPhrase
                : isStreaming
                ? "Streaming response..."
                : `${messages.filter((m) => m.role === 'user').length} quer${
                    messages.filter((m) => m.role === 'user').length === 1 ? 'y' : 'ies'
                  } • Click to expand`}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0" onClick={(e) => e.stopPropagation()}>
          {quota && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
              {quota.remaining}/{quota.limit}
            </span>
          )}
          <button
            onClick={() => setIsMinimized(false)}
            title="Maximize chat"
            className="p-1 text-slate-400 hover:text-white hover:bg-slate-700/60 rounded-md transition-colors cursor-pointer"
          >
            <Maximize2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onClose}
            title="Close chat"
            className="p-1 text-slate-400 hover:text-white hover:bg-slate-700/60 rounded-md transition-colors cursor-pointer"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    );
  }

  return (
    <div
      style={{
        width: typeof window !== 'undefined' && window.innerWidth < 640 ? '100%' : `${width}px`
      }}
      className={`fixed inset-x-0 sm:inset-x-auto sm:right-0 top-16 bottom-0 z-40 w-full sm:w-auto max-w-full bg-[#090d16] border-l border-slate-800 shadow-2xl flex flex-col ${
        isResizing ? 'transition-none select-none' : 'animate-in slide-in-from-right duration-300'
      }`}
    >
      {/* Resizable Left Edge Handle */}
      <div
        onMouseDown={startResizing}
        onTouchStart={startResizing}
        onDoubleClick={() => {
          setWidth(DEFAULT_DRAWER_WIDTH);
          widthRef.current = DEFAULT_DRAWER_WIDTH;
          try {
            localStorage.setItem('portfolio_chat_width', DEFAULT_DRAWER_WIDTH.toString());
          } catch {}
        }}
        title="Drag left/right to resize width • Double-click to reset"
        className="hidden sm:flex absolute -left-2 top-0 bottom-0 w-4 cursor-ew-resize items-center justify-center z-50 group/handle select-none"
      >
        <div
          className={`w-1 h-full transition-colors duration-150 rounded-full ${
            isResizing
              ? 'bg-cyan-400 shadow-[0_0_10px_rgba(34,211,238,0.7)]'
              : 'group-hover/handle:bg-cyan-500/80 bg-transparent'
          }`}
        />
        <div
          className={`absolute top-1/2 -translate-y-1/2 w-3.5 h-8 rounded-full border border-slate-700/80 transition-all duration-150 flex flex-col items-center justify-center gap-1 shadow-md ${
            isResizing
              ? 'bg-cyan-950 border-cyan-400 opacity-100 scale-105'
              : 'bg-slate-900 group-hover/handle:bg-slate-800 group-hover/handle:border-cyan-500/60 opacity-0 group-hover/handle:opacity-100'
          }`}
        >
          <div className="w-1 h-1 rounded-full bg-slate-400 group-hover/handle:bg-cyan-300" />
          <div className="w-1 h-1 rounded-full bg-slate-400 group-hover/handle:bg-cyan-300" />
          <div className="w-1 h-1 rounded-full bg-slate-400 group-hover/handle:bg-cyan-300" />
        </div>
      </div>

      {/* Drawer Header */}
      <div className="px-4 py-3 border-b border-slate-800 flex items-center justify-between bg-slate-900/80 backdrop-blur-md">
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-600 flex items-center justify-center shadow-md shadow-cyan-500/20 shrink-0">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <div className="min-w-0">
            <h3 className="font-bold text-sm text-white flex items-center gap-1.5 truncate">
              Brandon's AI Agent
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 shrink-0" />
            </h3>
            <p className="text-[10.5px] font-mono text-cyan-400 truncate">
              Gemini 2.0 Flash • Hybrid RAG
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {quota && (
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
              {quota.remaining}/{quota.limit} left
            </span>
          )}
          <button
            onClick={() => setIsMinimized(true)}
            title="Minimize chat"
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-md transition-colors cursor-pointer"
          >
            <Minus className="w-4 h-4" />
          </button>
          <button
            onClick={onClose}
            title="Close chat"
            className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-md transition-colors cursor-pointer"
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
            Unlock {targetAuthLimit}
          </button>
        </div>
      )}

      {/* Messages Thread */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-3.5 sm:p-4 space-y-4 overscroll-contain">
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
              className={`min-w-0 max-w-[88%] sm:max-w-[85%] rounded-2xl px-4 py-3 leading-relaxed break-words [overflow-wrap:anywhere] ${
                m.role === 'user'
                  ? 'bg-cyan-600 text-white rounded-tr-none'
                  : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none shadow-sm'
              }`}
            >
              <div className="whitespace-pre-wrap break-words [overflow-wrap:anywhere]">
                {m.role === 'assistant' ? (
                  m.content ? (
                    renderFormattedContent(m.content, m.id)
                  ) : (
                    <div className="flex items-center gap-2 font-mono text-xs text-slate-300">
                      <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping shrink-0" />
                      <span className="transition-all duration-300">{streamingPhrase}</span>
                    </div>
                  )
                ) : (
                  m.content
                )}
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
      <div className="p-3 sm:p-3.5 pb-[max(0.75rem,env(safe-area-inset-bottom))] border-t border-slate-800 bg-slate-900/95 backdrop-blur-md">
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
            disabled={rateLimitExceeded}
            className="flex-1 px-3.5 py-2.5 text-base sm:text-sm rounded-xl bg-slate-950 border border-slate-800 focus:border-cyan-500 focus:outline-none text-white placeholder-slate-500 disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isStreaming || rateLimitExceeded}
            className="p-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 disabled:opacity-40 disabled:cursor-not-allowed text-white transition-colors cursor-pointer"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
        <p className="mt-2 text-center text-[11px] text-slate-500 leading-tight">
          AI can make mistakes. Check with{' '}
          <button
            type="button"
            onClick={() => onOpenContact?.()}
            className="text-slate-400 hover:text-cyan-400 underline underline-offset-2 transition-colors cursor-pointer"
          >
            Brandon
          </button>{' '}
          for accurate information.
        </p>
      </div>
    </div>
  );
};
