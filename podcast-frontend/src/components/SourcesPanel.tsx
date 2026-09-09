interface Source {
  title: string;
  uri: string;
  type: string;
}

interface SourcesPanelProps {
  sources: Source[];
}

export default function SourcesPanel({ sources }: SourcesPanelProps) {
  if (!sources || sources.length === 0) return null;

  return (
    <div className="card h-full">
      <div className="section-label">
        <span className="label-icon">🔗</span>
        Research Sources
      </div>
      
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {sources.map((source, idx) => (
          <li 
            key={idx} 
            style={{ 
              marginBottom: 'var(--space-md)',
              paddingBottom: 'var(--space-md)',
              borderBottom: idx < sources.length - 1 ? '1px solid var(--border-subtle)' : 'none'
            }}
          >
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-sm)' }}>
              <span style={{ 
                color: 'var(--text-muted)', 
                fontFamily: 'var(--font-mono)', 
                fontSize: '0.9rem',
                marginTop: '2px'
              }}>
                {(idx + 1).toString().padStart(2, '0')}.
              </span>
              <div>
                {source.uri && (source.uri.startsWith('http://') || source.uri.startsWith('https://')) ? (
                  <a 
                    href={source.uri} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    style={{ display: 'block', fontWeight: 500, marginBottom: '4px', lineHeight: 1.3, color: 'var(--accent-primary)', textDecoration: 'underline' }}
                  >
                    {source.title} ↗
                  </a>
                ) : (
                  <span style={{ display: 'block', fontWeight: 500, marginBottom: '4px', lineHeight: 1.3 }}>
                    {source.title}
                  </span>
                )}
                <span className="badge badge-web">{source.type ? source.type.toUpperCase() : 'WEB'}</span>
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
