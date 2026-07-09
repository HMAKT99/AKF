import { useCallback, useEffect, useState } from 'react';

const TARGET = new Date('2026-08-02T00:00:00Z').getTime();

function useCountdown() {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  const diff = Math.max(0, TARGET - now);
  return {
    days: Math.floor(diff / 86_400_000),
    hours: Math.floor((diff % 86_400_000) / 3_600_000),
    mins: Math.floor((diff % 3_600_000) / 60_000),
    secs: Math.floor((diff % 60_000) / 1000),
    passed: diff === 0,
  };
}

function Digit({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex flex-col items-center">
      <span className="text-3xl sm:text-5xl font-extrabold font-mono tabular-nums text-text-primary leading-none">
        {String(value).padStart(2, '0')}
      </span>
      <span className="mt-1 text-[10px] sm:text-xs font-semibold uppercase tracking-widest text-text-tertiary">
        {label}
      </span>
    </div>
  );
}

/* ── Client-side readiness check — the file never leaves the browser ── */

type Verdict =
  | { status: 'ready'; found: string[] }
  | { status: 'partial'; found: string[]; missing: string }
  | { status: 'not-ready' }
  | { status: 'unsupported'; ext: string };

const TEXT_EXTENSIONS = [
  'md', 'markdown', 'txt', 'html', 'htm', 'json', 'yaml', 'yml', 'py', 'js', 'ts',
  'tsx', 'jsx', 'go', 'rs', 'java', 'rb', 'css', 'xml', 'csv', 'toml', 'akf',
];

function extractAkfMetadata(text: string, ext: string): Record<string, unknown> | null {
  // JSON: reserved _akf key, or a native .akf unit
  if (ext === 'json' || ext === 'akf') {
    try {
      const data = JSON.parse(text);
      if (data && typeof data === 'object') {
        if (data._akf) {
          return typeof data._akf === 'string' ? JSON.parse(data._akf) : data._akf;
        }
        if (data.claims && (data.v || data.version)) return data;
      }
    } catch {
      /* fall through to generic scan */
    }
  }

  // HTML: JSON-LD block
  const jsonLd = text.match(/<script[^>]*type="application\/akf\+json"[^>]*>([\s\S]*?)<\/script>/);
  if (jsonLd) {
    try {
      return JSON.parse(jsonLd[1].trim());
    } catch {
      /* ignore */
    }
  }

  // Frontmatter: legacy `_akf: '{json}'` single line
  const legacy = text.match(/^_akf:\s*'(\{[\s\S]*?\})'\s*$/m);
  if (legacy) {
    try {
      return JSON.parse(legacy[1]);
    } catch {
      /* ignore */
    }
  }

  // Frontmatter: native `akf:` YAML block — detect fields without a YAML parser
  const fm = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  if (fm && /^akf:\s*$/m.test(fm[1])) {
    const block = fm[1];
    const meta: Record<string, unknown> = { _nativeYaml: true };
    if (/^\s+ai:\s*true/m.test(block)) meta.ai = true;
    if (/^\s+agent:/m.test(block)) meta.agent = true;
    if (/^\s+at:/m.test(block)) meta.at = true;
    if (/^\s+- c:/m.test(block) || /^\s+claims:/m.test(block)) meta.claims = true;
    if (/^\s+hash:/m.test(block)) meta.hash = true;
    return meta;
  }

  return null;
}

function judge(meta: Record<string, unknown> | null): Verdict {
  if (!meta) return { status: 'not-ready' };

  const found: string[] = [];
  const metaStr = JSON.stringify(meta);
  const hasAiFlag = /"ai"\s*:\s*true|"ai_generated"\s*:\s*true/.test(metaStr) || meta.ai === true;

  found.push('Machine-readable metadata embedded in the file');
  if (/"agent"|"by"|"author"/.test(metaStr) || meta.agent) found.push('Origin recorded (agent / author)');
  if (/"at"|"created"|"timestamp"/.test(metaStr) || meta.at) found.push('Creation timestamp');
  if (/"claims"|"c":/.test(metaStr) || meta.claims) found.push('Content claims with trust scores');
  if (/"hash"|"integrity_hash"/.test(metaStr) || meta.hash) found.push('Integrity hash');

  if (hasAiFlag) {
    found.splice(1, 0, 'AI-generated flag (the Article 50 marking)');
    return { status: 'ready', found };
  }
  return {
    status: 'partial',
    found,
    missing: 'The metadata does not mark the content as AI-generated (no ai flag).',
  };
}

function CheckZone() {
  const [verdict, setVerdict] = useState<Verdict | null>(null);
  const [fileName, setFileName] = useState('');
  const [dragging, setDragging] = useState(false);

  const handleFile = useCallback((file: File) => {
    setFileName(file.name);
    const ext = (file.name.split('.').pop() || '').toLowerCase();
    if (!TEXT_EXTENSIONS.includes(ext)) {
      setVerdict({ status: 'unsupported', ext });
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      const text = String(reader.result || '');
      setVerdict(judge(extractAkfMetadata(text, ext)));
    };
    reader.readAsText(file);
  }, []);

  return (
    <div className="max-w-2xl mx-auto">
      <label
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          if (e.dataTransfer.files[0]) handleFile(e.dataTransfer.files[0]);
        }}
        className={`block cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition-colors ${
          dragging ? 'border-accent bg-accent/5' : 'border-border-subtle bg-surface-raised hover:border-accent/50'
        }`}
      >
        <input
          type="file"
          className="hidden"
          onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
        />
        <svg className="w-10 h-10 mx-auto text-text-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
        </svg>
        <p className="mt-3 text-text-primary font-medium">Drop a file — or click to choose</p>
        <p className="mt-1 text-sm text-text-secondary">
          Checked entirely in your browser. The file is never uploaded.
        </p>
      </label>

      {verdict && (
        <div className="mt-6">
          {verdict.status === 'ready' && (
            <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-6">
              <p className="text-lg font-bold text-emerald-500">✅ READY — {fileName}</p>
              <p className="mt-1 text-sm text-text-secondary">
                This file carries machine-readable transparency metadata, including the AI-generated marking Article 50 calls for.
              </p>
              <ul className="mt-3 space-y-1 text-sm text-text-secondary">
                {verdict.found.map((f) => <li key={f}>• {f}</li>)}
              </ul>
            </div>
          )}
          {verdict.status === 'partial' && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/5 p-6">
              <p className="text-lg font-bold text-amber-500">⚠ PARTIAL — {fileName}</p>
              <p className="mt-1 text-sm text-text-secondary">{verdict.missing}</p>
              <ul className="mt-3 space-y-1 text-sm text-text-secondary">
                {verdict.found.map((f) => <li key={f}>• {f}</li>)}
              </ul>
              <p className="mt-3 text-sm text-text-secondary">
                Re-stamp with the AI flag: <code className="text-accent font-mono">akf stamp {fileName} --agent your-tool</code>
              </p>
            </div>
          )}
          {verdict.status === 'not-ready' && (
            <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-6">
              <p className="text-lg font-bold text-red-500">✕ NOT READY — {fileName}</p>
              <p className="mt-1 text-sm text-text-secondary">
                No transparency metadata found. If this content is AI-generated and in scope, it carries none of the
                machine-readable marking Article 50 requires after August 2, 2026. The fix takes about five minutes — see below.
              </p>
            </div>
          )}
          {verdict.status === 'unsupported' && (
            <div className="rounded-xl border border-border-subtle bg-surface-raised p-6">
              <p className="text-lg font-bold text-text-primary">.{verdict.ext} — use the deep audit</p>
              <p className="mt-1 text-sm text-text-secondary">
                The in-browser check covers text formats. For DOCX, PDF, and images, run the free deep audit —
                <a className="text-accent underline" href="https://huggingface.co/spaces/HANAKT19/eu-ai-act-check" target="_blank" rel="noopener noreferrer"> hosted checker</a> or locally:
                <code className="block mt-2 text-accent font-mono text-xs">pip install akf && akf audit {fileName} --regulation eu_ai_act</code>
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ArticleFiftyPage() {
  const { days, hours, mins, secs, passed } = useCountdown();

  useEffect(() => {
    document.title = 'EU AI Act Article 50 Readiness Check — is your AI content compliant? | AKF';
  }, []);

  return (
    <div className="pt-24 pb-20 px-6">
      <div className="max-w-4xl mx-auto">
        {/* Hero + countdown */}
        <section className="text-center mb-14">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/20 text-red-500 text-sm font-medium mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
            EU AI Act · Article 50 · August 2, 2026
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight leading-[1.1]">
            Will your AI content
            <br />
            <span className="text-accent">pass Article 50?</span>
          </h1>
          <p className="mt-5 text-lg text-text-secondary max-w-2xl mx-auto">
            {passed
              ? 'Article 50 transparency obligations are now in effect.'
              : 'AI-generated content must carry machine-readable transparency marking in:'}
          </p>
          {!passed && (
            <div className="mt-6 flex items-center justify-center gap-6">
              <Digit value={days} label="days" />
              <Digit value={hours} label="hours" />
              <Digit value={mins} label="mins" />
              <Digit value={secs} label="secs" />
            </div>
          )}
        </section>

        {/* The check */}
        <section className="mb-16">
          <CheckZone />
        </section>

        {/* The fix */}
        <section className="mb-16 max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-text-primary mb-4">The five-minute fix</h2>
          <pre className="rounded-xl bg-surface-raised border border-border-subtle p-5 text-sm font-mono text-text-primary overflow-x-auto">
{`pip install akf

# Mark AI-generated content (machine-readable, embeds into the file)
akf stamp report.md --agent your-ai-tool

# Check readiness against the EU AI Act
akf audit report.md --regulation eu_ai_act`}
          </pre>
          <p className="mt-3 text-sm text-text-secondary">
            Works across 20+ formats — Markdown, HTML, JSON, DOCX, PDF, images. Free and open source (MIT).
            Agents can do it automatically: <code className="text-accent font-mono">akf init</code> wires the hooks.
          </p>
        </section>

        {/* What Article 50 requires */}
        <section className="mb-16 max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-text-primary mb-4">What Article 50 actually requires</h2>
          <ul className="space-y-3 text-text-secondary">
            <li>
              <strong className="text-text-primary">Who:</strong> providers and deployers of AI systems that generate
              synthetic text, images, audio, or video — including interactive AI systems that users may mistake for humans.
            </li>
            <li>
              <strong className="text-text-primary">What:</strong> AI-generated and manipulated content must be marked
              as such in a machine-readable format, and detectable as artificially generated. Deepfakes require
              explicit disclosure.
            </li>
            <li>
              <strong className="text-text-primary">Or else:</strong> administrative fines up to EUR 15M or 3% of global
              turnover for transparency violations (higher tiers apply to other AI Act breaches).
            </li>
          </ul>
          <p className="mt-6 text-xs text-text-tertiary">
            This page is an automated readiness signal, not legal advice. Scope and enforcement depend on your
            specific system and jurisdiction — consult counsel for compliance decisions.
          </p>
        </section>
      </div>
    </div>
  );
}
