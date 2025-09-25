import React, { useState } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = {
      id: Date.now(),
      role: 'user',
      content: input.trim()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('http://localhost:8002/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ prompt: input.trim() })
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullResponse = '';

      const assistantMessage = {
        id: Date.now() + 1,
        role: 'assistant',
        content: ''
      };

      setMessages(prev => [...prev, assistantMessage]);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        fullResponse += chunk;

        setMessages(prev => 
          prev.map(msg => 
            msg.id === assistantMessage.id 
              ? { ...msg, content: fullResponse }
              : msg
          )
        );
      }
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'מצטער, אירעה שגיאה. אנא נסה שוב.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>🤖 עוזר ארגוני חכם</h1>
        <p>בינה מלאכותית לעסקים</p>
      </header>

      <div className="chat-container">
        <div className="messages">
          {messages.length === 0 ? (
            <div className="welcome">
              <h2>ברוכים הבאים!</h2>
              <p>שאלו אותי על:</p>
              <ul>
                <li>💡 פיתוח מוצרים</li>
                <li>📈 שיווק דיגיטלי</li>
                <li>👥 ניהול צוותים</li>
                <li>🤖 טכנולוגיה</li>
              </ul>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className={`message ${message.role}`}>
                <div className="message-content">
                  {message.content}
                </div>
              </div>
            ))
          )}
          {loading && (
            <div className="message assistant">
              <div className="message-content loading">
                העוזר כותב...
              </div>
            </div>
          )}
        </div>

        <div className="input-container">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="כתבו את השאלה שלכם כאן..."
            disabled={loading}
          />
          <button 
            onClick={sendMessage}
            disabled={!input.trim() || loading}
            className="send-button"
          >
            {loading ? '...' : 'שלח'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default App;
