import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Heart, MessageCircle, Clock, AlertTriangle, CheckCircle, Shield, Sparkles, Phone } from 'lucide-react';
import api from '@/services/api';

interface Message {
  id: string;
  text: string;
  sender: 'user' | 'ai';
  timestamp: Date;
  severity?: 'low' | 'medium' | 'high' | 'crisis';
  suggestions?: string[];
}

const AIChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const backendWarmed = useRef(false);

  // Pre-warm Render backend on mount (defeats cold start)
  useEffect(() => {
    if (!backendWarmed.current) {
      backendWarmed.current = true;
      const API_BASE_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:5000`;
      fetch(`${API_BASE_URL}/health`, { method: 'GET' }).catch(() => {});
    }
  }, []);

  // Scroll to bottom on new messages
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const messageText = inputText;
    setInputText('');
    setIsTyping(true);

    try {
      const res = await api.post(
        '/chat',
        {
          message: messageText,
          session_id: sessionId,
        },
        { timeout: 45000 }
      );
      const data = res.data;

      // Persist the session_id so subsequent messages maintain context
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

      // Show error in chat UI so the user always sees feedback
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        text: errorText,
        sender: 'ai',
        timestamp: new Date(),
        severity: 'medium',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const getSeverityColor = (severity?: string) => {
    switch (severity) {
      case 'crisis': return 'border-l-red-500 bg-red-50 dark:bg-red-950/30';
      case 'high': return 'border-l-orange-500 bg-orange-50 dark:bg-orange-950/30';
      case 'medium': return 'border-l-yellow-500 bg-yellow-50 dark:bg-yellow-950/30';
      default: return 'border-l-primary bg-primary/5';
    }
  };

  const getSeverityIcon = (severity?: string) => {
    switch (severity) {
      case 'crisis': return <AlertTriangle className="h-4 w-4 text-red-600" />;
      case 'high': return <AlertTriangle className="h-4 w-4 text-orange-600" />;
      case 'medium': return <Clock className="h-4 w-4 text-yellow-600" />;
      default: return null;
    }
  };

  return (
    <div className="min-h-screen bg-[#F7F7F2]">
      <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
        {/* Chat Header */}
        <div className="mb-6 border-2 border-black bg-[#FFE17C] p-5 shadow-[4px_4px_0_#000] sm:p-7">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
            <div>
              <span className="text-xs font-black uppercase tracking-[.18em]">Your support space</span>
              <h1 className="mt-2 text-4xl font-black sm:text-5xl">TALK WITH ZENITH</h1>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary" className="border border-black bg-white text-black"><Sparkles className="mr-1 h-3 w-3" /> AI companion</Badge>
              <Badge variant="outline" className="border border-black bg-[#B7C6C2] text-black"><Shield className="mr-1 h-3 w-3" /> Support, not diagnosis</Badge>
            </div>
          </div>
        </div>

        {/* Chat Card */}
        <Card className="mb-5 overflow-hidden border-2 border-black rounded-[10px] shadow-[8px_8px_0_#000]">
          <CardHeader className="border-b-2 border-black bg-[#171E19] p-4 text-white">
            <div className="flex items-center justify-between">
              <CardTitle className="!text-white">ZENITH / NEW CONVERSATION</CardTitle>
              <Button
                variant="outline"
                size="sm"
                className="border-2 border-white bg-transparent text-white"
                onClick={() => { setMessages([]); setSessionId(null); }}
              >
                Reset
              </Button>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <ScrollArea className="h-96 p-4">
              <div className="space-y-4">
                {messages.length === 0 && (
                  <div className="text-center py-12 text-muted-foreground">
                    <Heart className="h-8 w-8 mx-auto mb-3 text-primary/40" />
                    <p className="text-sm">Say hi to start a conversation.</p>
                    <p className="text-xs mt-1">Everything you share here is confidential.</p>
                  </div>
                )}
                {messages.map((msg) => (
                  <div key={msg.id} className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`max-w-[75%] rounded-2xl px-4 py-3 ${msg.sender === 'user'
                      ? 'border-2 border-black bg-[#FFE17C] text-black rounded-br-md'
                      : `border-l-4 ${getSeverityColor(msg.severity)} rounded-bl-md`}`}>
                      {msg.sender === 'ai' && msg.severity && msg.severity !== 'low' && (
                        <div className="flex items-center space-x-1 mb-1.5">
                          {getSeverityIcon(msg.severity)}
                          <span className="text-xs font-medium capitalize">{msg.severity} priority</span>
                        </div>
                      )}
                      <p className="text-sm whitespace-pre-line leading-relaxed">{msg.text}</p>
                      {msg.sender === 'ai' && msg.suggestions && msg.suggestions.length > 0 && (
                        <div className="mt-3 pt-2 border-t border-border/30 flex flex-wrap gap-1.5">
                          {msg.suggestions.map((sug, i) => (
                            <Button key={i} variant="outline" size="sm" className="text-xs h-7 rounded-full" onClick={() => setInputText(sug)}>
                              {sug}
                            </Button>
                          ))}
                        </div>
                      )}
                      <p className="text-[10px] text-muted-foreground mt-1.5 opacity-60">
                        {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                ))}
                {isTyping && (
                  <div className="flex justify-start items-center space-x-2">
                    <div className="bg-muted rounded-2xl rounded-bl-md px-4 py-3 flex items-center space-x-1.5">
                      <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <span className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>
            </ScrollArea>

            {/* Input */}
            <div className="flex gap-2 border-t-2 border-black p-4 bg-[#F7F7F2]">
              <Input
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Share what is on your mind…"
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
                className="brutal-input"
              />
              <Button className="brutal-button h-12 w-12 p-0" onClick={handleSendMessage} disabled={!inputText.trim() || isTyping} aria-label="Send message">
                <Send className="h-5 w-5" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Crisis Support */}
        <Card className="border-2 border-black bg-white p-5 shadow-[4px_4px_0_#000]">
          <h3 className="mb-2 border-l-4 border-red-600 pl-3 font-black text-red-800">Emergency support</h3>
          <p className="mb-4 text-sm font-medium text-red-800">If you are in immediate danger or having thoughts of self-harm, seek help now.</p>
          <div className="flex flex-wrap gap-2">
            <Button
              variant="destructive"
              className="flex items-center gap-2"
              onClick={() => window.open('tel:14416', '_self')}
            >
              <Phone className="h-4 w-4" /> Call 14416
            </Button>
            <Button
              variant="outline"
              className="flex items-center gap-2"
              onClick={() => window.open('tel:+912227546669', '_self')}
            >
              <MessageCircle className="h-4 w-4" /> Call AASRA
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default AIChat;
