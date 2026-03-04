export default function Footer() {
  return (
    <footer className="border-t border-border-subtle py-12 px-6">
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <span className="text-accent font-mono font-bold">.akf</span>
          <span className="text-sm text-text-tertiary">MIT License</span>
        </div>
        <p className="text-sm text-text-tertiary">Built for the AI era.</p>
        <a
          href="https://github.com/HMAKT99/AKF"
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm text-text-secondary hover:text-text-primary transition-colors"
        >
          github.com/HMAKT99/AKF
        </a>
      </div>
    </footer>
  );
}
