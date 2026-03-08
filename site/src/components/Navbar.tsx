import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

export default function Navbar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const navigate = useNavigate();
  const isHome = location.pathname === '/';

  const scrollToSection = (id: string) => {
    if (isHome) {
      document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
    } else {
      navigate('/');
      setTimeout(() => {
        document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-surface/80 backdrop-blur-md border-b border-border-subtle">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 text-text-primary font-semibold tracking-tight">
          <span className="text-accent font-mono font-bold text-lg">.akf</span>
          <span className="text-sm text-text-secondary hidden sm:inline">Agent Knowledge Format</span>
        </Link>
        <div className="flex items-center gap-6">
          <Link
            to="/"
            className="text-sm text-text-secondary hover:text-text-primary transition-colors hidden sm:inline"
          >
            Home
          </Link>
          <button
            onClick={() => scrollToSection('ai-native')}
            className="text-sm text-text-secondary hover:text-text-primary transition-colors hidden sm:inline"
          >
            Why AKF
          </button>
          <Link
            to="/personas"
            className="text-sm text-text-secondary hover:text-text-primary transition-colors hidden sm:inline"
          >
            Personas
          </Link>
          <Link
            to="/enterprise-report"
            className="text-sm text-text-secondary hover:text-text-primary transition-colors hidden sm:inline"
          >
            Governance Report
          </Link>
          <Link
            to="/convert-to-akf"
            className="text-sm text-text-secondary hover:text-text-primary transition-colors hidden sm:inline"
          >
            Convert to AKF
          </Link>
          <Link
            to="/get-started"
            className="hidden sm:inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-accent hover:bg-accent-hover text-white text-sm font-medium transition-colors"
          >
            Get Started
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
          <Link
            to="/"
            onClick={() => setMenuOpen(false)}
            className="text-sm text-text-secondary hover:text-text-primary transition-colors py-2"
          >
            Home
          </Link>
          <button
            onClick={() => { scrollToSection('ai-native'); setMenuOpen(false); }}
            className="text-sm text-text-secondary hover:text-text-primary transition-colors py-2 text-left"
          >
            Why AKF
          </button>
          <Link
            to="/personas"
            onClick={() => setMenuOpen(false)}
            className="text-sm text-text-secondary hover:text-text-primary transition-colors py-2"
          >
            Personas
          </Link>
          <Link
            to="/validate"
            onClick={() => setMenuOpen(false)}
            className="text-sm text-text-secondary hover:text-text-primary transition-colors py-2"
          >
            Validate & Audit
          </Link>
          <Link
            to="/enterprise-report"
            onClick={() => setMenuOpen(false)}
            className="text-sm text-text-secondary hover:text-text-primary transition-colors py-2"
          >
            Governance Report
          </Link>
          <Link
            to="/akf-vs-md"
            onClick={() => setMenuOpen(false)}
            className="text-sm text-text-secondary hover:text-text-primary transition-colors py-2"
          >
            AKF vs MD
          </Link>
          <Link
            to="/convert-to-akf"
            onClick={() => setMenuOpen(false)}
            className="text-sm text-text-secondary hover:text-text-primary transition-colors py-2"
          >
            Convert to AKF
          </Link>
          <Link
            to="/get-started"
            onClick={() => setMenuOpen(false)}
            className="text-sm font-medium text-accent hover:text-accent-hover transition-colors py-2"
          >
            Get Started
          </Link>
        </div>
      )}
    </nav>
  );
}
