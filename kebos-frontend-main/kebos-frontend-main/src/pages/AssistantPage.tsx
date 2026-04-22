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
    <div className="p-6 h-full flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold text-black mb-2">AI Security Assistant</h1>
          <p className="text-black">AI-powered threat analysis and security guidance</p>
        </div>
        <div className="flex space-x-2">
          <button className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium">
            Export Chat
          </button>
          <button className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium">
            Clear History
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 h-full">
        {/* Chat Interface */}
        <div className="lg:col-span-3 bg-background-secondary rounded-lg border border-border flex flex-col">
          {/* Chat Header */}
          <div className="p-4 border-b border-border">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-primary rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-black">AI Security Assistant</h3>
                  <p className="text-sm text-black opacity-70">Online • Ready to assist</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-3 h-3 bg-success rounded-full"></span>
                <span className="text-sm text-text-secondary">Connected</span>
              </div>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                    message.sender === 'user'
                      ? 'bg-primary text-white'
                      : `bg-background-primary text-text-primary ${
                          message.type === 'threat-narrative' ? 'border-l-4 border-error' :
                          message.type === 'analysis' ? 'border-l-4 border-warning' : ''
                        }`
                  }`}
                >
                  <p className="text-sm">{message.content}</p>
                  <p className={`text-xs mt-1 ${
                    message.sender === 'user' ? 'text-blue-100' : 'text-text-secondary'
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
          <div className="p-4 border-t border-border">
            <div className="flex space-x-2">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Ask about threats, request analysis, or get security guidance..."
                className="flex-1 px-3 py-2 border border-border rounded-lg bg-background-primary text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
                rows={1}
                disabled={isLoading}
              />
              <button
                onClick={handleSendMessage}
                disabled={isLoading || !inputValue.trim()}
                className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Send
              </button>
            </div>
            <div className="flex items-center justify-between mt-2 text-xs text-text-secondary">
              <span>Press Enter to send, Shift+Enter for new line</span>
              <span>{inputValue.length}/500</span>
            </div>
          </div>
        </div>

        {/* Assistant Stats & Quick Actions */}
        <div className="space-y-6">
          {/* Performance Stats */}
          <div className="bg-background-secondary rounded-lg p-6 border border-border">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Assistant Performance</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-text-secondary">Total Queries</span>
                  <span className="text-sm font-medium text-text-primary">{stats.totalQueries}</span>
                </div>
              </div>
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-text-secondary">Avg Response Time</span>
                  <span className="text-sm font-medium text-text-primary">{stats.averageResponseTime}s</span>
                </div>
              </div>
              <div>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-sm text-text-secondary">Satisfaction Score</span>
                  <span className="text-sm font-medium text-success">{stats.satisfactionScore}/5.0</span>
                </div>
              </div>
            </div>
          </div>

          {/* Query Types */}
          <div className="bg-background-secondary rounded-lg p-6 border border-border">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Query Distribution</h3>
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">Threat Analysis</span>
                <span className="text-sm font-medium text-text-primary">{stats.queryTypes.threats}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">Security Analysis</span>
                <span className="text-sm font-medium text-text-primary">{stats.queryTypes.analysis}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-text-secondary">General Queries</span>
                <span className="text-sm font-medium text-text-primary">{stats.queryTypes.general}</span>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="bg-background-secondary rounded-lg p-6 border border-border">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Quick Actions</h3>
            <div className="space-y-3">
              <button className="w-full bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium text-sm">
                Generate Threat Report
              </button>
              <button className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium">
                Security Assessment
              </button>
              <button className="bg-primary hover:bg-primary-dark text-white px-4 py-2 rounded-lg font-medium">
                Incident Analysis
              </button>
            </div>
          </div>

          {/* Recent Topics */}
          <div className="bg-background-secondary rounded-lg p-6 border border-border">
            <h3 className="text-lg font-semibold text-text-primary mb-4">Recent Topics</h3>
            <div className="space-y-2">
              <div className="text-xs bg-background-primary px-2 py-1 rounded text-text-primary">
                Network anomaly detection
              </div>
              <div className="text-xs bg-background-primary px-2 py-1 rounded text-text-primary">
                Phishing campaign analysis
              </div>
              <div className="text-xs bg-background-primary px-2 py-1 rounded text-text-primary">
                Incident response planning
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
