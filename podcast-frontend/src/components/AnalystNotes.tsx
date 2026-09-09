import { Fragment } from 'react';

interface AnalystNotesProps {
  insights: string;
}

export default function AnalystNotes({ insights }: AnalystNotesProps) {
  if (!insights) return null;

  // Extremely lightweight custom markdown parser
  // Handles paragraphs, bullet lists (* or -), and bold text (**text**)
  const renderMarkdown = (text: string) => {
    const lines = text.split('\n');
    const elements: React.ReactNode[] = [];
    let currentList: React.ReactNode[] = [];
    let keyCounter = 0;

    const parseBold = (str: string, keyPrefix: string) => {
      const parts = str.split(/(\*\*.*?\*\*)/g);
      return parts.map((part, i) => {
        if (part.startsWith('**') && part.endsWith('**')) {
          return <strong key={`${keyPrefix}-bold-${i}`} style={{ color: 'var(--text-primary)' }}>{part.slice(2, -2)}</strong>;
        }
        return <Fragment key={`${keyPrefix}-text-${i}`}>{part}</Fragment>;
      });
    };

    const flushList = () => {
      if (currentList.length > 0) {
        elements.push(
          <ul key={`ul-${keyCounter++}`} style={{ marginBottom: 'var(--space-md)', paddingLeft: 'var(--space-lg)' }}>
            {[...currentList]}
          </ul>
        );
        currentList = [];
      }
    };

    lines.forEach((line) => {
      const trimmed = line.trim();
      
      // Empty line
      if (!trimmed) {
        flushList();
        return;
      }

      // List item
      if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
        const content = trimmed.substring(2);
        currentList.push(
          <li key={`li-${keyCounter++}`} style={{ marginBottom: '4px' }}>
            {parseBold(content, `li-${keyCounter}`)}
          </li>
        );
      } else {
        // Normal paragraph
        flushList();
        elements.push(
          <p key={`p-${keyCounter++}`} style={{ marginBottom: 'var(--space-md)' }}>
            {parseBold(trimmed, `p-${keyCounter}`)}
          </p>
        );
      }
    });
    
    flushList(); // Flush any remaining list

    return elements;
  };

  return (
    <div className="card h-full">
      <div className="section-label">
        <span className="label-icon">🧠</span>
        Analyst Notes
      </div>
      <div style={{ fontSize: '0.95rem' }}>
        {renderMarkdown(insights)}
      </div>
    </div>
  );
}
