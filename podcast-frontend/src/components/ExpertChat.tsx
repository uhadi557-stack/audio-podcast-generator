import { useState, useRef, useEffect } from 'react';
import './ExpertChat.css';

interface Source {
  title: string;
  uri: string;
  type: string;
}

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

interface ExpertChatProps {
  researchText: string;
  sources: Source[];
  guestName: string;
  apiBase: string;
}

export default function ExpertChat({ researchText, sources, guestName, apiBase }: ExpertChatProps) {
  const [history, setHistory] = useState<ChatMessage[]>([]);
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const historyRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (historyRef.current) {
      historyRef.current.scrollTop = historyRef.current.scrollHeight;
    }
  }, [history, loading]);

  async function handleSend() {
    if (!question.trim() || loading) return;

    const userMsg: ChatMessage = { role: 'user', content: question.trim() };
    const newHistory = [...history, userMsg];
    
    setHistory(newHistory);
    setQuestion('');
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${apiBase}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          research_text: researchText,
          sources: sources,
          question: userMsg.content,
          history: history, // send previous history (without the current question, backend takes question separately)
          guest_name: guestName,
        }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.message || `Chat failed (${res.status})`);
      }

      const data = await res.json();
      setHistory([...newHistory, { role: 'assistant', content: data.answer }]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Chat failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card fade-in-up" style={{ animationDelay: '0.2s' }}>
      <div className="section-label">
        <span className="label-icon">💬</span>
        Expert Follow-up
      </div>
      
      <p style={{ marginBottom: 'var(--space-md)' }}>
        Ask <strong>{guestName}</strong> follow-up questions about this topic.
      </p>

      <div className="chat-container">
        <div className="chat-history custom-scrollbar" ref={historyRef}>
          {history.length === 0 && !loading && (
            <div style={{ margin: 'auto', color: 'var(--text-muted)', fontStyle: 'italic' }}>
              No messages yet. Ask a question!
            </div>
          )}
          
          {history.map((msg, idx) => (
            <div key={idx} className={`chat-bubble ${msg.role}`}>
              <div className="chat-bubble-name">
                {msg.role === 'user' ? 'You' : guestName}
              </div>
              <div>{msg.content}</div>
            </div>
          ))}

          {loading && (
            <div className="chat-bubble assistant">
              <div className="chat-bubble-name">{guestName}</div>
              <div style={{ display: 'flex', alignItems: 'center', height: '24px' }}>
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
                <span className="typing-dot"></span>
              </div>
            </div>
          )}
        </div>

        {error && (
          <div style={{ color: 'var(--error)', fontSize: '0.85rem', marginBottom: '8px' }}>
            {error}
          </div>
        )}

        <div className="chat-input-area">
          <input 
            type="text" 
            className="input" 
            placeholder={`Ask ${guestName}...`}
            value={question}
            onChange={e => setQuestion(e.target.value)}
            onKeyDown={e => {
              if (e.key === 'Enter') handleSend();
            }}
            disabled={loading}
          />
          <button 
            className="btn btn-primary"
            onClick={handleSend}
            disabled={!question.trim() || loading}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
