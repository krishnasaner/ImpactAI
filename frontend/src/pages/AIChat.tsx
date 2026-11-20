import React, { useCallback, useEffect, useRef, useState } from 'react';
import { AlertTriangle, ArrowUp, Brain, Menu, Plus, RotateCcw, X } from 'lucide-react';
import api from '@/services/api';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  severity?: 'low' | 'medium' | 'high' | 'crisis';
  suggestions?: string[];
  isError?: boolean;
}

const AIChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastFailedMessage, setLastFailedMessage] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const saved = sessionStorage.getItem('zenith_session_id');
    if (!saved) return;
    setSessionId(saved);
    void api
      .get('/chat/history', { params: { session_id: saved } })
      .then((res) => {
        const records = res.data?.messages || [];
        setMessages(
          records.map((record: {
            id: number;
            sender: 'user' | 'assistant';
            content: string;
            llm_severity?: 'low' | 'medium' | 'high' | 'crisis';
            suggestions?: string[];
            created_at?: string;
          }) => ({
            id: String(record.id),
            text: record.content,
            sender: record.sender === 'assistant' ? 'ai' : 'user',
            timestamp: record.created_at ? new Date(record.created_at) : new Date(),
            severity: record.llm_severity || 'low',
            suggestions: record.suggestions || [],
          }))
        );
      })
      .catch((loadError) => console.error('Failed to load Zenith history:', loadError));
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  const sendMessage = useCallback(async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || typing) return;
    setError(null);
    setLastFailedMessage(null);
    setMessages((current) => [
      ...current,
      { id: `${Date.now()}-user`, text: trimmed, sender: 'user', timestamp: new Date() },
    ]);
    setInput('');
    setTyping(true);

    try {
      const res = await api.post('/chat', { message: trimmed, session_id: sessionId }, { timeout: 45000 });
      const data = res.data;
      if (data.session_id) {
        setSessionId(data.session_id);
        sessionStorage.setItem('zenith_session_id', data.session_id);
      }
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-ai`,
          text: data.text || 'I am here to listen.',
          sender: 'ai',
          timestamp: new Date(),
          severity: data.severity || 'low',
          suggestions: data.suggestions || [],
        },
      ]);
    } catch (requestError) {
      const message =
        requestError instanceof Error
          ? `Unable to reach Zenith: ${requestError.message}`
          : 'Unable to reach Zenith. Please try again.';
      setError(message);
      setLastFailedMessage(trimmed);
      setMessages((current) => [
        ...current,
        { id: `${Date.now()}-error`, text: message, sender: 'ai', timestamp: new Date(), isError: true },
      ]);
    } finally {
      setTyping(false);
    }
  }, [sessionId, typing]);

  const newChat = () => {
    setMessages([]);
    setSessionId(null);
    setError(null);
    setLastFailedMessage(null);
    sessionStorage.removeItem('zenith_session_id');
    setHistoryOpen(false);
  };

  const suggestions = ["I'm feeling anxious", 'Help me relax', 'I need to talk', 'What can you do?'];

  return (
    <main className="grid min-h-[calc(100vh-4rem)] grid-cols-1 bg-[#F7F6F0] lg:grid-cols-[260px_1fr]">
      {historyOpen && (
        <button
          type="button"
          aria-label="Close conversation panel"
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          onClick={() => setHistoryOpen(false)}
        />
      )}
      <aside
        className={`fixed bottom-0 left-0 top-16 z-50 w-[280px] border-r-2 border-black bg-[#171E19] text-white transition-transform lg:static lg:z-auto lg:w-auto lg:translate-x-0 ${
          historyOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex h-full flex-col p-4">
          <div className="flex items-center justify-between border-b-2 border-white/20 pb-4">
            <div className="flex items-center gap-3">
              <div className="flex h-11 w-11 items-center justify-center border-2 border-white bg-[#FFE17C] text-[#171E19]">
                <Brain className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs font-black uppercase tracking-[.14em] text-[#FFE17C]">Your companion</p>
                <p className="font-black">Zenith</p>
              </div>
            </div>
            <button type="button" className="lg:hidden" onClick={() => setHistoryOpen(false)} aria-label="Close">
              <X className="h-5 w-5" />
            </button>
          </div>

          <button type="button" onClick={newChat} className="brutal-button mt-4 inline-flex items-center justify-center gap-2 px-4 py-3">
            <Plus className="h-4 w-4" /> New conversation
          </button>

          <div className="mt-6 flex-1">
            <p className="text-xs font-black uppercase tracking-[.14em] text-[#B7C6C2]">Conversation</p>
            {sessionId ? (
              <div className="mt-3 border-l-4 border-[#FFE17C] bg-white/10 px-3 py-3">
                <p className="text-sm font-bold">Current conversation</p>
                <p className="mt-1 text-xs text-[#B7C6C2]">Restored from this browser session</p>
              </div>
            ) : (
              <p className="mt-3 text-sm leading-relaxed text-[#B7C6C2]">No saved conversation yet.</p>
            )}
          </div>

          <div className="border-t-2 border-white/20 pt-4">
            <p className="text-xs leading-relaxed text-[#B7C6C2]">
              Zenith provides general wellbeing support, not diagnosis or emergency care.
            </p>
            <a href="tel:14416" className="mt-3 block border-2 border-white px-3 py-2 text-center text-sm font-black">
              Crisis line: 14416
            </a>
          </div>
        </div>
      </aside>

      <section className="flex min-h-[calc(100vh-4rem)] min-w-0 flex-col">
        <header className="flex h-16 shrink-0 items-center gap-3 border-b-2 border-black bg-white px-4 sm:px-6">
          <button type="button" className="border-2 border-black p-2 lg:hidden" onClick={() => setHistoryOpen(true)} aria-label="Open conversation panel">
            <Menu className="h-5 w-5" />
          </button>
          <div className="flex h-10 w-10 items-center justify-center border-2 border-black bg-[#FFE17C]">
            <Brain className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h1 className="text-lg leading-tight">Zenith</h1>
            <p className="text-xs text-[#171E19]/60">Emotional wellbeing companion</p>
          </div>
        </header>

        {error && (
          <div className="flex shrink-0 items-center gap-3 border-b-2 border-black bg-[#FFE17C] px-4 py-3">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <p className="min-w-0 flex-1 text-sm">{error}</p>
            {lastFailedMessage && (
              <button type="button" onClick={() => sendMessage(lastFailedMessage)} className="border-2 border-black bg-white p-2" aria-label="Retry">
                <RotateCcw className="h-4 w-4" />
              </button>
            )}
          </div>
        )}

        <div className="flex-1 overflow-y-auto px-4 py-6 sm:px-6">
          {messages.length === 0 ? (
            <div className="mx-auto flex min-h-[420px] max-w-2xl items-center justify-center text-center">
              <div>
                <div className="mx-auto flex h-16 w-16 items-center justify-center border-2 border-black bg-[#B7C6C2] shadow-[4px_4px_0_#000]">
                  <Brain className="h-7 w-7" />
                </div>
                <h2 className="mt-6 text-4xl">Start where you are.</h2>
                <p className="mx-auto mt-3 max-w-md text-sm leading-relaxed text-[#171E19]/70">
                  Share a thought or choose a prompt. This conversation is sent to the configured AI service.
                </p>
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {suggestions.map((suggestion) => (
                    <button
                      type="button"
                      key={suggestion}
                      onClick={() => sendMessage(suggestion)}
                      className="border-2 border-black bg-white px-4 py-2 text-sm font-bold shadow-[3px_3px_0_#000] hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-none"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="mx-auto max-w-3xl space-y-5">
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                  <div
                    className={`max-w-[85%] border-2 border-black px-4 py-3 sm:max-w-[70%] ${
                      message.sender === 'user'
                        ? 'bg-[#FFE17C] shadow-[4px_4px_0_#000]'
                        : message.isError
                          ? 'bg-red-50'
                          : 'bg-white shadow-[4px_4px_0_#000]'
                    }`}
                  >
                    <p className="mb-1 text-[10px] font-black uppercase tracking-[.12em]">
                      {message.sender === 'user' ? 'You' : 'Zenith'}
                    </p>
                    <p className="whitespace-pre-line text-sm leading-relaxed sm:text-base">{message.text}</p>
                    {message.suggestions && message.suggestions.length > 0 && (
                      <div className="mt-3 flex flex-wrap gap-2 border-t-2 border-black/10 pt-3">
                        {message.suggestions.map((suggestion) => (
                          <button
                            type="button"
                            key={suggestion}
                            onClick={() => setInput(suggestion)}
                            className="border-2 border-black bg-[#B7C6C2] px-2 py-1 text-xs font-bold"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              ))}
              {typing && (
                <div className="flex justify-start">
                  <div className="border-2 border-black bg-white px-4 py-3 text-sm font-bold shadow-[4px_4px_0_#000]">
                    Zenith is thinking…
                  </div>
                </div>
              )}
              <div ref={endRef} />
            </div>
          )}
        </div>

        <div className="shrink-0 border-t-2 border-black bg-white p-3 sm:p-4">
          <div className="mx-auto flex max-w-3xl items-end gap-2">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' && !event.shiftKey) {
                  event.preventDefault();
                  void sendMessage(input);
                }
              }}
              rows={1}
              placeholder="Write to Zenith…"
              disabled={typing}
              className="min-h-12 max-h-36 flex-1 resize-none border-2 border-black px-4 py-3 text-sm outline-none focus:ring-4 focus:ring-[#2677ff]/25"
            />
            <button
              type="button"
              onClick={() => void sendMessage(input)}
              disabled={!input.trim() || typing}
              className="brutal-button flex h-12 w-12 items-center justify-center p-0 disabled:cursor-not-allowed disabled:opacity-50"
              aria-label="Send message"
            >
              <ArrowUp className="h-5 w-5" />
            </button>
          </div>
        </div>
      </section>
    </main>
  );
};

export default AIChat;
