import { Link } from 'react-router-dom';

const fileExamples = [
  {
    icon: '📄',
    format: '.docx',
    file: 'quarterly-report.docx',
    result: 'Trust: 0.5 · Origin: unknown · Review: unreviewed',
    color: 'text-blue-500',
    embedding: 'Native (Custom XML)',
  },
  {
    icon: '📊',
    format: '.xlsx',
    file: 'forecast-model.xlsx',
    result: 'Trust: 0.5 · Origin: unknown · Review: unreviewed',
    color: 'text-emerald-500',
    embedding: 'Native (Sheet Property)',
  },
  {
    icon: '📑',
    format: '.pdf',
    file: 'compliance-report.pdf',
    result: 'Trust: 0.5 · Origin: unknown · Review: unreviewed',
    color: 'text-red-500',
    embedding: 'Native (XMP Metadata)',
  },
  {
    icon: '🖼️',
    format: '.png',
    file: 'hero-banner.png',
    result: 'Integrity: sha256:a3f2… · Review: unreviewed',
    color: 'text-purple-500',
    embedding: 'Native (tEXt Chunk)',
  },
  {
    icon: '🎵',
    format: '.mp3',
    file: 'podcast-intro.mp3',
    result: 'Integrity: sha256:7b1c… · Review: unreviewed',
    color: 'text-amber-500',
    embedding: 'Sidecar (.mp3.akf.json)',
  },
  {
    icon: '🎬',
    format: '.mp4',
    file: 'product-demo.mp4',
    result: 'Integrity: sha256:e9d4… · Review: unreviewed',
    color: 'text-pink-500',
    embedding: 'Sidecar (.mp4.akf.json)',
  },
  {
    icon: '💻',
    format: '.py',
    file: 'data-pipeline.py',
    result: 'Trust: 0.5 · Author: git blame · Review: unreviewed',
    color: 'text-cyan-500',
    embedding: 'Native (Comment Header)',
  },
  {
    icon: '📝',
    format: '.md',
    file: 'api-docs.md',
    result: 'Trust: 0.5 · Origin: unknown · Review: unreviewed',
    color: 'text-text-secondary',
    embedding: 'Native (YAML Frontmatter)',
  },
];

const steps = [
  {
    num: '01',
    title: 'Point',
    desc: 'Point AKF at any folder — your documents, creative assets, shared drives, code repos. Any folder, any content type.',
  },
  {
    num: '02',
    title: 'Enrich',
    desc: 'Every file gets an integrity hash, format detection, and an honest "unreviewed" flag. Native embedding where possible, lightweight sidecar files where not.',
  },
  {
    num: '03',
    title: 'Audit',
    desc: 'Now run akf audit and akf scan across everything. Full compliance visibility. Structured review queue. Complete inventory.',
  },
];

const enrichmentDetails = [
  {
    title: 'SHA-256 Integrity Hash',
    desc: 'Every file gets a cryptographic fingerprint. From this moment forward, any tampering is detectable.',
    icon: (
      <svg className="w-6 h-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
  },
  {
    title: 'Format Detection',
    desc: 'Automatic identification of file type, structure, and the best embedding strategy (native or sidecar).',
    icon: (
      <svg className="w-6 h-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m5.231 13.481L15 17.25m-4.5-15H5.625c-.621 0-1.125.504-1.125 1.125v16.5c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9zm3.75 11.625a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
      </svg>
    ),
  },
  {
    title: 'Full Inventory',
    desc: 'Every file cataloged. You now know exactly what\'s in your system — the foundation for any governance program.',
    icon: (
      <svg className="w-6 h-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z" />
      </svg>
    ),
  },
  {
    title: 'Review Queue',
    desc: 'Every enriched file is marked "unreviewed" — giving your team a structured, prioritizable queue instead of an impossible mountain.',
    icon: (
      <svg className="w-6 h-6 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3.75 12h.007v.008H3.75V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm-.375 5.25h.007v.008H3.75v-.008zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
      </svg>
    ),
  },
];

export default function ConvertPage() {
  return (
    <div className="pt-14">
      {/* ── HERO ── */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <Link to="/" className="text-sm text-accent hover:underline mb-10 inline-block">← Home</Link>

          <p className="text-xs font-mono text-accent tracking-widest uppercase mb-3">Bulk Enrichment</p>
          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-text-primary">
            Make every existing file{' '}
            <span className="text-accent">trust-aware</span>
          </h1>
          <p className="mt-5 text-lg text-text-secondary max-w-2xl mx-auto leading-relaxed">
            Documents, images, spreadsheets, code, audio, video — one command brings your entire file system into AKF.
            Full inventory. Integrity verification. Structured review queue.
          </p>

          {/* The one-liner */}
          <div className="mt-10 inline-block">
            <div className="bg-gray-900 rounded-xl px-8 py-4 border border-gray-700">
              <code className="text-lg sm:text-xl font-mono">
                <span className="text-gray-500">$ </span>
                <span className="text-emerald-400">akf enrich</span>
                <span className="text-gray-300"> ./your-files/</span>
              </code>
            </div>
          </div>
        </div>
      </section>

      {/* ── WHAT GETS ENRICHED ── */}
      <section className="py-16 px-6 bg-surface-raised/50">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-3">
            Every format. Every content type.
          </h2>
          <p className="text-text-secondary text-center mb-12 max-w-xl mx-auto">
            AKF embeds metadata natively where the format supports it. For everything else, a lightweight sidecar file travels alongside.
          </p>

          <div className="grid sm:grid-cols-2 gap-3">
            {fileExamples.map((f) => (
              <div
                key={f.file}
                className="rounded-xl border border-border-subtle bg-surface p-4 flex items-start gap-4 hover:border-accent/30 transition-colors"
              >
                <span className="text-2xl mt-0.5">{f.icon}</span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-sm font-mono font-bold ${f.color}`}>{f.format}</span>
                    <span className="text-xs text-text-tertiary">·</span>
                    <span className="text-sm font-mono text-text-secondary truncate">{f.file}</span>
                  </div>
                  <p className="text-xs text-text-tertiary font-mono">{f.result}</p>
                  <p className="text-xs text-text-tertiary mt-1">{f.embedding}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ── */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-14">
            Three steps to full visibility
          </h2>

          <div className="flex flex-col gap-12">
            {steps.map((s) => (
              <div key={s.num} className="flex gap-6">
                <span className="text-3xl font-mono font-bold text-accent/30 shrink-0 w-12 text-right">{s.num}</span>
                <div>
                  <h3 className="text-xl font-bold text-text-primary mb-2">{s.title}</h3>
                  <p className="text-text-secondary leading-relaxed">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── WHAT YOU GET ── */}
      <section className="py-16 px-6 bg-surface-raised/50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-3">
            What enrichment adds to every file
          </h2>
          <p className="text-text-secondary text-center mb-12 max-w-xl mx-auto">
            Enrichment doesn't guess trust scores. It gives you real, verifiable foundations — integrity hashes, format detection, and a clear path to full trust metadata.
          </p>

          <div className="grid sm:grid-cols-2 gap-4">
            {enrichmentDetails.map((d) => (
              <div key={d.title} className="rounded-xl border border-border-subtle bg-surface p-5">
                <div className="flex items-center gap-3 mb-2">
                  {d.icon}
                  <h3 className="font-semibold text-text-primary">{d.title}</h3>
                </div>
                <p className="text-sm text-text-secondary leading-relaxed">{d.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── BEFORE / AFTER ── */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-12">
            Before and after
          </h2>

          <div className="grid sm:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-red-400/60" />
                <p className="text-xs font-mono text-text-tertiary uppercase tracking-wider">Before enrichment</p>
              </div>
              <div className="rounded-xl border border-border-subtle bg-surface-raised p-5 h-full">
                <pre className="text-sm font-mono text-text-tertiary leading-relaxed whitespace-pre-wrap">{`quarterly-report.docx
hero-banner.png
forecast-model.xlsx
podcast-intro.mp3
product-demo.mp4
data-pipeline.py

No trust metadata.
No integrity verification.
No way to audit.
No idea what's AI-generated.`}</pre>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-accent" />
                <p className="text-xs font-mono text-accent uppercase tracking-wider">After enrichment</p>
              </div>
              <div className="rounded-xl border border-accent/20 bg-surface-raised p-5 h-full">
                <pre className="text-sm font-mono text-text-secondary leading-relaxed whitespace-pre-wrap">{`quarterly-report.docx`}  <span className="text-emerald-500">✓ enriched</span>{`
hero-banner.png`}       <span className="text-emerald-500">✓ enriched</span>{`
forecast-model.xlsx`}   <span className="text-emerald-500">✓ enriched</span>{`
podcast-intro.mp3`}     <span className="text-amber-500">+ sidecar</span>{`
product-demo.mp4`}      <span className="text-amber-500">+ sidecar</span>{`
data-pipeline.py`}      <span className="text-emerald-500">✓ enriched</span>{`

`}<span className="text-emerald-500 font-bold">6 files enriched</span>{`
`}<span className="text-amber-500">2 sidecar files created</span>{`
`}<span className="text-accent">6 flagged for review</span>{`
`}<span className="text-text-tertiary">0 errors</span></pre>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── PATH 1: CLI ── */}
      <section className="py-16 px-6 bg-surface-raised/50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-3">
            For developers & DevOps
          </h2>
          <p className="text-text-secondary text-center mb-10">
            One command. Any folder. Any content type.
          </p>

          <div className="bg-gray-900 rounded-xl overflow-hidden border border-gray-700">
            <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-800 border-b border-gray-700">
              <span className="w-2.5 h-2.5 rounded-full bg-[#ff5f57]" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#febc2e]" />
              <span className="w-2.5 h-2.5 rounded-full bg-[#28c840]" />
            </div>
            <pre className="p-5 text-sm font-mono leading-relaxed text-gray-300 overflow-x-auto">
              <span className="text-gray-500"># Install</span>{'\n'}
              <span className="text-emerald-400">pip install</span>{' akf\n\n'}
              <span className="text-gray-500"># Enrich your documents folder</span>{'\n'}
              <span className="text-emerald-400">akf enrich</span>{' ~/Documents/reports/\n\n'}
              <span className="text-gray-500"># Enrich creative assets</span>{'\n'}
              <span className="text-emerald-400">akf enrich</span>{' ~/Creative/ai-assets/\n\n'}
              <span className="text-gray-500"># Enrich a shared drive</span>{'\n'}
              <span className="text-emerald-400">akf enrich</span>{' /mnt/shared/marketing/\n\n'}
              <span className="text-gray-500"># Enrich a code repo (git-aware)</span>{'\n'}
              <span className="text-emerald-400">akf enrich</span>{' ./my-repo/ '}<span className="text-sky-400">--git-aware</span>{'\n\n'}
              <span className="text-gray-500"># Preview without modifying anything</span>{'\n'}
              <span className="text-emerald-400">akf enrich</span>{' ./data/ '}<span className="text-sky-400">--dry-run</span>{'\n\n'}
              <span className="text-gray-500"># Then audit everything</span>{'\n'}
              <span className="text-emerald-400">akf audit</span>{' ./Documents/ '}<span className="text-sky-400">--framework</span>{' eu-ai-act'}
            </pre>
          </div>

          <div className="mt-8 grid sm:grid-cols-3 gap-3 text-center">
            <div className="rounded-lg border border-border-subtle bg-surface p-4">
              <p className="text-2xl font-bold font-mono text-text-primary">20+</p>
              <p className="text-xs text-text-tertiary mt-1">Supported formats</p>
            </div>
            <div className="rounded-lg border border-border-subtle bg-surface p-4">
              <p className="text-2xl font-bold font-mono text-text-primary">--parallel</p>
              <p className="text-xs text-text-tertiary mt-1">Multi-threaded processing</p>
            </div>
            <div className="rounded-lg border border-border-subtle bg-surface p-4">
              <p className="text-2xl font-bold font-mono text-text-primary">--dry-run</p>
              <p className="text-xs text-text-tertiary mt-1">Preview before modifying</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── PATH 3: OFFICE / WORKSPACE ── */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-3">
            For teams & knowledge workers
          </h2>
          <p className="text-text-secondary text-center mb-12">
            No terminal required. Enrich documents directly from the tools your team already uses.
          </p>

          <div className="grid sm:grid-cols-2 gap-6">
            {/* Microsoft Office */}
            <div className="rounded-xl border border-border-subtle bg-surface-raised p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                  <span className="text-blue-500 font-bold text-lg">M</span>
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary">Microsoft Office Add-in</h3>
                  <p className="text-xs text-text-tertiary">Word · Excel · PowerPoint</p>
                </div>
              </div>
              <ul className="space-y-2.5 text-sm text-text-secondary">
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-0.5">&#10003;</span>
                  <span>Enrich all documents in a SharePoint library</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-0.5">&#10003;</span>
                  <span>Trust panel in the ribbon for every file</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-0.5">&#10003;</span>
                  <span>Bulk audit across folders with one click</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-0.5">&#10003;</span>
                  <span>Review and approve directly in Office</span>
                </li>
              </ul>
            </div>

            {/* Google Workspace */}
            <div className="rounded-xl border border-border-subtle bg-surface-raised p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                  <span className="text-emerald-500 font-bold text-lg">G</span>
                </div>
                <div>
                  <h3 className="font-semibold text-text-primary">Google Workspace Add-on</h3>
                  <p className="text-xs text-text-tertiary">Docs · Sheets · Slides</p>
                </div>
              </div>
              <ul className="space-y-2.5 text-sm text-text-secondary">
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-0.5">&#10003;</span>
                  <span>Enrich all documents in a Drive folder</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-0.5">&#10003;</span>
                  <span>Trust sidebar for every document</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-0.5">&#10003;</span>
                  <span>Bulk audit from the sidebar</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="text-accent mt-0.5">&#10003;</span>
                  <span>Export enrichment reports</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* ── NATIVE VS SIDECAR ── */}
      <section className="py-16 px-6 bg-surface-raised/50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-3">
            Native embedding or sidecar — your files decide
          </h2>
          <p className="text-text-secondary text-center mb-10 max-w-xl mx-auto">
            AKF embeds trust metadata directly inside files that support it. For formats like audio and video, a lightweight JSON sidecar travels alongside.
          </p>

          <div className="grid sm:grid-cols-2 gap-6">
            <div className="rounded-xl border border-accent/20 bg-surface p-5">
              <h3 className="font-semibold text-text-primary mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-accent" />
                Native Embedding
              </h3>
              <p className="text-sm text-text-secondary mb-4">Metadata lives inside the file. Survives email, Slack, downloads.</p>
              <div className="flex flex-wrap gap-2">
                {['.docx', '.xlsx', '.pptx', '.pdf', '.md', '.html', '.json', '.png', '.py'].map((f) => (
                  <span key={f} className="text-xs font-mono px-2 py-1 rounded-md bg-accent/10 text-accent">{f}</span>
                ))}
              </div>
            </div>

            <div className="rounded-xl border border-amber-500/20 bg-surface p-5">
              <h3 className="font-semibold text-text-primary mb-3 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                Sidecar Files
              </h3>
              <p className="text-sm text-text-secondary mb-4">A <code className="text-xs bg-surface-raised px-1 py-0.5 rounded">.akf.json</code> companion file. Same metadata, zero modification to originals.</p>
              <div className="flex flex-wrap gap-2">
                {['.mp3', '.wav', '.mp4', '.mov', '.jpg', '.webp', '.tiff'].map((f) => (
                  <span key={f} className="text-xs font-mono px-2 py-1 rounded-md bg-amber-500/10 text-amber-600">{f}</span>
                ))}
                <span className="text-xs font-mono px-2 py-1 rounded-md bg-gray-500/10 text-text-tertiary">+ everything else</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── WHAT HAPPENS AFTER ── */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary mb-3">
            After enrichment, everything unlocks
          </h2>
          <p className="text-text-secondary mb-12 max-w-xl mx-auto">
            Enriched files participate in the full AKF ecosystem — audit, scan, detect, and track trust across your entire organization.
          </p>

          <div className="grid sm:grid-cols-3 gap-4 text-left">
            <div className="rounded-xl border border-border-subtle bg-surface-raised p-5">
              <div className="bg-gray-900 rounded-lg px-3 py-2 mb-3 inline-block">
                <code className="text-xs font-mono text-emerald-400">akf audit</code>
              </div>
              <h3 className="font-semibold text-text-primary mb-1 text-sm">Compliance Audit</h3>
              <p className="text-xs text-text-secondary">Run EU AI Act, HIPAA, SOX compliance checks across all enriched files.</p>
            </div>

            <div className="rounded-xl border border-border-subtle bg-surface-raised p-5">
              <div className="bg-gray-900 rounded-lg px-3 py-2 mb-3 inline-block">
                <code className="text-xs font-mono text-emerald-400">akf scan</code>
              </div>
              <h3 className="font-semibold text-text-primary mb-1 text-sm">Security Scan</h3>
              <p className="text-xs text-text-secondary">Detect unreviewed AI content, trust degradation, and 10 AI-specific threat classes.</p>
            </div>

            <div className="rounded-xl border border-border-subtle bg-surface-raised p-5">
              <div className="bg-gray-900 rounded-lg px-3 py-2 mb-3 inline-block">
                <code className="text-xs font-mono text-emerald-400">akf read</code>
              </div>
              <h3 className="font-semibold text-text-primary mb-1 text-sm">Trust Visibility</h3>
              <p className="text-xs text-text-secondary">Read trust metadata from any enriched file. Track review status and integrity.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-20 px-6 bg-surface-raised/50">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-text-primary mb-4">
            Your files are already there.<br />
            Make them <span className="text-accent">trust-aware</span>.
          </h2>
          <p className="text-text-secondary mb-8 max-w-lg mx-auto">
            One command brings every existing file into your trust framework. Full inventory. Integrity verification. Actionable review queue.
          </p>

          <div className="inline-block mb-8">
            <div className="bg-gray-900 rounded-xl px-8 py-4 border border-gray-700">
              <code className="text-lg font-mono">
                <span className="text-emerald-400">pip install</span>
                <span className="text-gray-300">{' '}akf</span>
              </code>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              to="/get-started"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-accent hover:bg-accent-hover text-white font-medium transition-colors"
            >
              Get Started
            </Link>
            <a
              href="https://github.com/HMAKT99/AKF"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-lg border border-border-subtle bg-surface hover:bg-surface-raised text-text-primary font-medium transition-colors"
            >
              View on GitHub
            </a>
          </div>
        </div>
      </section>
    </div>
  );
}
