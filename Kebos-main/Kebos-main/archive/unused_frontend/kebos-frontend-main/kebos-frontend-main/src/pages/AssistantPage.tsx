import React, { useState, useEffect, useRef } from 'react';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'assistant';
  timestamp: Date;
  type?: 'text' | 'threat-narrative' | 'analysis';
}

interface AssistantStats {
  totalQueries: number;
  averageResponseTime: number;
  satisfactionScore: number;
  queryTypes: {
    threats: number;
    analysis: number;
    general: number;
  };
}

export function AssistantPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [stats, _setStats] = useState<AssistantStats>({
    totalQueries: 1247,
    averageResponseTime: 1.8,
    satisfactionScore: 4.7,
    queryTypes: {
      threats: 523,
      analysis: 389,
      general: 335
    }
  });
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Initialize with welcome message
    setMessages([
      {
        id: '1',
        content: 'Hello! I\'m your AI security assistant. I can help you with threat analysis, generate security narratives, and answer questions about your cybersecurity posture. How can I assist you today?',
        sender: 'assistant',
        timestamp: new Date(),
        type: 'text'
      }
    ]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      sender: 'user',
      timestamp: new Date(),
      type: 'text'
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    // Simulate AI response
    setTimeout(() => {
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: getSimulatedResponse(inputValue),
        sender: 'assistant',
        timestamp: new Date(),
        type: getResponseType(inputValue)
      };

      setMessages(prev => [...prev, assistantMessage]);
      setIsLoading(false);
    }, 1500);
  };

  const getSimulatedResponse = (query: string): string => {
    if (query.toLowerCase().includes('threat')) {
      return 'Based on current network analysis, I\'ve detected several potential threats in your environment. The most critical appears to be suspicious network traffic from IP 192.168.1.105, which shows patterns consistent with data exfiltration attempts. I recommend immediate investigation and potential isolation of the affected system.';
    }
    if (query.toLowerCase().includes('narrative')) {
      return 'I\'ve generated a comprehensive threat narrative for the recent security incident. The attack appears to have originated from a phishing email that bypassed initial filters, leading to credential compromise and lateral movement through the network. The attacker maintained persistence for approximately 72 hours before detection.';
    }
    return 'I understand your query. Based on the current security posture and available data, I recommend reviewing the latest threat intelligence feeds and ensuring all security controls are properly configured. Would you like me to provide more specific guidance on any particular area?';
  };

  const getResponseType = (query: string): 'text' | 'threat-narrative' | 'analysis' => {
    if (query.toLowerCase().includes('narrative')) return 'threat-narrative';
    if (query.toLowerCase().includes('analysis') || query.toLowerCase().includes('threat')) return 'analysis';
    return 'text';
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-sm border-b border-slate-200/50 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-600 rounded-lg shadow-lg">
              <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <div>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
                AI Security Assistant
              </h1>
              <p className="text-slate-600">AI-powered threat analysis and security guidance</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        {/* Quick Actions */}
        <div className="flex justify-end space-x-4">
          <button className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-200">
            Export Chat
          </button>
          <button className="px-6 py-3 bg-red-400 backdrop-blur-sm text-white rounded-lg font-medium border border-slate-200 hover:shadow-lg transition-all duration-200">
            Clear History
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6 hover:shadow-2xl transition-all duration-200">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-3xl font-bold text-indigo-600">{stats.totalQueries}</p>
                <p className="text-slate-600 text-sm font-medium">Total Queries</p>
              </div>
              <div className="p-3 bg-indigo-100 rounded-xl">
                <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
            </div>
          </div>
          
          {/* Add similar styled cards for other stats */}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Chat Interface */}
          <div className="lg:col-span-3">
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 overflow-hidden">
              {/* Messages Container */}
              <div className="h-[600px] flex flex-col">
                <div className="flex-1 overflow-y-auto p-6 space-y-4">
                  {messages.map((message) => (
                    <div key={message.id} className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div className={`max-w-xs lg:max-w-md rounded-2xl px-6 py-4 ${
                        message.sender === 'user'
                          ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                          : 'bg-white/90 border border-slate-200'
                      }`}>
                        <p className={message.sender === 'user' ? 'text-white' : 'text-slate-700'}>
                          {message.content}
                        </p>
                        <p className={`text-xs mt-2 ${
                          message.sender === 'user' ? 'text-indigo-100' : 'text-slate-400'
                        }`}>
                          {message.timestamp.toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))}
                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-background-primary text-text-primary px-4 py-2 rounded-lg">
                        <div className="flex items-center space-x-2">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-primary rounded-full animate-bounce"></div>
                            <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                            <div className="w-2 h-2 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                          </div>
                          <span className="text-sm">Assistant is typing...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="p-6 border-t border-slate-200 bg-white/50">
                  <div className="flex space-x-4">
                    <textarea
                      value={inputValue}
                      onChange={(e) => setInputValue(e.target.value)}
                      onKeyPress={handleKeyPress}
                      placeholder="Ask about threats, request analysis, or get security guidance..."
                      className="flex-1 px-4 py-3 bg-white border border-slate-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-shadow resize-none"
                      rows={1}
                    />
                    <button
                      onClick={handleSendMessage}
                      disabled={isLoading || !inputValue.trim()}
                      className="px-6 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-xl font-medium shadow-lg hover:shadow-xl transition-all duration-200 "
                    >
                      Send
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Quick Actions Panel */}
            <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-white/50 p-6">
              <h3 className="text-lg font-semibold text-slate-800 mb-4">Quick Actions</h3>
              <div className="space-y-3">
                <button className="w-full px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-700 hover:to-purple-700 text-white rounded-lg font-medium shadow-lg hover:shadow-xl transition-all duration-200">
                  Generate Report
                </button>
                <button className="w-full px-4 py-2 bg-secondary hover:bg-secondary-dark hover:text-text-secondary rounded-lg font-medium border border-border">
                  Security Assessment
                </button>
                <button className="w-full px-4 py-2 bg-secondary hover:bg-secondary-dark hover:text-text-secondary rounded-lg font-medium border border-border">
                  Incident Analysis
                </button>
              </div>
            </div>

            {/* Other sidebar panels with same styling */}
          </div>
        </div>
      </div>
    </div>
  );
}