import React, { useState, useEffect, useRef } from 'react';
import './App.css';

interface Message {
  id: string;
  content: string;
  sender: 'user' | 'ai';
  timestamp: string;
  confidence?: number;
  sources?: any[];
  tokensUsed?: number;
}

interface ChatResponse {
  response: string;
  session_id: string;
  timestamp: string;
  user_id: string;
  sources?: any[];
  confidence?: number;
  tokens_used?: number;
}

const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [userId] = useState(`user_${Math.random().toString(36).substr(2, 9)}`);
  const [isConnected, setIsConnected] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const API_BASE = 'http://localhost:8000';

  useEffect(() => {
    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const checkConnection = async () => {
    try {
      const response = await fetch(`${API_BASE}/health`);
      setIsConnected(response.ok);
    } catch (error) {
      setIsConnected(false);
    }
  };

  const addMessage = (content: string, sender: 'user' | 'ai', timestamp?: string, confidence?: number, sources?: any[], tokensUsed?: number) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      content,
      sender,
      timestamp: timestamp || new Date().toISOString(),
      confidence,
      sources,
      tokensUsed
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const sendMessage = async () => {
    if (!inputMessage.trim() || !isConnected) return;

    const message = inputMessage.trim();
    setInputMessage('');
    addMessage(message, 'user');
    setIsLoading(true);

    try {
      const requestData = {
        message,
        user_id: userId,
        ...(sessionId && { session_id: sessionId })
      };

      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      if (response.ok) {
        const data: ChatResponse = await response.json();
        setSessionId(data.session_id);
        
        // Add AI response with delay for better UX
        setTimeout(() => {
          addMessage(
            data.response,
            'ai',
            data.timestamp,
            data.confidence,
            data.sources,
            data.tokens_used
          );
          setIsLoading(false);
        }, 1000);
      } else {
        throw new Error(`Server error: ${response.status}`);
      }
    } catch (error) {
      console.error('Error:', error);
      addMessage(`מצטער, אירעה שגיאה: ${error instanceof Error ? error.message : 'Unknown error'}. אנא נסה שוב.`, 'ai');
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      <div className="chat-container">
        <div className="header">
          <div className="status-indicator" style={{ backgroundColor: isConnected ? '#4CAF50' : '#f44336' }}></div>
          <h1>🚀 Enterprise AI Assistant</h1>
          <p>מערכת בינה מלאכותית מתקדמת לניהול ופיתוח עסקי</p>
        </div>

        <div className="messages-container">
          {messages.length === 0 && (
            <div className="welcome-message">
              <h2>ברוכים הבאים למערכת הבינה המלאכותית המתקדמת!</h2>
              <p>מערכת AI חכמה ומקצועית לניהול עסקי, פיתוח אסטרטגיות וקבלת החלטות</p>
              
              <div className="features">
                <div className="feature">
                  <div className="feature-icon">🎯</div>
                  <h3>ניהול אסטרטגי</h3>
                  <p>פיתוח אסטרטגיות עסקיות מתקדמות</p>
                </div>
                <div className="feature">
                  <div className="feature-icon">👥</div>
                  <h3>ניהול צוותים</h3>
                  <p>הדרכה מקצועית לניהול יעיל</p>
                </div>
                <div className="feature">
                  <div className="feature-icon">📈</div>
                  <h3>פיתוח עסקי</h3>
                  <p>אסטרטגיות צמיחה והתרחבות</p>
                </div>
                <div className="feature">
                  <div className="feature-icon">🚀</div>
                  <h3>טכנולוגיה מתקדמת</h3>
                  <p>אוטומציה וחדשנות טכנולוגית</p>
                </div>
              </div>
            </div>
          )}

          {messages.map((message) => (
            <div key={message.id} className={`message ${message.sender}`}>
              <div className="message-bubble">
                <div className="message-content">{message.content}</div>
                <div className="message-time">
                  {new Date(message.timestamp).toLocaleTimeString('he-IL')}
                </div>
                {message.confidence && message.sender === 'ai' && (
                  <div className="confidence">
                    ביטחון: {(message.confidence * 100).toFixed(1)}%
                  </div>
                )}
                {message.sources && message.sources.length > 0 && message.sender === 'ai' && (
                  <div className="sources">
                    <strong>מקורות רלוונטיים:</strong><br />
                    {message.sources.map((source, index) => (
                      <div key={index}>• {source.message || 'מקור קודם'}</div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="message ai">
              <div className="message-bubble">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
                <span>העוזר החכם כותב...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div className="input-container">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="כתבו את השאלה שלכם כאן..."
            className="message-input"
            disabled={!isConnected}
          />
          <button
            onClick={sendMessage}
            disabled={!inputMessage.trim() || !isConnected || isLoading}
            className="send-button"
          >
            שלח
          </button>
        </div>
      </div>
    </div>
  );
};

export default App;
