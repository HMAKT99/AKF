import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="border-t border-border-subtle py-12 px-6">
      <div className="max-w-6xl mx-auto flex flex-col gap-6">
        <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
          <Link to="/validate" className="text-sm text-text-tertiary hover:text-text-primary transition-colors">Validate & Audit</Link>
          <Link to="/certify" className="text-sm text-text-tertiary hover:text-text-primary transition-colors">Certify</Link>
          <Link to="/akf-vs-md" className="text-sm text-text-tertiary hover:text-text-primary transition-colors">AKF vs MD</Link>
          <Link to="/about" className="text-sm text-text-tertiary hover:text-text-primary transition-colors">About</Link>
        </div>
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <span className="text-accent font-mono font-bold">.akf</span>
            <span className="text-sm text-text-tertiary">MIT License</span>
          </div>
          <p className="text-sm text-text-tertiary">Built for the AI era.</p>
        </div>
      </div>
    </footer>
  );
}
