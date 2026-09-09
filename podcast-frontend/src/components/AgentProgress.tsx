import { useEffect, useRef } from 'react';
import './AgentProgress.css';

export interface LogEvent {
  stage: string;
  message: string;
  timestamp: number;
}

interface AgentProgressProps {
  logs: LogEvent[];
  activeStage: string | null;
}

const STAGES = [
  { id: 'Researcher', icon: '🔍' },
  { id: 'Analyst', icon: '🧠' },
  { id: 'Scriptwriter', icon: '✍️' },
  { id: 'Audio Director', icon: '🎬' },
  { id: 'Audio Engineer', icon: '🎛️' },
];

export default function AgentProgress({ logs, activeStage }: AgentProgressProps) {
  const terminalRef = useRef<HTMLDivElement>(null);

  // Auto-scroll terminal to bottom when new logs arrive
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  function formatTime(ts: number) {
    const d = new Date(ts * 1000);
    return d.toISOString().substring(11, 19); // HH:MM:SS
  }

  function getStageClass(stage: string) {
    return stage.toLowerCase().replace(' ', '-');
  }

  // Determine stage status
  function getStageStatus(stageId: string) {
    const stageIndex = STAGES.findIndex(s => s.id === stageId);
    const activeIndex = STAGES.findIndex(s => s.id === activeStage);
    
    if (activeStage === 'done' || (activeIndex > -1 && stageIndex < activeIndex)) {
      return 'done';
    }
    if (stageId === activeStage) {
      return 'active';
    }
    return 'pending';
  }

  return (
    <div className="card fade-in-up agent-progress-container">
      <div className="section-label">
        <span className="badge badge-number">⚡</span>
        Live Generation Pipeline
      </div>

      <div className="stages-grid">
        {STAGES.map(stage => {
          const status = getStageStatus(stage.id);
          return (
            <div key={stage.id} className={`agent-card ${status}`}>
              <span className="icon">{stage.icon}</span>
              <div className="name">{stage.id}</div>
              <div className="status">
                {status === 'active' ? 'Working...' : status === 'done' ? 'Complete' : 'Waiting'}
              </div>
            </div>
          );
        })}
      </div>

      <div className="terminal-card custom-scrollbar" ref={terminalRef}>
        {logs.length === 0 ? (
          <div className="text-muted">Waiting for pipeline to start...</div>
        ) : (
          logs.map((log, idx) => (
            <div key={idx} className="log-line fade-in-up">
              <span className="log-timestamp">[{formatTime(log.timestamp)}]</span>
              {log.stage !== 'system' && log.stage !== 'done' && (
                <span className={`log-stage ${getStageClass(log.stage)}`}>
                  [{log.stage}]
                </span>
              )}
              <span style={{ color: log.stage === 'error' ? 'var(--error)' : 'inherit' }}>
                {log.message}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
