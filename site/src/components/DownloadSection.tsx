import { useState, useEffect } from 'react';
import SectionHeading from '../ui/SectionHeading';

const GITHUB_REPO = 'HMAKT99/AKF';

interface ReleaseInfo {
  tag: string;
  name: string;
  zipUrl: string;
  tarUrl: string;
  publishedAt: string;
}

function useLatestRelease() {
  const [release, setRelease] = useState<ReleaseInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const controller = new AbortController();
    fetch(`https://api.github.com/repos/${GITHUB_REPO}/releases/latest`, {
      signal: controller.signal,
      headers: { Accept: 'application/vnd.github.v3+json' },
    })
      .then((res) => {
        if (!res.ok) throw new Error('No release');
        return res.json();
      })
      .then((data) => {
        setRelease({
          tag: data.tag_name,
          name: data.name || data.tag_name,
          zipUrl: data.zipball_url,
          tarUrl: data.tarball_url,
          publishedAt: data.published_at,
        });
      })
      .catch(() => {
        // Fallback to main branch download
        setRelease(null);
      })
      .finally(() => setLoading(false));

    return () => controller.abort();
  }, []);

  return { release, loading };
}

const installMethods = [
  {
    label: 'Python',
    command: 'pip install akf',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M14.25.18l.9.2.73.26.59.3.45.32.34.34.25.34.16.33.1.3.04.26.02.2-.01.13V8.5l-.05.63-.13.55-.21.46-.26.38-.3.31-.33.25-.35.19-.35.14-.33.1-.3.07-.26.04-.21.02H8.77l-.69.05-.59.14-.5.22-.41.27-.33.32-.27.35-.2.36-.15.37-.1.35-.07.32-.04.27-.02.21v3.06H3.17l-.21-.03-.28-.07-.32-.12-.35-.18-.36-.26-.36-.36-.35-.46-.32-.59-.28-.73-.21-.88-.14-1.05-.05-1.23.06-1.22.16-1.04.24-.87.32-.71.36-.57.4-.44.42-.33.42-.24.4-.16.36-.1.32-.05.24-.01h.16l.06.01h8.16v-.83H6.18l-.01-2.75-.02-.37.05-.35.12-.33.18-.3.25-.27.31-.23.38-.2.44-.18.51-.15.58-.12.64-.1.71-.06.77-.04.84-.02 1.27.05zm-6.3 1.98l-.23.33-.08.41.08.41.23.34.33.22.41.09.41-.09.33-.22.23-.34.08-.41-.08-.41-.23-.33-.33-.22-.41-.09-.41.09z" />
        <path d="M21.1 6.11l.28.06.32.12.35.18.36.27.36.35.35.47.32.59.28.73.21.88.14 1.04.05 1.23-.06 1.23-.16 1.04-.24.86-.32.71-.36.57-.4.45-.42.33-.42.24-.4.16-.36.09-.32.05-.24.02-.16-.01h-8.22v.82h5.84l.01 2.76.02.36-.05.34-.12.33-.18.3-.25.27-.31.23-.38.2-.44.18-.51.15-.58.12-.64.09-.71.07-.77.04-.84.01-1.27-.04-1.07-.14-.9-.2-.73-.25-.59-.3-.45-.33-.34-.34-.25-.34-.16-.33-.1-.3-.04-.25-.02-.2.01-.13v-5.34l.05-.64.13-.54.21-.46.26-.38.3-.32.33-.24.35-.2.35-.14.33-.1.3-.06.26-.04.21-.02.13-.01h5.84l.69-.05.59-.14.5-.21.41-.28.33-.32.27-.35.2-.36.15-.36.1-.35.07-.32.04-.28.02-.21V6.07h2.09l.14.01z" />
      </svg>
    ),
  },
  {
    label: 'npm',
    command: 'npm install akf',
    icon: (
      <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
        <path d="M1.763 0C.786 0 0 .786 0 1.763v20.474C0 23.214.786 24 1.763 24h20.474c.977 0 1.763-.786 1.763-1.763V1.763C24 .786 23.214 0 22.237 0zM5.13 5.323l13.837.019-.009 13.836h-3.464l.01-10.382h-3.456L12.04 19.17H5.113z" />
      </svg>
    ),
  },
  {
    label: 'Source',
    command: 'git clone https://github.com/HMAKT99/AKF.git',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
      </svg>
    ),
  },
];

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(text).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <button
      onClick={handleCopy}
      className="shrink-0 p-1.5 rounded-md text-text-tertiary hover:text-text-primary transition-colors cursor-pointer"
      aria-label={`Copy "${text}" to clipboard`}
    >
      {copied ? (
        <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      ) : (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
        </svg>
      )}
    </button>
  );
}

export default function DownloadSection() {
  const { release, loading } = useLatestRelease();

  const zipUrl = release
    ? release.zipUrl
    : `https://github.com/${GITHUB_REPO}/archive/refs/heads/main.zip`;

  const tarUrl = release
    ? release.tarUrl
    : `https://github.com/${GITHUB_REPO}/archive/refs/heads/main.tar.gz`;

  return (
    <section id="download" className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="Download AKF"
          subtitle="Install via your package manager, clone the source, or download directly from GitHub."
        />

        {/* Direct download buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3 mb-10">
          <a
            href={zipUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2.5 px-5 py-3 rounded-xl bg-accent hover:bg-accent-hover text-white font-medium text-sm transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
            </svg>
            {loading ? 'Download .zip' : release ? `Download ${release.tag} (.zip)` : 'Download .zip'}
          </a>
          <a
            href={tarUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2.5 px-5 py-3 rounded-xl bg-surface-raised border border-border-subtle hover:border-accent/40 text-text-primary font-medium text-sm transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m8.25 3v6.75m0 0l-3-3m3 3l3-3M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
            </svg>
            {loading ? 'Download .tar.gz' : release ? `Download ${release.tag} (.tar.gz)` : 'Download .tar.gz'}
          </a>
          <a
            href={`https://github.com/${GITHUB_REPO}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2.5 px-5 py-3 rounded-xl bg-surface-raised border border-border-subtle hover:border-accent/40 text-text-primary font-medium text-sm transition-colors"
          >
            <svg className="w-4.5 h-4.5" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            View Source
          </a>
        </div>

        {release && (
          <p className="text-center text-xs text-text-tertiary mb-8">
            Latest release: <span className="font-semibold text-text-secondary">{release.name}</span>
            {' '}published {new Date(release.publishedAt).toLocaleDateString()}
          </p>
        )}

        {/* Install methods */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {installMethods.map((m) => (
            <div
              key={m.label}
              className="rounded-xl border border-border-subtle bg-surface-raised p-4"
            >
              <div className="flex items-center gap-2.5 mb-3">
                <div className="w-8 h-8 rounded-lg bg-accent/10 text-accent flex items-center justify-center">
                  {m.icon}
                </div>
                <span className="text-sm font-semibold text-text-primary">{m.label}</span>
              </div>
              <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface border border-border-subtle font-mono text-xs">
                <span className="text-text-tertiary select-none">$</span>
                <span className="text-text-primary flex-1 truncate">{m.command}</span>
                <CopyButton text={m.command} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
