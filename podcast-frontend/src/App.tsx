import { useState, useRef, useEffect } from 'react';
import './App.css';

import Header from './components/Header';
import VoiceSetup from './components/VoiceSetup';
import TopicInput from './components/TopicInput';
import AgentProgress, { type LogEvent } from './components/AgentProgress';
import EpisodePlayer from './components/EpisodePlayer';
import SourcesPanel from './components/SourcesPanel';
import AnalystNotes from './components/AnalystNotes';
import ScriptViewer from './components/ScriptViewer';
import ExpertChat from './components/ExpertChat';

const API_BASE = 'http://127.0.0.1:8000';

interface Source {
  title: string;
  uri: string;
  type: string;
}

interface EpisodeData {
  filename: string;
  script: string;
  sources: Source[];
  insights: string;
  research_text: string;
}

export default function App() {
  const [topic, setTopic] = useState('');
  const [hostName, setHostName] = useState('Alex');
  const [guestName, setGuestName] = useState('Sam');

  const [hostRefId, setHostRefId] = useState<string | null>(null);
  const [guestRefId, setGuestRefId] = useState<string | null>(null);
  const [cloningHost, setCloningHost] = useState(false);
  const [cloningGuest, setCloningGuest] = useState(false);

  // Generation State
  const [generating, setGenerating] = useState(false);
  const [logs, setLogs] = useState<LogEvent[]>([]);
  const [activeStage, setActiveStage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Results State
  const [episodeData, setEpisodeData] = useState<EpisodeData | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);

  // Cleanup EventSource on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  async function cloneVoice(
    file: File,
    title: string,
    setBusy: (b: boolean) => void,
    setRefId: (id: string) => void
  ) {
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append('audio', file);
      form.append('title', title);
      const res = await fetch(`${API_BASE}/api/voice/clone`, { method: 'POST', body: form });
      if (!res.ok) throw new Error(`Clone failed (${res.status})`);
      const data = await res.json();
      setRefId(data.reference_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Voice cloning failed');
    } finally {
      setBusy(false);
    }
  }

  function generateEpisode() {
    if (!topic.trim()) {
      setError('Please enter a research topic first.');
      return;
    }

    setGenerating(true);
    setError(null);
    setEpisodeData(null);
    setAudioUrl(null);
    setLogs([]);
    setActiveStage(null);

    // Build query string
    const params = new URLSearchParams();
    params.append('topic', topic);
    params.append('host_name', hostName);
    params.append('guest_name', guestName);
    if (hostRefId) params.append('host_reference_id', hostRefId);
    if (guestRefId) params.append('guest_reference_id', guestRefId);
    params.append('include_music', 'true');

    const url = `${API_BASE}/api/generate-episode/stream?${params.toString()}`;

    // Close any existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const es = new EventSource(url);
    eventSourceRef.current = es;

    setLogs([{ stage: 'system', message: 'Connecting to pipeline...', timestamp: Date.now() / 1000 }]);

    es.addEventListener('progress', (e) => {
      const data = JSON.parse(e.data);
      setLogs(prev => [...prev, data]);
      setActiveStage(data.stage);
    });

    es.addEventListener('complete', (e) => {
      const data = JSON.parse(e.data);
      setLogs(prev => [...prev, data]);
      setActiveStage('done');
      setGenerating(false);
      
      const payload: EpisodeData = data.data;
      setEpisodeData(payload);
      setAudioUrl(`${API_BASE}/api/audio/${payload.filename}`);
      
      es.close();
      eventSourceRef.current = null;
    });

    es.addEventListener('error', (e: any) => {
      // If e.data exists, it's our custom error event
      if (e.data) {
        try {
          const data = JSON.parse(e.data);
          setError(`Pipeline Error: ${data.message}`);
          setLogs(prev => [...prev, data]);
        } catch {
          setError('Pipeline failed.');
        }
      } else {
        // Generic EventSource error (e.g. connection lost)
        setError('Lost connection to backend server.');
      }
      setGenerating(false);
      setActiveStage(null);
      es.close();
      eventSourceRef.current = null;
    });
  }

  return (
    <div className="app">
      <Header />

      {error && (
        <div className="error-banner">
          <span className="label-icon">⚠️</span>
          {error}
        </div>
      )}

      {/* SETUP PHASE: Remains visible so users can review voices and topic */}
      <VoiceSetup 
        hostName={hostName} setHostName={setHostName}
        guestName={guestName} setGuestName={setGuestName}
        onCloneHost={(file) => cloneVoice(file, hostName, setCloningHost, setHostRefId)}
        onCloneGuest={(file) => cloneVoice(file, guestName, setCloningGuest, setGuestRefId)}
        cloningHost={cloningHost} cloningGuest={cloningGuest}
        hostRefId={hostRefId} guestRefId={guestRefId}
      />
      <TopicInput 
        topic={topic} setTopic={setTopic}
        generating={generating} onGenerate={generateEpisode}
      />

      {/* GENERATION / LOGS PHASE: Remains visible once started and stays visible after completion */}
      {(generating || logs.length > 0) && (
        <AgentProgress logs={logs} activeStage={activeStage} />
      )}

      {/* RESULTS PHASE: Shown when stream completes successfully */}
      {episodeData && audioUrl && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-xl)' }}>
          <EpisodePlayer audioUrl={audioUrl} />
          
          <div className="results-grid">
            <SourcesPanel sources={episodeData.sources} />
            <AnalystNotes insights={episodeData.insights} />
          </div>
          
          <div className="results-grid">
            <ScriptViewer script={episodeData.script} />
            <ExpertChat 
              researchText={episodeData.research_text}
              sources={episodeData.sources}
              guestName={guestName}
              apiBase={API_BASE}
            />
          </div>
          
          <div style={{ textAlign: 'center', marginTop: 'var(--space-lg)' }}>
            <button 
              className="btn btn-secondary" 
              onClick={() => {
                setEpisodeData(null);
                setAudioUrl(null);
                setLogs([]);
                setActiveStage(null);
              }}
            >
              Start New Episode
            </button>
          </div>
        </div>
      )}
    </div>
  );
}