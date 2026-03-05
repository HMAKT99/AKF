import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';

const anchorLinks = [
  { href: '#workflow', label: 'Workflow' },
  { href: '#sdk', label: 'SDK' },
  { href: '#formats', label: 'Formats' },
];

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === '/';

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-surface/80 backdrop-blur-md border-b border-border-subtle">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-text-primary font-semibold tracking-tight">
          <span className="text-accent font-mono font-bold text-lg">.akf</span>
          <span className="text-sm text-text-secondary hidden sm:inline">AI Knowledge Format</span>
        </Link>
        <div className="flex items-center gap-6">
          {anchorLinks.map((link) => (
            <a
              key={link.href}
              href={isHome ? link.href : `/${link.href}`}
              className="text-sm text-text-secondary hover:text-text-primary transition-colors hidden sm:inline"
            >
              {link.label}
            </a>
          ))}
          <Link
            to="/about"
            className="text-sm text-text-secondary hover:text-text-primary transition-colors hidden sm:inline"
          >
            About
          </Link>

          {/* Mobile menu button */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="sm:hidden p-1.5 rounded-md text-text-secondary hover:text-text-primary transition-colors"
            aria-label="Toggle menu"
            aria-expanded={menuOpen}
          >
            {menuOpen ? (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Mobile menu dropdown */}
      {menuOpen && (
        <div className="sm:hidden border-t border-border-subtle bg-surface/95 backdrop-blur-md px-6 py-3 flex flex-col gap-1">
          {anchorLinks.map((link) => (
            <a
              key={link.href}
              href={isHome ? link.href : `/${link.href}`}
              onClick={() => setMenuOpen(false)}
              className="text-sm text-text-secondary hover:text-text-primary transition-colors py-2"
            >
              {link.label}
            </a>
          ))}
          <Link
            to="/about"
            onClick={() => setMenuOpen(false)}
            className="text-sm text-text-secondary hover:text-text-primary transition-colors py-2"
          >
            About
          </Link>
        </div>
      )}
    </nav>
  );
}
