import { useState, useEffect } from 'react';

interface Stats {
  karma: number;
  posts: number;
  mentions: number;
}

const FALLBACK: Stats = { karma: 58, posts: 4, mentions: 7 };
const POLL_INTERVAL = 60_000;

export default function MoltbookStats() {
  const [stats, setStats] = useState<Stats>(FALLBACK);

  useEffect(() => {
    let cancelled = false;

    async function fetchStats() {
      try {
        const res = await fetch('/api/moltbook-stats');
        if (!res.ok) return;
        const data = await res.json();
        if (cancelled) return;
        if (data.karma > 0) {
          setStats({
            karma: data.karma || FALLBACK.karma,
            posts: data.posts || FALLBACK.posts,
            mentions: data.mentions || FALLBACK.mentions,
          });
        }
      } catch {
        // Keep current values
      }
    }

    fetchStats();
    const id = setInterval(fetchStats, POLL_INTERVAL);
    return () => { cancelled = true; clearInterval(id); };
  }, []);

  return (
    <a
      href="https://www.moltbook.com/u/akf-agent"
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-3 px-5 py-2.5 rounded-full bg-surface-raised border border-border-subtle hover:border-accent/40 transition-colors group"
    >
      <span className="flex items-center gap-1.5">
        <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09zM18.259 8.715L18 9.75l-.259-1.035a3.375 3.375 0 00-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 002.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 002.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 00-2.455 2.456z" />
        </svg>
        <span className="text-text-secondary text-sm">akf-agent on Moltbook</span>
      </span>
      <span className="h-4 w-px bg-border-subtle" />
      <span className="flex items-center gap-3 text-xs text-text-tertiary">
        <span><strong className="text-text-primary">{stats.karma}</strong> karma</span>
        <span><strong className="text-text-primary">{stats.posts}</strong> posts</span>
        <span><strong className="text-text-primary">{stats.mentions}</strong> agent mentions</span>
      </span>
      <svg className="w-3.5 h-3.5 text-text-tertiary group-hover:text-accent transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
      </svg>
    </a>
  );
}
