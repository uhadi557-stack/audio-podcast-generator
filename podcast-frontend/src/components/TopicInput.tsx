interface TopicInputProps {
  topic: string;
  setTopic: (t: string) => void;
  onGenerate: () => void;
  generating: boolean;
}

export default function TopicInput({ topic, setTopic, onGenerate, generating }: TopicInputProps) {
  return (
    <div className="card fade-in-up" style={{ animationDelay: '0.4s' }}>
      <div className="section-label">
        <span className="badge badge-number">3</span>
        Research Topic
      </div>
      
      <div style={{ display: 'flex', gap: 'var(--space-md)', alignItems: 'center' }}>
        <input 
          type="text" 
          className="input" 
          value={topic}
          onChange={e => setTopic(e.target.value)}
          placeholder="e.g. The history and impact of quantum computing..."
          disabled={generating}
          onKeyDown={e => {
            if (e.key === 'Enter' && topic.trim() && !generating) {
              onGenerate();
            }
          }}
        />
        <button 
          className="btn btn-primary"
          style={{ whiteSpace: 'nowrap' }}
          disabled={!topic.trim() || generating}
          onClick={onGenerate}
        >
          {generating ? 'Generating...' : 'Start Podcast Generation'}
        </button>
      </div>
    </div>
  );
}
