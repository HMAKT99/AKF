import { useState, useEffect } from 'react';

const GITHUB_REPO = 'HMAKT99/AKF';
const NPM_PACKAGE = 'akf-format';

interface Stats {
  stars: number;
  forks: number;
  issues: number;
  npmDownloads: number;
  watchers: number;
  contributors: number;
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `${(n / 1_000).toFixed(1)}k`;
  return n.toLocaleString();
}

function StatItem({ icon, value, label }: { icon: React.ReactNode; value: string; label: string }) {
  return (
    <div className="flex flex-col items-center gap-1 px-5 py-3 min-w-[100px]">
      <span className="text-accent">{icon}</span>
      <span className="text-2xl font-bold text-text-primary tabular-nums">{value}</span>
      <span className="text-xs text-text-tertiary whitespace-nowrap">{label}</span>
    </div>
  );
}

export default function GitHubStats() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function fetchStats() {
      try {
        const [ghRes, npmRes, contribRes] = await Promise.allSettled([
          fetch(`https://api.github.com/repos/${GITHUB_REPO}`),
          fetch(`https://api.npmjs.org/downloads/point/last-month/${NPM_PACKAGE}`),
          fetch(`https://api.github.com/repos/${GITHUB_REPO}/contributors?per_page=1&anon=true`, {
            headers: { Accept: 'application/json' },
          }),
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

        // Get contributor count from Link header
        let contributorCount = 0;
        if (contribRes.status === 'fulfilled' && contribRes.value.ok) {
          const link = contribRes.value.headers.get('Link');
          if (link) {
            const match = link.match(/page=(\d+)>; rel="last"/);
            contributorCount = match ? parseInt(match[1], 10) : 1;
          } else {
            const contribData = await contribRes.value.json();
            contributorCount = Array.isArray(contribData) ? contribData.length : 0;
          }
        }

        setStats({
          stars: gh?.stargazers_count ?? 0,
          forks: gh?.forks_count ?? 0,
          issues: gh?.open_issues_count ?? 0,
          npmDownloads: npm?.downloads ?? 0,
          watchers: gh?.subscribers_count ?? 0,
          contributors: contributorCount,
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
      <div className="flex justify-center py-6">
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-4 rounded-2xl border border-border-subtle bg-surface-raised px-6 py-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <div key={i} className="flex flex-col items-center gap-2 px-5 py-3">
              <div className="w-5 h-5 rounded bg-border-subtle animate-pulse" />
              <div className="w-12 h-7 rounded bg-border-subtle animate-pulse" />
              <div className="w-16 h-3 rounded bg-border-subtle animate-pulse" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const totalDownloads = stats.npmDownloads;

  return (
    <div className="flex justify-center py-6">
      <div className="grid grid-cols-3 sm:grid-cols-6 gap-0 rounded-2xl border border-border-subtle bg-surface-raised px-2 py-2">
        <StatItem
          icon={
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M12 .587l3.668 7.568L24 9.306l-6 5.848 1.416 8.259L12 19.446l-7.416 3.967L6 15.154 0 9.306l8.332-1.151z" />
            </svg>
          }
          value={formatNumber(stats.stars)}
          label="Stars"
        />
        <StatItem
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
            </svg>
          }
          value={formatNumber(stats.forks)}
          label="Forks"
        />
        <StatItem
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          }
          value={formatNumber(totalDownloads)}
          label="npm Downloads/mo"
        />
        <StatItem
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          }
          value={formatNumber(stats.watchers)}
          label="Watchers"
        />
        <StatItem
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          }
          value={formatNumber(stats.contributors)}
          label="Contributors"
        />
        <StatItem
          icon={
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          }
          value={formatNumber(stats.issues)}
          label="Open Issues"
        />
      </div>
    </div>
  );
}
