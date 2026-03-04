import { useState, useEffect } from 'react';

const GITHUB_REPO = 'HMAKT99/AKF';
const NPM_PACKAGE = 'akf';

interface Stats {
  stars: number;
  forks: number;
  issues: number;
  npmDownloads: number;
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString();
}

function StatItem({ icon, value, label }: { icon: React.ReactNode; value: string; label: string }) {
  return (
    <div className="flex items-center gap-2 px-4 py-2">
      <span className="text-accent">{icon}</span>
      <span className="text-lg font-semibold text-text-primary tabular-nums">{value}</span>
      <span className="text-sm text-text-tertiary">{label}</span>
    </div>
  );
}

export default function GitHubStats() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchStats() {
      try {
        const [ghRes, npmRes] = await Promise.allSettled([
          fetch(`https://api.github.com/repos/${GITHUB_REPO}`),
          fetch(`https://api.npmjs.org/downloads/point/last-month/${NPM_PACKAGE}`),
        ]);

        if (cancelled) return;

        const gh =
          ghRes.status === 'fulfilled' && ghRes.value.ok
            ? await ghRes.value.json()
            : null;
        const npm =
          npmRes.status === 'fulfilled' && npmRes.value.ok
            ? await npmRes.value.json()
            : null;

        setStats({
          stars: gh?.stargazers_count ?? 0,
          forks: gh?.forks_count ?? 0,
          issues: gh?.open_issues_count ?? 0,
          npmDownloads: npm?.downloads ?? 0,
        });
      } catch {
        // Stats are non-critical — fail silently
      }
    }

    fetchStats();
    return () => { cancelled = true; };
  }, []);

  if (!stats) {
    return (
      <div className="flex justify-center py-4">
        <div className="flex flex-wrap justify-center gap-1 rounded-xl border border-border-subtle bg-surface-raised px-2 py-1">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="flex items-center gap-2 px-4 py-2">
              <div className="w-4 h-4 rounded bg-border-subtle animate-pulse" />
              <div className="w-8 h-5 rounded bg-border-subtle animate-pulse" />
              <div className="w-12 h-4 rounded bg-border-subtle animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-center py-4">
      <div className="flex flex-wrap justify-center gap-1 rounded-xl border border-border-subtle bg-surface-raised px-2 py-1">
        <StatItem
          icon={
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 .587l3.668 7.568L24 9.306l-6 5.848 1.416 8.259L12 19.446l-7.416 3.967L6 15.154 0 9.306l8.332-1.151z" />
            </svg>
          }
          value={formatNumber(stats.stars)}
          label="Stars"
        />
        <span className="self-center text-border-subtle">|</span>
        <StatItem
          icon={
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          }
          value={formatNumber(stats.forks)}
          label="Forks"
        />
        <span className="self-center text-border-subtle">|</span>
        <StatItem
          icon={
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          }
          value={formatNumber(stats.npmDownloads)}
          label="Downloads/mo"
        />
        <span className="self-center text-border-subtle">|</span>
        <StatItem
          icon={
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          value={formatNumber(stats.issues)}
          label="Issues"
        />
      </div>
    </div>
  );
}
