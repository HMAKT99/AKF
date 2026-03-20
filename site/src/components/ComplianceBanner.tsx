import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

const TARGET = new Date('2026-08-02T00:00:00Z').getTime();
const BANNER_HEIGHT = 36; // h-9 = 2.25rem = 36px

export function useBannerVisible() {
  const [dismissed, setDismissed] = useState(false);
  const visible = !dismissed && Date.now() < TARGET;
  return { visible, dismiss: () => setDismissed(true), height: visible ? BANNER_HEIGHT : 0 };
}

export default function ComplianceBanner({
  onDismiss,
}: {
  onDismiss: () => void;
}) {
  const [now, setNow] = useState(Date.now());
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);

  if (TARGET - now <= 0) return null;

  const diff = TARGET - now;
  const days = Math.floor(diff / 86_400_000);
  const hours = Math.floor((diff % 86_400_000) / 3_600_000);
  const mins = Math.floor((diff % 3_600_000) / 60_000);
  const secs = Math.floor((diff % 60_000) / 1000);

  const handleClick = () => {
    if (location.pathname === '/') {
      document.getElementById('compliance')?.scrollIntoView({ behavior: 'smooth' });
    } else {
      navigate('/');
      setTimeout(() => {
        document.getElementById('compliance')?.scrollIntoView({ behavior: 'smooth' });
      }, 100);
    }
  };

  return (
    <div className="fixed top-0 left-0 right-0 z-[60] bg-gradient-to-r from-amber-600 via-amber-500 to-orange-500 text-white">
      <div className="max-w-6xl mx-auto px-4 h-9 flex items-center justify-center gap-3 text-[13px]">
        <button
          onClick={handleClick}
          className="flex items-center gap-3 hover:opacity-90 transition-opacity"
        >
          <span className="hidden sm:inline font-medium">
            EU AI Act Article 50 takes effect in
          </span>
          <span className="sm:hidden font-medium">Art. 50 in</span>

          <span className="font-mono font-bold tabular-nums tracking-tight">
            {days}d {String(hours).padStart(2, '0')}h {String(mins).padStart(2, '0')}m {String(secs).padStart(2, '0')}s
          </span>

          <span className="hidden sm:inline text-amber-100">
            — your AI content must be labeled
          </span>

          <span className="inline-flex items-center gap-1 ml-1 px-2 py-0.5 rounded-full bg-white/20 text-[11px] font-semibold">
            Learn more
            <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
            </svg>
          </span>
        </button>

        <button
          onClick={onDismiss}
          className="absolute right-3 p-1 rounded hover:bg-white/20 transition-colors"
          aria-label="Dismiss banner"
        >
          <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>
  );
}
