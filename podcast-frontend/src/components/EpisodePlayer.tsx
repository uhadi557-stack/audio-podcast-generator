interface EpisodePlayerProps {
  audioUrl: string;
}

export default function EpisodePlayer({ audioUrl }: EpisodePlayerProps) {
  return (
    <div className="card fade-in-up" style={{ textAlign: 'center' }}>
      <div className="section-label" style={{ justifyContent: 'center' }}>
        <span className="badge badge-success">✓</span>
        Episode Ready
      </div>
      
      <audio 
        controls 
        src={audioUrl} 
        style={{ width: '100%', marginBottom: 'var(--space-md)' }} 
        autoPlay
      />
      
      <a 
        href={audioUrl} 
        download 
        className="btn btn-secondary"
        style={{ textDecoration: 'none' }}
      >
        ↓ Download Audio (.wav)
      </a>
    </div>
  );
}
