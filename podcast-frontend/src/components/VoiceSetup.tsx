import { useState } from 'react';

interface VoiceSetupProps {
  hostName: string;
  setHostName: (name: string) => void;
  guestName: string;
  setGuestName: (name: string) => void;
  onCloneHost: (file: File) => Promise<void>;
  onCloneGuest: (file: File) => Promise<void>;
  cloningHost: boolean;
  cloningGuest: boolean;
  hostRefId: string | null;
  guestRefId: string | null;
}

export default function VoiceSetup({
  hostName,
  setHostName,
  guestName,
  setGuestName,
  onCloneHost,
  onCloneGuest,
  cloningHost,
  cloningGuest,
  hostRefId,
  guestRefId,
}: VoiceSetupProps) {
  const [hostFile, setHostFile] = useState<File | null>(null);
  const [guestFile, setGuestFile] = useState<File | null>(null);

  return (
    <div className="setup-section">
      <div className="card fade-in-up" style={{ animationDelay: '0.2s' }}>
        <div className="section-label">
          <span className="badge badge-number">1</span>
          Host Settings
        </div>
        
        <div style={{ marginBottom: 'var(--space-md)' }}>
          <label style={{ display: 'block', marginBottom: 'var(--space-xs)', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Host Name</label>
          <input 
            type="text" 
            className="input" 
            value={hostName} 
            onChange={e => setHostName(e.target.value)} 
          />
        </div>

        <div style={{ marginBottom: 'var(--space-md)' }}>
          <label style={{ display: 'block', marginBottom: 'var(--space-xs)', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Voice Sample (10-30s clean audio)</label>
          <label className={`file-input-label ${hostFile ? 'has-file' : ''}`}>
            <span style={{ fontSize: '1.2rem' }}>🎤</span>
            {hostFile ? hostFile.name : 'Choose audio file...'}
            <input 
              type="file" 
              accept="audio/*" 
              className="sr-only" 
              onChange={e => setHostFile(e.target.files?.[0] || null)}
            />
          </label>
        </div>

        <button 
          className="btn btn-secondary" 
          style={{ width: '100%' }}
          disabled={!hostFile || cloningHost}
          onClick={() => hostFile && onCloneHost(hostFile)}
        >
          {cloningHost ? (
            <><span className="spinner"></span> Cloning...</>
          ) : hostRefId ? (
            <span className="text-success">✓ Voice Cloned</span>
          ) : (
            'Clone Host Voice'
          )}
        </button>
      </div>

      <div className="card fade-in-up" style={{ animationDelay: '0.3s' }}>
        <div className="section-label">
          <span className="badge badge-number">2</span>
          Guest Settings
        </div>
        
        <div style={{ marginBottom: 'var(--space-md)' }}>
          <label style={{ display: 'block', marginBottom: 'var(--space-xs)', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Guest Name</label>
          <input 
            type="text" 
            className="input" 
            value={guestName} 
            onChange={e => setGuestName(e.target.value)} 
          />
        </div>

        <div style={{ marginBottom: 'var(--space-md)' }}>
          <label style={{ display: 'block', marginBottom: 'var(--space-xs)', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Voice Sample (10-30s clean audio)</label>
          <label className={`file-input-label ${guestFile ? 'has-file' : ''}`}>
            <span style={{ fontSize: '1.2rem' }}>🎤</span>
            {guestFile ? guestFile.name : 'Choose audio file...'}
            <input 
              type="file" 
              accept="audio/*" 
              className="sr-only" 
              onChange={e => setGuestFile(e.target.files?.[0] || null)}
            />
          </label>
        </div>

        <button 
          className="btn btn-secondary" 
          style={{ width: '100%' }}
          disabled={!guestFile || cloningGuest}
          onClick={() => guestFile && onCloneGuest(guestFile)}
        >
          {cloningGuest ? (
            <><span className="spinner"></span> Cloning...</>
          ) : guestRefId ? (
            <span className="text-success">✓ Voice Cloned</span>
          ) : (
            'Clone Guest Voice'
          )}
        </button>
      </div>
    </div>
  );
}
