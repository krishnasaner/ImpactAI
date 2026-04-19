import React, { useState, useEffect, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Send, Heart, MessageCircle, Clock, AlertTriangle, CheckCircle, Shield, Sparkles, Phone } from 'lucide-react';
import { toast } from 'react-toastify';

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
      const API_BASE_URL = import.meta.env.VITE_API_URL || `http://${window.location.hostname}:5000`;
      const token = sessionStorage.getItem('token') || localStorage.getItem('token');
      const res = await fetch(`${API_BASE_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          message: messageText,
          session_id: sessionId,
        }),
        credentials: 'include',
      });

      if (!res.ok) {
        const payload = await res.json().catch(() => null);
        throw new Error(payload?.detail || 'AI service request failed.');
      }

      const data = await res.json();

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
      console.error(error);
      toast.error('Unable to connect to the AI backend. Please try again later.');
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
    <div className="min-h-screen bg-gradient-mesh">
      <div className="container mx-auto px-4 py-6 max-w-5xl">
        {/* Chat Header */}
        <div className="text-center mb-6">
          <h1 className="text-3xl font-bold mb-2">ImpactAI Support</h1>
          <p className="text-muted-foreground">
            Your personal mental health companion — confidential and available 24/7.
          </p>
          <div className="flex justify-center gap-2 mt-2">
            <Badge variant="secondary" className="flex items-center gap-1"><Sparkles className="h-3 w-3" /> AI-Powered</Badge>
            <Badge variant="outline" className="flex items-center gap-1"><Shield className="h-3 w-3" /> Confidential</Badge>
            <Badge variant="outline" className="flex items-center gap-1"><CheckCircle className="h-3 w-3" /> Crisis Detection</Badge>
          </div>
        </div>

        {/* Chat Card */}
        <Card className="mb-4">
          <CardHeader className="bg-gradient-to-r from-background to-background/80 p-4">
            <CardTitle>ImpactAI Chat</CardTitle>
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
                      ? 'bg-primary text-primary-foreground rounded-br-md'
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
            <div className="flex space-x-2 p-4 border-t border-border/40">
              <Input
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                placeholder="Type a message..."
                onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              />
              <Button onClick={handleSendMessage} disabled={!inputText.trim() || isTyping}>
                <Send className="h-4 w-4" />
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Crisis Support */}
        <Card className="bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800 p-4">
          <h3 className="font-bold text-red-800 dark:text-red-300 mb-2">Emergency Support</h3>
          <p className="text-red-700 dark:text-red-400 text-sm mb-4">
            If you are in crisis or having thoughts of self-harm, seek help immediately.
          </p>
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
