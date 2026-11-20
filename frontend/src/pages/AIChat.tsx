import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import {
  Send,
  Plus,
  Menu,
  X,
  PenSquare,
  AlertTriangle,
  Clock,
  Phone,
  MessageCircle,
  RefreshCw,
} from 'lucide-react';
import api from '@/services/api';

// ─── Types ───────────────────────────────────────────────────────────────────

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  severity?: 'low' | 'medium' | 'high' | 'crisis';
  suggestions?: string[];
  isError?: boolean;
}

interface ChatSession {
  id: string;
  title: string;
  date: string;
  active?: boolean;
}

// ─── Sub-components ──────────────────────────────────────────────────────────

/** Teal avatar circle with "Z" */
const ZenithAvatar = ({ size = 'sm' }: { size?: 'sm' | 'md' | 'lg' }) => {
  const cls =
    size === 'lg'
      ? 'w-16 h-16 text-2xl'
      : size === 'md'
        ? 'w-10 h-10 text-base'
        : 'w-8 h-8 text-sm';
  return (
    <div
      className={`${cls} rounded-full bg-[#2F7A6D] text-white flex items-center justify-center font-bold flex-shrink-0 shadow-sm`}
    >
      Z
    </div>
  );
};

/** Animated typing indicator */
const TypingIndicator = () => (
  <div className="flex items-end gap-2 mb-4">
    <ZenithAvatar size="sm" />
    <div className="bg-white border border-gray-100 shadow-sm rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1.5">
      <span
        className="w-2 h-2 bg-[#2F7A6D]/60 rounded-full animate-bounce"
        style={{ animationDelay: '0ms' }}
      />
      <span
        className="w-2 h-2 bg-[#2F7A6D]/60 rounded-full animate-bounce"
        style={{ animationDelay: '150ms' }}
      />
      <span
        className="w-2 h-2 bg-[#2F7A6D]/60 rounded-full animate-bounce"
        style={{ animationDelay: '300ms' }}
      />
    </div>
  </div>
);

/** Severity-based styling helpers */
const getSeverityBorder = (severity?: string) => {
  switch (severity) {
    case 'crisis':
      return 'border-l-4 border-l-red-500';
    case 'high':
      return 'border-l-4 border-l-orange-500';
    case 'medium':
      return 'border-l-4 border-l-yellow-500';
    default:
      return '';
  }
};

const getSeverityIcon = (severity?: string) => {
  switch (severity) {
    case 'crisis':
      return <AlertTriangle className="h-3.5 w-3.5 text-red-600 flex-shrink-0" />;
    case 'high':
      return <AlertTriangle className="h-3.5 w-3.5 text-orange-600 flex-shrink-0" />;
    case 'medium':
      return <Clock className="h-3.5 w-3.5 text-yellow-600 flex-shrink-0" />;
    default:
      return null;
  }
};

// ─── Main Component ───────────────────────────────────────────────────────────

const AIChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [errorBanner, setErrorBanner] = useState<string | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);

  // Mock session history (replace with real API if available)
  const [sessions] = useState<ChatSession[]>([
    { id: 'current', title: 'Current Session', date: 'Today', active: true },
    { id: 'sess-2', title: 'Anxiety check-in', date: 'Yesterday' },
    { id: 'sess-3', title: 'Breathing exercises', date: '3 days ago' },
    { id: 'sess-4', title: 'Sleep concerns', date: 'Last week' },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const backendWarmed = useRef(false);

  // Pre-warm Render backend on mount (defeats cold start)
  useEffect(() => {
    if (!backendWarmed.current) {
      backendWarmed.current = true;
      const API_BASE_URL =
        import.meta.env.VITE_API_URL || `http://${window.location.hostname}:8000`;
      fetch(`${API_BASE_URL}/health`, { method: 'GET' }).catch(() => {});
    }
  }, []);

  // Auto-scroll to newest message
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping, scrollToBottom]);

  // Auto-resize textarea
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInputText(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  // Core send logic (preserved from original)
  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      setErrorBanner(null);
      setLastFailedMessage(null);

      const userMessage: Message = {
        id: Date.now().toString(),
        text,
        sender: 'user',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, userMessage]);
      setInputText('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
      setIsTyping(true);

      try {
        const res = await api.post(
          '/chat',
          {
            message: text,
            session_id: sessionId,
          },
          { timeout: 45000 }
        );
        const data = res.data;

        // Persist session_id so subsequent messages maintain context
        if (data.session_id && !sessionId) {
          setSessionId(data.session_id);
        }

        const aiResponse: Message = {
          id: (Date.now() + 1).toString(),
          text: data.text || 'I am here to support you.',
          sender: 'ai',
          timestamp: new Date(),
          severity: data.severity || 'low',
          suggestions: data.suggestions || [],
        };
        setMessages((prev) => [...prev, aiResponse]);
      } catch (error) {
        console.error('Chat API error:', error);

        const errorText =
          error instanceof DOMException && error.name === 'AbortError'
            ? 'The server is waking up — this can take up to a minute on the first request. Please try again.'
            : error instanceof Error
              ? `Unable to reach the AI service: ${error.message}`
              : 'Unable to connect to the AI backend. Please try again later.';

        setErrorBanner(errorText);
        setLastFailedMessage(text);

        // Also show error inline in chat
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: errorText,
          sender: 'ai',
          timestamp: new Date(),
          severity: 'medium',
          isError: true,
        };
        setMessages((prev) => [...prev, errorMessage]);
      } finally {
        setIsTyping(false);
      }
    },
    [sessionId]
  );

  const handleSendMessage = () => {
    sendMessage(inputText);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.key === 'Enter' && !e.shiftKey) || (e.key === 'Enter' && e.ctrlKey)) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleChipClick = (chip: string) => {
    sendMessage(chip);
  };

  const handleRetry = () => {
    if (lastFailedMessage) {
      setErrorBanner(null);
      sendMessage(lastFailedMessage);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setSessionId(null);
    setErrorBanner(null);
    setLastFailedMessage(null);
    setSidebarOpen(false);
  };

  const suggestionChips = [
    "I'm feeling anxious",
    'Help me relax',
    'I need to talk',
    'What can you do?',
  ];

  return (
    <div className="flex h-screen bg-[#F5F5F5] overflow-hidden">
      {/* ── Sidebar Overlay (mobile) ─────────────────────────── */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/40 z-20 md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* ── Left Sidebar ─────────────────────────────────────── */}
      <aside
        className={`
          fixed md:static z-30 top-0 left-0 h-full w-64 bg-white border-r border-gray-100 shadow-sm
          flex flex-col transition-transform duration-300
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
          md:translate-x-0
        `}
      >
        {/* Sidebar header */}
        <div className="p-4 border-b border-gray-100 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ZenithAvatar size="sm" />
            <span className="font-semibold text-gray-800 text-sm">Zenith</span>
          </div>
          <button
            className="md:hidden text-gray-500 hover:text-gray-700"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close sidebar"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* New Chat button */}
        <div className="p-3">
          <button
            onClick={handleNewChat}
            className="bg-[#2F7A6D] text-white rounded-lg w-full py-2.5 px-4 flex items-center justify-center gap-2 text-sm font-medium hover:bg-[#276860] transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Chat
          </button>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto px-2 pb-4">
          <p className="text-xs text-gray-400 uppercase tracking-wide px-2 py-2 font-medium">
            Recent
          </p>
          <ul className="space-y-0.5">
            {sessions.map((session) => (
              <li key={session.id}>
                <button
                  className={`w-full text-left rounded-lg px-3 py-2.5 text-sm transition-colors ${
                    session.active
                      ? 'bg-teal-100 border-l-2 border-[#2F7A6D] text-[#2F7A6D] font-medium'
                      : 'hover:bg-teal-50 text-gray-700'
                  }`}
                >
                  <span className="block truncate">{session.title}</span>
                  <span className="text-xs text-gray-400">{session.date}</span>
                </button>
              </li>
            ))}
          </ul>
        </div>

        {/* Crisis support footer */}
        <div className="p-3 border-t border-gray-100 bg-red-50">
          <p className="text-xs text-red-700 font-medium mb-2">Emergency Support</p>
          <div className="flex gap-2">
            <button
              onClick={() => window.open('tel:14416', '_self')}
              className="flex-1 flex items-center justify-center gap-1 bg-red-600 text-white text-xs rounded-md py-1.5 hover:bg-red-700 transition-colors"
            >
              <Phone className="h-3 w-3" />
              14416
            </button>
            <button
              onClick={() => window.open('tel:+912227546669', '_self')}
              className="flex-1 flex items-center justify-center gap-1 border border-red-300 text-red-700 text-xs rounded-md py-1.5 hover:bg-red-100 transition-colors"
            >
              <MessageCircle className="h-3 w-3" />
              AASRA
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main Chat Area ────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 h-full">
        {/* Chat header */}
        <header className="bg-white border-b border-gray-100 px-4 py-3 flex items-center gap-3 flex-shrink-0 shadow-sm">
          {/* Mobile hamburger */}
          <button
            className="md:hidden text-gray-500 hover:text-gray-700 p-1"
            onClick={() => setSidebarOpen(true)}
            aria-label="Open sidebar"
          >
            <Menu className="h-5 w-5" />
          </button>

          <ZenithAvatar size="md" />

          <div className="flex-1 min-w-0">
            <h1 className="font-semibold text-gray-900 text-base leading-tight">Zenith</h1>
            <p className="text-xs text-gray-500 leading-tight">AI Mental Wellness Companion</p>
          </div>

          <button
            onClick={handleNewChat}
            className="p-2 rounded-lg hover:bg-teal-50 text-[#2F7A6D] transition-colors"
            title="New conversation"
            aria-label="Start new conversation"
          >
            <PenSquare className="h-4 w-4" />
          </button>
        </header>

        {/* Error banner */}
        {errorBanner && (
          <div className="bg-red-50 border-b border-red-200 px-4 py-2.5 flex items-center gap-3 flex-shrink-0">
            <AlertTriangle className="h-4 w-4 text-red-600 flex-shrink-0" />
            <p className="text-red-700 text-sm flex-1 min-w-0 truncate">{errorBanner}</p>
            {lastFailedMessage && (
              <button
                onClick={handleRetry}
                className="flex items-center gap-1 text-xs text-red-700 border border-red-300 rounded-md px-2.5 py-1 hover:bg-red-100 transition-colors flex-shrink-0"
              >
                <RefreshCw className="h-3 w-3" />
                Retry
              </button>
            )}
            <button
              onClick={() => setErrorBanner(null)}
              className="text-red-400 hover:text-red-600 flex-shrink-0"
              aria-label="Dismiss error"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        )}

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-4 py-4" id="messages-container">
          {messages.length === 0 ? (
            /* Welcome / empty state */
            <div className="h-full flex items-center justify-center">
              <div className="text-center max-w-sm px-4">
                <div className="flex justify-center mb-4">
                  <ZenithAvatar size="lg" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">Hi, I'm Zenith</h2>
                <p className="text-gray-500 text-sm mb-6 leading-relaxed">
                  Your AI mental wellness companion — here to listen, support, and guide you 24/7.
                  Everything you share is confidential.
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {suggestionChips.map((chip) => (
                    <button
                      key={chip}
                      onClick={() => handleChipClick(chip)}
                      className="px-4 py-2 rounded-full border border-[#2F7A6D] text-[#2F7A6D] text-sm hover:bg-teal-50 transition-colors font-medium"
                    >
                      {chip}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            /* Message list */
            <div className="max-w-2xl mx-auto space-y-1 pb-2">
              {messages.map((msg) =>
                msg.sender === 'user' ? (
                  /* User bubble */
                  <div key={msg.id} className="flex justify-end mb-4">
                    <div className="flex flex-col items-end max-w-[75%]">
                      <div className="bg-[#2F7A6D] text-white rounded-2xl rounded-tr-sm px-4 py-2.5">
                        <p className="text-sm whitespace-pre-line leading-relaxed">{msg.text}</p>
                      </div>
                      <span className="text-xs text-gray-400 mt-1">
                        {msg.timestamp.toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                  </div>
                ) : (
                  /* AI bubble */
                  <div key={msg.id} className="flex items-end gap-2 mb-4">
                    <ZenithAvatar size="sm" />
                    <div className="flex flex-col items-start max-w-[75%]">
                      <div
                        className={`bg-white border border-gray-100 shadow-sm rounded-2xl rounded-tl-sm px-4 py-2.5 ${getSeverityBorder(msg.severity)}`}
                      >
                        {msg.severity && msg.severity !== 'low' && (
                          <div className="flex items-center gap-1.5 mb-1.5">
                            {getSeverityIcon(msg.severity)}
                            <span className="text-xs font-medium capitalize text-gray-600">
                              {msg.severity} priority
                            </span>
                          </div>
                        )}
                        <p className="text-sm whitespace-pre-line leading-relaxed text-gray-800">
                          {msg.text}
                        </p>
                        {msg.suggestions && msg.suggestions.length > 0 && (
                          <div className="mt-3 pt-2 border-t border-gray-100 flex flex-wrap gap-1.5">
                            {msg.suggestions.map((sug, i) => (
                              <button
                                key={i}
                                onClick={() => setInputText(sug)}
                                className="text-xs px-3 py-1 rounded-full border border-[#2F7A6D]/30 text-[#2F7A6D] hover:bg-teal-50 transition-colors"
                              >
                                {sug}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                      <span className="text-xs text-gray-400 mt-1">
                        {msg.timestamp.toLocaleTimeString([], {
                          hour: '2-digit',
                          minute: '2-digit',
                        })}
                      </span>
                    </div>
                  </div>
                )
              )}

              {/* Typing indicator */}
              {isTyping && <TypingIndicator />}

              {/* Scroll anchor */}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input bar */}
        <div className="bg-white border-t border-gray-100 p-4 flex-shrink-0">
          <div className="max-w-2xl mx-auto flex items-end gap-2">
            <textarea
              ref={textareaRef}
              value={inputText}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder="Type a message… (Enter to send, Shift+Enter for newline)"
              rows={1}
              className="flex-1 resize-none overflow-y-auto rounded-xl border border-gray-200 px-4 py-2.5 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none focus:ring-2 focus:ring-[#2F7A6D]/30 focus:border-[#2F7A6D] transition-colors leading-relaxed"
              style={{ minHeight: '42px', maxHeight: '160px' }}
              disabled={isTyping}
            />
            <button
              onClick={handleSendMessage}
              disabled={!inputText.trim() || isTyping}
              className="p-2.5 rounded-xl bg-[#2F7A6D] text-white hover:bg-[#276860] disabled:opacity-40 disabled:cursor-not-allowed transition-colors flex-shrink-0"
              aria-label="Send message"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
          <p className="text-center text-xs text-gray-400 mt-2">
            Zenith is an AI — not a substitute for professional mental health support.
          </p>
        </div>
      </div>
    </div>
  );
};

export default AIChat;
