export default function Header() {
  return (
    <header style={{ textAlign: 'center', marginBottom: 'var(--space-2xl)' }}>
      <h1 className="fade-in-up" style={{ marginBottom: 'var(--space-sm)' }}>
        Deep Research <span className="text-accent">Podcaster</span>
      </h1>
      <p className="fade-in-up" style={{ animationDelay: '0.1s', fontSize: '1.1rem' }}>
        AI-generated podcasts from deep research with zero-shot voice cloning.
      </p>
    </header>
  );
}
