interface ScriptViewerProps {
  script: string;
}

export default function ScriptViewer({ script }: ScriptViewerProps) {
  if (!script) return null;

  return (
    <div className="card fade-in-up" style={{ animationDelay: '0.1s' }}>
      <div className="section-label">
        <span className="label-icon">✍️</span>
        Generated Script
      </div>
      
      <div 
        className="custom-scrollbar"
        style={{ 
          background: 'var(--bg-input)', 
          padding: 'var(--space-lg)', 
          borderRadius: 'var(--radius-md)',
          maxHeight: '400px',
          overflowY: 'auto'
        }}
      >
        {script.split('\n').map((line, idx) => {
          const match = line.match(/^([^:]+):\s*(.+)$/);
          if (match) {
            return (
              <div key={idx} style={{ marginBottom: 'var(--space-md)' }}>
                <strong style={{ color: 'var(--accent-primary)', display: 'block', marginBottom: '2px' }}>
                  {match[1]}
                </strong>
                <span style={{ color: 'var(--text-primary)' }}>
                  {match[2]}
                </span>
              </div>
            );
          }
          // Non-dialogue line (if any)
          if (line.trim()) {
            return <p key={idx} style={{ marginBottom: 'var(--space-sm)' }}>{line}</p>;
          }
          return null;
        })}
      </div>
    </div>
  );
}
