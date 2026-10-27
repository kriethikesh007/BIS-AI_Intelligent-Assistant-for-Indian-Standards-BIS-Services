import React, { useState, useRef, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Copy,
  Check,
  RotateCcw,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  AlertTriangle,
  Terminal,
  ArrowDown,
  Square,
  BookOpen,
  FileText,
  Compass,
} from 'lucide-react';
import { cn } from '../utils/cn';
import { Button, Badge, Card, Skeleton } from '../components/ui';
import { sendChatMessage } from '../services/api/endpoints';
import type { ChatResponseData, ChatHistoryItem } from '../types/api';

/* ─── Message Interface ─── */
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  status: 'sending' | 'success' | 'error';
  error?: string;
  data?: ChatResponseData;
  query?: string;
}

/* ─── Refined Suggested Prompts ─── */
const SUGGESTED_PROMPTS = [
  {
    label: 'Motorcycle Helmets',
    prompt: 'Which standard applies to motorcycle helmets and what tests are mandatory?',
    code: 'IS 4151',
  },
  {
    label: 'Packaged Drinking Water',
    prompt: 'What are the BIS certification rules for packaged drinking water jars?',
    code: 'IS 14543',
  },
  {
    label: '22K Gold Hallmarking',
    prompt: 'Explain the 6-digit laser HUID and karat fineness rules for 22K gold jewelry.',
    code: 'IS 1417',
  },
  {
    label: 'ISI vs CRS Scheme',
    prompt: 'What is the difference between Scheme I (ISI Mark) and Scheme II (CRS registration)?',
    code: 'Compliance',
  },
];

/* ─── Assistant Evidence / Source Citation Card ─── */
function EvidenceCard({ data }: { data: ChatResponseData }) {
  const [expanded, setExpanded] = useState(false);

  const standardCode = data.recommended_standard || data.relevant_standard;
  const referenceDoc = data.reference_document || data.reference;
  const clauseInfo = data.page_section_clause || data.clause_verification;
  const sourceUrl = data.source;
  const confidenceScore =
    data.confidence_score !== null && data.confidence_score !== undefined
      ? Math.round(data.confidence_score * 100)
      : data.confidence
      ? Number.parseFloat(data.confidence) <= 1
        ? Math.round(Number.parseFloat(data.confidence) * 100)
        : data.confidence
      : null;

  const hasEvidence = Boolean(
    standardCode || referenceDoc || clauseInfo || (sourceUrl && sourceUrl.startsWith('http'))
  );

  if (!hasEvidence) return null;

  return (
    <div
      className="mt-3.5 rounded-lg border text-xs overflow-hidden transition-all duration-150"
      style={{
        backgroundColor: 'var(--color-bg-secondary)',
        borderColor: 'var(--color-border-default)',
      }}
    >
      {/* Evidence Summary Header */}
      <div className="flex items-center justify-between p-2.5 sm:px-3">
        <div className="flex items-center gap-2 flex-wrap min-w-0">
          <div className="flex items-center gap-1.5 text-emerald-500 font-medium">
            <ShieldCheck size={14} className="shrink-0" />
            <span className="text-[11px] font-semibold">Verified Evidence</span>
          </div>

          {standardCode && (
            <span
              className="font-mono text-[11px] font-semibold px-2 py-0.5 rounded border"
              style={{
                backgroundColor: 'var(--color-bg-primary)',
                borderColor: 'var(--color-border-subtle)',
                color: 'var(--color-text-primary)',
              }}
            >
              {standardCode}
            </span>
          )}

          {confidenceScore !== null && (
            <span
              className="text-[10px] font-medium px-1.5 py-0.2 rounded"
              style={{
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                color: 'var(--color-brand)',
              }}
            >
              {confidenceScore}% confidence
            </span>
          )}

          {data.verification_status && (
            <span
              className="text-[10px] font-medium px-1.5 py-0.5 rounded border"
              style={{
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                borderColor: 'rgba(16, 185, 129, 0.25)',
                color: '#10b981',
              }}
            >
              {data.verification_status}
            </span>
          )}
        </div>

        <button
          type="button"
          onClick={() => setExpanded(prev => !prev)}
          className="p-1 rounded text-text-tertiary hover:text-text-primary transition-colors cursor-pointer shrink-0 ml-2"
          aria-label={expanded ? 'Collapse evidence' : 'Expand evidence'}
        >
          {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>
      </div>

      {/* Expandable Evidence Details */}
      {expanded && (
        <div
          className="px-3 pb-3 pt-1 border-t space-y-2 text-[11px]"
          style={{ borderColor: 'var(--color-border-subtle)' }}
        >
          {referenceDoc && (
            <div>
              <span className="text-text-tertiary font-medium block text-[10px] uppercase tracking-wider">
                Authorized Reference
              </span>
              <p className="mt-0.5 font-medium text-text-primary">{referenceDoc}</p>
            </div>
          )}

          {clauseInfo && (
            <div>
              <span className="text-text-tertiary font-medium block text-[10px] uppercase tracking-wider">
                Clause & Section
              </span>
              <p className="mt-0.5 text-text-secondary">{clauseInfo}</p>
            </div>
          )}

          {(data.why || data.reason) && (
            <div>
              <span className="text-text-tertiary font-medium block text-[10px] uppercase tracking-wider">
                Conformity Scope
              </span>
              <p className="mt-0.5 text-text-secondary leading-relaxed">
                {data.why || data.reason}
              </p>
            </div>
          )}

          {sourceUrl && sourceUrl.startsWith('http') && (
            <div className="pt-1">
              <a
                href={sourceUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 text-xs font-medium hover:underline text-brand-600 dark:text-brand-400"
              >
                <ExternalLink size={12} />
                <span>Open Official BIS Documentation</span>
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Collapsible Developer Diagnostics Bar ─── */
function DiagnosticsBar({ data }: { data: ChatResponseData }) {
  const [open, setOpen] = useState(false);

  const hasDiagnostics = Boolean(
    data.detected_intent ||
      data.router_intent ||
      data.intent ||
      data.llm_model ||
      data.processed_query ||
      data.detected_language
  );

  if (!hasDiagnostics) return null;

  return (
    <div className="mt-2 text-xs">
      <button
        type="button"
        onClick={() => setOpen(prev => !prev)}
        className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono text-text-tertiary hover:text-text-secondary transition-colors cursor-pointer"
      >
        <Terminal size={11} />
        <span>{open ? 'Hide telemetry' : 'Debug telemetry'}</span>
      </button>

      {open && (
        <div
          className="mt-1 p-2.5 rounded-lg border font-mono text-[10px] space-y-1.5 overflow-x-auto"
          style={{
            backgroundColor: 'var(--color-bg-tertiary)',
            borderColor: 'var(--color-border-subtle)',
            color: 'var(--color-text-secondary)',
          }}
        >
          <div className="grid grid-cols-2 gap-2">
            <div>
              <span className="opacity-60">Intent: </span>
              <span className="font-semibold text-text-primary">
                {data.detected_intent || data.router_intent || data.intent || 'STANDARD_LOOKUP'}
              </span>
            </div>
            <div>
              <span className="opacity-60">Model: </span>
              <span className="text-text-primary">
                {data.llm_model || 'Voting Ensemble / Groq'}
              </span>
            </div>
            {data.detected_language && (
              <div>
                <span className="opacity-60">Language: </span>
                <span className="font-semibold text-text-primary">
                  {data.detected_language}
                </span>
              </div>
            )}
            {data.match_type && (
              <div>
                <span className="opacity-60">Match: </span>
                <span className="text-text-primary">{data.match_type}</span>
              </div>
            )}
          </div>
          {data.processed_query && (
            <div className="pt-1 border-t" style={{ borderColor: 'var(--color-border-subtle)' }}>
              <span className="opacity-60 block">Normalized Query:</span>
              <span className="text-text-primary break-all">{data.processed_query}</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ─── Main Assistant Flagship Component ─── */
export default function AssistantPage() {
  const [searchParams] = useSearchParams();
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [showScrollBottom, setShowScrollBottom] = useState(false);

  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const isUserScrolledUpRef = useRef(false);
  const abortControllerRef = useRef<AbortController | null>(null);
  const handledInitialQueryRef = useRef(false);

  // Auto-resize textarea
  const adjustTextareaHeight = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    const computedHeight = Math.min(Math.max(textarea.scrollHeight, 40), 130);
    textarea.style.height = `${computedHeight}px`;
  }, []);

  useEffect(() => {
    adjustTextareaHeight();
  }, [input, adjustTextareaHeight]);

  const messagesRef = useRef(messages);
  messagesRef.current = messages;

  // Scroll management
  const handleScroll = useCallback(() => {
    const el = scrollContainerRef.current;
    if (!el) return;
    const isNearBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 80;
    isUserScrolledUpRef.current = !isNearBottom;
    setShowScrollBottom(!isNearBottom && el.scrollHeight > el.clientHeight + 80);
  }, []);

  const scrollToBottom = useCallback((smooth = true) => {
    const el = scrollContainerRef.current;
    if (!el) return;
    el.scrollTo({
      top: el.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto',
    });
    isUserScrolledUpRef.current = false;
    setShowScrollBottom(false);
  }, []);

  useEffect(() => {
    if (!isUserScrolledUpRef.current) {
      scrollToBottom();
    }
  }, [messages, isGenerating, scrollToBottom]);

  // Copy to clipboard helper
  const handleCopy = useCallback((id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => {
      setCopiedId(null);
    }, 1800);
  }, []);

  // Reset conversation
  const handleClearConversation = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsGenerating(false);
    setMessages([]);
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = '40px';
    }
  }, []);

  // Send message
  const handleSend = useCallback(async (overrideQuery?: string) => {
    const queryToSend = (overrideQuery ?? input).trim();
    if (!queryToSend || isGenerating) return;

    if (!overrideQuery) {
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = '40px';
      }
    }

    abortControllerRef.current?.abort();
    const controller = new AbortController();
    abortControllerRef.current = controller;

    const timestampNow = new Date();
    const userMessageId = `user-${timestampNow.getTime()}`;
    const assistantMessageId = `asst-${timestampNow.getTime() + 1}`;

    const userMsg: Message = {
      id: userMessageId,
      role: 'user',
      content: queryToSend,
      timestamp: timestampNow,
      status: 'success',
    };

    const pendingAssistantMsg: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      timestamp: timestampNow,
      status: 'sending',
      query: queryToSend,
    };

    setMessages(prev => [...prev, userMsg, pendingAssistantMsg]);
    setIsGenerating(true);
    isUserScrolledUpRef.current = false;

    const history: ChatHistoryItem[] = messagesRef.current
      .filter(m => m.status === 'success' && m.content.trim())
      .map(m => ({
        role: m.role,
        content: m.content,
      }));

    try {
      const data = await sendChatMessage(queryToSend, {
        history,
        signal: controller.signal,
      });

      setMessages(prev =>
        prev.map(msg =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                status: 'success',
                content: data.answer || 'No direct answer could be retrieved for this query.',
                data,
              }
            : msg
        )
      );
    } catch (err: unknown) {
      if (controller.signal.aborted) {
        setMessages(prev => prev.filter(msg => msg.id !== assistantMessageId));
        return;
      }
      const errorMessage =
        err instanceof Error ? err.message : 'Unable to connect to the BIS knowledge server.';

      setMessages(prev =>
        prev.map(msg =>
          msg.id === assistantMessageId
            ? {
                ...msg,
                status: 'error',
                error: errorMessage,
                content: 'Failed to retrieve response from the BIS-AI engine.',
              }
            : msg
        )
      );
    } finally {
      setIsGenerating(false);
    }
  }, [input, isGenerating]);

  // Handle URL param query `?q=...` on first mount
  useEffect(() => {
    const q = searchParams.get('q');
    if (q && !handledInitialQueryRef.current) {
      handledInitialQueryRef.current = true;
      handleSend(q);
    }
  }, [searchParams, handleSend]);

  // Keyboard shortcut: Enter sends, Shift+Enter newlines
  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div
      className="flex flex-col h-full min-h-0 w-full relative"
      style={{ backgroundColor: 'var(--color-bg-primary)' }}
    >
      {/* ─── Compact Header ─── */}
      <header
        className="flex items-center justify-between px-4 sm:px-6 h-11 border-b shrink-0 z-10"
        style={{
          backgroundColor: 'var(--color-bg-primary)',
          borderColor: 'var(--color-border-subtle)',
        }}
      >
        <div className="flex items-center gap-2 text-xs">
          <div className="flex items-center gap-1.5 font-medium text-text-secondary">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>BIS Knowledge Retrieval Active</span>
          </div>
          <span className="text-text-tertiary hidden sm:inline">•</span>
          <span className="text-text-tertiary hidden sm:inline text-[11px]">
            Strict Evidence Mode
          </span>
        </div>

        {messages.length > 0 && (
          <Button
            variant="ghost"
            size="xs"
            onClick={handleClearConversation}
            icon={<RotateCcw size={12} />}
            title="Start new conversation"
          >
            New Chat
          </Button>
        )}
      </header>

      {/* ─── Main Chat Scroll Area ─── */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto px-4 py-4 sm:py-6"
      >
        <div className="max-w-[800px] w-full mx-auto flex flex-col gap-6">
          {/* Initial First-Use Empty State */}
          {messages.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.25 }}
              className="py-10 sm:py-16 flex flex-col items-center text-center"
            >
              {/* Refined Assistant Emblem */}
              <div
                className="w-10 h-10 rounded-xl border flex items-center justify-center mb-4 shadow-xs"
                style={{
                  backgroundColor: 'var(--color-bg-secondary)',
                  borderColor: 'var(--color-border-default)',
                  color: 'var(--color-brand)',
                }}
              >
                <Compass size={22} strokeWidth={1.8} />
              </div>

              {/* Concise Title & Subtitle */}
              <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-text-primary">
                Your guide to Indian Standards
              </h1>
              <p className="mt-1.5 text-xs sm:text-sm max-w-md text-text-secondary leading-relaxed">
                Source-backed compliance assistance for Indian Standards (IS), mandatory certification schemes, and hallmarking.
              </p>

              {/* Centered Composer for First-Use (Linear / Claude style) */}
              <div className="w-full max-w-xl mt-7">
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    handleSend();
                  }}
                  className="rounded-xl border shadow-sm transition-all duration-150 focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-500/20 text-left"
                  style={{
                    backgroundColor: 'var(--color-bg-elevated)',
                    borderColor: 'var(--color-border-default)',
                  }}
                >
                  <textarea
                    ref={textareaRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    disabled={isGenerating}
                    placeholder="Ask about standards, certification schemes, or IS codes..."
                    rows={1}
                    className="w-full bg-transparent px-3.5 py-3 text-xs sm:text-sm outline-none resize-none placeholder:text-text-tertiary text-text-primary"
                    style={{ minHeight: '44px', maxHeight: '130px' }}
                  />
                  <div className="flex items-center justify-between px-3 pb-2 pt-1 border-t" style={{ borderColor: 'var(--color-border-subtle)' }}>
                    <span className="text-[10px] text-text-tertiary">
                      Press <kbd className="px-1 py-0.2 rounded border bg-bg-tertiary">Enter</kbd> to ask
                    </span>
                    <Button
                      type="submit"
                      variant="primary"
                      size="xs"
                      disabled={!input.trim() || isGenerating}
                      icon={<Send size={11} />}
                    >
                      Ask
                    </Button>
                  </div>
                </form>
              </div>

              {/* 4 Compact Suggested Prompts */}
              <div className="mt-6 w-full max-w-xl">
                <div className="text-[10px] font-semibold uppercase tracking-wider text-text-tertiary mb-2 text-left">
                  Suggested inquiries
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-left">
                  {SUGGESTED_PROMPTS.map((item) => (
                    <button
                      key={item.label}
                      type="button"
                      onClick={() => handleSend(item.prompt)}
                      className="group flex items-start justify-between gap-2 p-2.5 rounded-lg border text-left transition-all duration-120 hover:border-border-strong hover:bg-bg-secondary cursor-pointer"
                      style={{
                        backgroundColor: 'var(--color-bg-primary)',
                        borderColor: 'var(--color-border-default)',
                      }}
                    >
                      <div className="min-w-0">
                        <div className="text-xs font-semibold text-text-primary group-hover:text-brand-600 dark:text-brand-400 transition-colors">
                          {item.label}
                        </div>
                        <div className="text-[11px] text-text-secondary line-clamp-1 mt-0.5">
                          {item.prompt}
                        </div>
                      </div>
                      <span className="text-[9px] font-mono px-1 py-0.2 rounded shrink-0 bg-bg-tertiary text-text-tertiary">
                        {item.code}
                      </span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Subtle Trust & Reference Note */}
              <p className="mt-6 text-[11px] text-text-tertiary max-w-sm">
                Answers cite authorized Bureau of Indian Standards clauses, testing parameters, and official URLs.
              </p>
            </motion.div>
          ) : (
            /* ─── Active Message Conversation Stream ─── */
            <div className="flex flex-col gap-6">
              <AnimatePresence initial={false}>
                {messages.map((message) => (
                  <motion.div
                    key={message.id}
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.18 }}
                    className={cn(
                      'flex w-full',
                      message.role === 'user' ? 'justify-end' : 'justify-start'
                    )}
                  >
                    {message.role === 'user' ? (
                      /* User Message: Restrained Dark Pill/Card (NO giant bright blue bubble) */
                      <div className="flex items-end gap-2 max-w-[85%] sm:max-w-[75%]">
                        <div
                          className="px-3.5 py-2.5 rounded-xl rounded-br-xs shadow-xs text-xs sm:text-sm leading-relaxed whitespace-pre-wrap select-text border"
                          style={{
                            backgroundColor: 'var(--color-bg-tertiary)',
                            borderColor: 'var(--color-border-default)',
                            color: 'var(--color-text-primary)',
                          }}
                        >
                          {message.content}
                        </div>
                        <div
                          className="w-6 h-6 rounded-full flex items-center justify-center shrink-0 mb-0.5"
                          style={{
                            backgroundColor: 'var(--color-bg-tertiary)',
                            color: 'var(--color-text-tertiary)',
                          }}
                        >
                          <User size={12} />
                        </div>
                      </div>
                    ) : (
                      /* Assistant Message: Editorial Typography & Evidence */
                      <div className="flex items-start gap-3 w-full">
                        <div
                          className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0 mt-0.5 border shadow-xs"
                          style={{
                            backgroundColor: 'var(--color-bg-secondary)',
                            borderColor: 'var(--color-border-default)',
                            color: 'var(--color-brand)',
                          }}
                        >
                          <Bot size={15} />
                        </div>

                        <div className="flex-1 min-w-0">
                          {message.status === 'sending' ? (
                            /* Loading / Generating State */
                            <div className="space-y-2.5 pt-1">
                              <div className="flex items-center gap-2">
                                <span className="inline-flex gap-1 items-center">
                                  <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-bounce" />
                                  <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-bounce [animation-delay:0.15s]" />
                                  <span className="w-1.5 h-1.5 rounded-full bg-brand-500 animate-bounce [animation-delay:0.3s]" />
                                </span>
                                <span className="text-xs text-text-tertiary">
                                  Retrieving authorized Indian Standards...
                                </span>
                              </div>
                              <Skeleton className="h-4 w-3/4" />
                              <Skeleton className="h-4 w-1/2" />
                            </div>
                          ) : message.status === 'error' ? (
                            /* Error State */
                            <div
                              className="p-3 rounded-lg border text-xs text-rose-500"
                              style={{
                                backgroundColor: 'var(--color-error-bg)',
                                borderColor: 'rgba(239, 68, 68, 0.25)',
                              }}
                            >
                              <div className="flex items-center gap-1.5 font-semibold">
                                <AlertTriangle size={14} />
                                <span>Query Processing Error</span>
                              </div>
                              <p className="mt-1 text-[11px] opacity-90">{message.error || message.content}</p>
                              {message.query && (
                                <Button
                                  variant="secondary"
                                  size="xs"
                                  className="mt-2 text-xs"
                                  onClick={() => handleSend(message.query)}
                                  icon={<RotateCcw size={11} />}
                                >
                                  Retry Query
                                </Button>
                              )}
                            </div>
                          ) : (
                            /* Success Answer Output */
                            <>
                              <div className="markdown-content text-xs sm:text-sm">
                                <ReactMarkdown
                                  remarkPlugins={[remarkGfm]}
                                  components={{
                                    table: ({ children }) => (
                                      <div className="table-container">
                                        <table>{children}</table>
                                      </div>
                                    ),
                                    a: ({ href, children }) => (
                                      <a
                                        href={href}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="font-medium underline hover:opacity-80 text-brand-600 dark:text-brand-400"
                                      >
                                        {children}
                                      </a>
                                    ),
                                  }}
                                >
                                  {message.content}
                                </ReactMarkdown>
                              </div>

                              {/* Source & Verified Evidence Card */}
                              {message.data && <EvidenceCard data={message.data} />}

                              {/* Collapsible Developer Diagnostics */}
                              {message.data && <DiagnosticsBar data={message.data} />}

                              {/* Message Action Footer: Copy button & timestamp */}
                              <div
                                className="mt-2.5 pt-2 border-t flex items-center justify-between text-[11px]"
                                style={{ borderColor: 'var(--color-border-subtle)' }}
                              >
                                <button
                                  type="button"
                                  onClick={() => handleCopy(message.id, message.content)}
                                  className="inline-flex items-center gap-1 text-text-tertiary hover:text-text-secondary transition-colors cursor-pointer"
                                  title="Copy response"
                                >
                                  {copiedId === message.id ? (
                                    <>
                                      <Check size={11} className="text-emerald-500" />
                                      <span className="text-emerald-500 font-medium">Copied</span>
                                    </>
                                  ) : (
                                    <>
                                      <Copy size={11} />
                                      <span>Copy</span>
                                    </>
                                  )}
                                </button>

                                <span className="text-[10px] text-text-tertiary font-mono">
                                  {new Date(message.timestamp).toLocaleTimeString([], {
                                    hour: '2-digit',
                                    minute: '2-digit',
                                  })}
                                </span>
                              </div>
                            </>
                          )}
                        </div>
                      </div>
                    )}
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          )}
        </div>
      </div>

      {/* Floating Scroll to Bottom Indicator */}
      {showScrollBottom && (
        <button
          type="button"
          onClick={() => scrollToBottom(true)}
          className="absolute bottom-20 right-6 sm:right-10 z-20 p-2 rounded-full shadow-md border transition-all hover:scale-105 active:scale-95 cursor-pointer"
          style={{
            backgroundColor: 'var(--color-bg-elevated)',
            borderColor: 'var(--color-border-default)',
            color: 'var(--color-text-secondary)',
          }}
          aria-label="Scroll to bottom"
        >
          <ArrowDown size={14} />
        </button>
      )}

      {/* ─── Bottom Floating Message Composer (when messages exist) ─── */}
      {messages.length > 0 && (
        <div
          className="border-t p-3 sm:p-4 shrink-0"
          style={{
            backgroundColor: 'var(--color-bg-primary)',
            borderColor: 'var(--color-border-subtle)',
          }}
        >
          <div className="max-w-[800px] w-full mx-auto">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="relative flex flex-col rounded-xl border transition-all duration-150 focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-500/20"
              style={{
                backgroundColor: 'var(--color-bg-elevated)',
                borderColor: 'var(--color-border-default)',
              }}
            >
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isGenerating}
                placeholder="Ask follow-up question or search standard number..."
                rows={1}
                className="w-full bg-transparent px-3 py-2.5 text-xs sm:text-sm outline-none resize-none placeholder:text-text-tertiary text-text-primary"
                style={{ minHeight: '40px', maxHeight: '120px' }}
              />

              <div className="flex items-center justify-between px-3 pb-2 pt-0.5">
                <span className="text-[10px] text-text-tertiary hidden sm:inline">
                  <kbd className="px-1 py-0.2 rounded border bg-bg-tertiary">Enter</kbd> send, <kbd className="px-1 py-0.2 rounded border bg-bg-tertiary">Shift+Enter</kbd> newline
                </span>
                <span className="text-[10px] text-text-tertiary sm:hidden">
                  BIS Grounded
                </span>

                <div className="flex items-center gap-1.5 ml-auto">
                  {isGenerating ? (
                    <Button
                      type="button"
                      variant="ghost"
                      size="xs"
                      onClick={() => abortControllerRef.current?.abort()}
                      className="text-red-500 hover:text-red-600 hover:bg-red-500/10"
                      icon={<Square size={11} className="fill-current" />}
                    >
                      Stop
                    </Button>
                  ) : (
                    <Button
                      type="submit"
                      variant="primary"
                      size="xs"
                      disabled={!input.trim() || isGenerating}
                      icon={<Send size={11} />}
                    >
                      Send
                    </Button>
                  )}
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
