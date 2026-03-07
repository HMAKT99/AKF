import { Link } from 'react-router-dom';

const formatGroups = [
  {
    category: 'Documents',
    formats: [
      { ext: '.docx', label: 'Word', method: 'Native' },
      { ext: '.pdf', label: 'PDF', method: 'Native' },
      { ext: '.xlsx', label: 'Excel', method: 'Native' },
      { ext: '.pptx', label: 'PowerPoint', method: 'Native' },
    ],
  },
  {
    category: 'Content',
    formats: [
      { ext: '.md', label: 'Markdown', method: 'Native' },
      { ext: '.html', label: 'HTML', method: 'Native' },
      { ext: '.json', label: 'JSON', method: 'Native' },
      { ext: '.csv', label: 'CSV', method: 'Sidecar' },
    ],
  },
  {
    category: 'Media',
    formats: [
      { ext: '.png', label: 'PNG', method: 'Native' },
      { ext: '.jpg', label: 'JPEG', method: 'Sidecar' },
      { ext: '.mp4', label: 'Video', method: 'Sidecar' },
      { ext: '.mp3', label: 'Audio', method: 'Sidecar' },
    ],
  },
  {
    category: 'Code',
    formats: [
      { ext: '.py', label: 'Python', method: 'Native' },
      { ext: '.js', label: 'JavaScript', method: 'Native' },
      { ext: '.ts', label: 'TypeScript', method: 'Native' },
      { ext: '.go', label: 'Go', method: 'Sidecar' },
    ],
  },
];

export default function ConvertPage() {
  return (
    <div className="pt-14">
      {/* ── HERO ── */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto">
          <Link to="/" className="text-sm text-accent hover:underline mb-10 inline-block">← Home</Link>

          <p className="text-xs font-mono text-accent tracking-widest uppercase mb-4">Convert to AKF</p>

          <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-text-primary leading-tight">
            Your organization has thousands of AI&#8209;generated files.
            <br />
            <span className="text-text-tertiary">None of them carry trust metadata.</span>
          </h1>

          <p className="mt-6 text-lg text-text-secondary max-w-2xl leading-relaxed">
            Regulators are asking for AI content inventories. Security teams need visibility.
            Compliance officers need audit trails. AKF converts your existing files — documents,
            images, spreadsheets, code, audio, video — into trust-aware assets with a single command.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-start sm:items-center gap-4">
            <div className="bg-gray-900 rounded-xl px-6 py-3.5 border border-gray-700">
              <code className="text-base sm:text-lg font-mono">
                <span className="text-gray-500">$ </span>
                <span className="text-emerald-400">akf enrich</span>
                <span className="text-gray-300"> ./your-files/</span>
              </code>
            </div>
            <span className="text-sm text-text-tertiary">Works on any folder, any OS, any content type</span>
          </div>
        </div>
      </section>

      {/* ── THE PROBLEM ── */}
      <section className="py-16 px-6 bg-surface-raised/50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-12">
            Without conversion, you're flying blind
          </h2>

          <div className="grid sm:grid-cols-3 gap-5">
            {[
              {
                stat: '0%',
                label: 'Visibility',
                desc: 'No way to know which files are AI-generated, which have been reviewed, or which are compliant.',
              },
              {
                stat: '0',
                label: 'Audit trail',
                desc: 'Auditors ask for your AI content inventory. Without metadata, you have nothing to show.',
              },
              {
                stat: '0',
                label: 'Tamper detection',
                desc: 'If a file is altered after creation, there\'s no integrity hash to flag the change.',
              },
            ].map((item) => (
              <div key={item.label} className="rounded-xl border border-border-subtle bg-surface p-5 text-center">
                <p className="text-3xl font-bold font-mono text-red-400/80 mb-1">{item.stat}</p>
                <p className="text-sm font-semibold text-text-primary mb-2">{item.label}</p>
                <p className="text-xs text-text-secondary leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── BEFORE / AFTER ── */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-3">
            One command transforms your file system
          </h2>
          <p className="text-text-secondary text-center mb-12 max-w-lg mx-auto">
            Every file gets cataloged, integrity-verified, and queued for review — without modifying your originals.
          </p>

          <div className="grid sm:grid-cols-2 gap-6">
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-red-400/60" />
                <p className="text-xs font-mono text-text-tertiary uppercase tracking-wider">Before</p>
              </div>
              <div className="rounded-xl border border-border-subtle bg-surface-raised p-5 h-full">
                <pre className="text-[13px] font-mono text-text-tertiary leading-relaxed whitespace-pre-wrap">{`quarterly-report.docx
hero-banner.png
forecast-model.xlsx
podcast-intro.mp3
product-demo.mp4
data-pipeline.py

No metadata. No integrity hash.
No way to audit or scan.
No idea what's AI-generated.`}</pre>
              </div>
            </div>

            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-accent" />
                <p className="text-xs font-mono text-accent uppercase tracking-wider">After <code className="text-[10px] bg-accent/10 px-1.5 py-0.5 rounded">akf enrich ./</code></p>
              </div>
              <div className="rounded-xl border border-accent/20 bg-surface-raised p-5 h-full">
                <pre className="text-[13px] font-mono text-text-secondary leading-relaxed whitespace-pre-wrap">{`quarterly-report.docx  `}<span className="text-emerald-500">SHA-256 ✓  embedded</span>{`
hero-banner.png       `}<span className="text-emerald-500">SHA-256 ✓  embedded</span>{`
forecast-model.xlsx   `}<span className="text-emerald-500">SHA-256 ✓  embedded</span>{`
podcast-intro.mp3     `}<span className="text-amber-500">SHA-256 ✓  sidecar</span>{`
product-demo.mp4      `}<span className="text-amber-500">SHA-256 ✓  sidecar</span>{`
data-pipeline.py      `}<span className="text-emerald-500">SHA-256 ✓  embedded</span>{`
`}
<span className="text-emerald-500 font-semibold">6 files enriched</span>{` · `}<span className="text-amber-500">2 sidecars</span>{`
`}<span className="text-accent">6 queued for review</span>{` · `}<span className="text-text-tertiary">0 errors</span></pre>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── WHAT EACH FILE GETS ── */}
      <section className="py-16 px-6 bg-surface-raised/50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-3">
            What every file receives
          </h2>
          <p className="text-text-secondary text-center mb-12 max-w-lg mx-auto">
            Real, verifiable foundations — not guesses. Every enriched file carries enough metadata
            to participate in audits, scans, and compliance checks.
          </p>

          <div className="grid sm:grid-cols-2 gap-4">
            <div className="rounded-xl border border-border-subtle bg-surface p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                  <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-text-primary">Integrity Hash</h3>
              </div>
              <p className="text-sm text-text-secondary leading-relaxed">
                SHA-256 cryptographic fingerprint. If the file is tampered with after enrichment, you'll know immediately.
              </p>
            </div>

            <div className="rounded-xl border border-border-subtle bg-surface p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                  <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m5.231 13.481L15 17.25m-4.5-15H5.625c-.621 0-1.125.504-1.125 1.125v16.5c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9zm3.75 11.625a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-text-primary">Format Classification</h3>
              </div>
              <p className="text-sm text-text-secondary leading-relaxed">
                File type, structure, and embedding strategy automatically detected. Native embedding where possible, sidecar where not.
              </p>
            </div>

            <div className="rounded-xl border border-border-subtle bg-surface p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                  <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 6.75h12M8.25 12h12m-12 5.25h12M3.75 6.75h.007v.008H3.75V6.75zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zM3.75 12h.007v.008H3.75V12zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm-.375 5.25h.007v.008H3.75v-.008zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z" />
                  </svg>
                </div>
                <h3 className="font-semibold text-text-primary">Review Queue</h3>
              </div>
              <p className="text-sm text-text-secondary leading-relaxed">
                Every file is marked <code className="text-xs bg-surface-raised px-1.5 py-0.5 rounded text-amber-500">unreviewed</code> — creating a structured,
                prioritizable queue for your team instead of an impossible mountain.
              </p>
            </div>

            <div className="rounded-xl border border-border-subtle bg-surface p-5">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                  <svg className="w-4 h-4 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776" />
                  </svg>
                </div>
                <h3 className="font-semibold text-text-primary">Complete Inventory</h3>
              </div>
              <p className="text-sm text-text-secondary leading-relaxed">
                Every file cataloged and visible to <code className="text-xs bg-surface-raised px-1.5 py-0.5 rounded text-emerald-500">akf audit</code> and{' '}
                <code className="text-xs bg-surface-raised px-1.5 py-0.5 rounded text-emerald-500">akf scan</code>.
                The foundation for any AI governance program.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── SUPPORTED FORMATS ── */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-3">
            20+ formats supported
          </h2>
          <p className="text-text-secondary text-center mb-12 max-w-lg mx-auto">
            AKF embeds metadata natively inside files that support it. For everything else,
            a lightweight <code className="text-xs bg-surface-raised px-1.5 py-0.5 rounded">.akf.json</code> sidecar
            travels alongside — same metadata, zero modification to originals.
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            {formatGroups.map((group) => (
              <div key={group.category}>
                <p className="text-xs font-mono text-text-tertiary uppercase tracking-wider mb-3">{group.category}</p>
                <div className="flex flex-col gap-2">
                  {group.formats.map((f) => (
                    <div key={f.ext} className="flex items-center justify-between rounded-lg border border-border-subtle bg-surface-raised px-3 py-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-mono font-semibold text-text-primary">{f.ext}</span>
                        <span className="text-xs text-text-tertiary">{f.label}</span>
                      </div>
                      <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${
                        f.method === 'Native'
                          ? 'bg-accent/10 text-accent'
                          : 'bg-amber-500/10 text-amber-600'
                      }`}>{f.method}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW TO CONVERT ── */}
      <section className="py-16 px-6 bg-surface-raised/50">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-3">
            Two paths to conversion
          </h2>
          <p className="text-text-secondary text-center mb-12">
            Choose the approach that fits your workflow.
          </p>

          <div className="grid sm:grid-cols-2 gap-6">
            {/* CLI */}
            <div className="rounded-xl border border-border-subtle bg-surface overflow-hidden">
              <div className="px-6 pt-6 pb-4">
                <p className="text-xs font-mono text-accent uppercase tracking-wider mb-2">For developers &amp; DevOps</p>
                <h3 className="text-xl font-bold text-text-primary mb-1">CLI</h3>
                <p className="text-sm text-text-secondary">Any folder. Any OS. Any content type.</p>
              </div>
              <div className="bg-gray-900 border-t border-gray-700">
                <div className="flex items-center gap-1.5 px-4 py-2 border-b border-gray-800">
                  <span className="w-2 h-2 rounded-full bg-[#ff5f57]" />
                  <span className="w-2 h-2 rounded-full bg-[#febc2e]" />
                  <span className="w-2 h-2 rounded-full bg-[#28c840]" />
                </div>
                <pre className="px-4 py-4 text-[13px] font-mono text-gray-300 leading-relaxed overflow-x-auto"><span className="text-gray-500"># Enrich a folder of documents</span>{'\n'}<span className="text-emerald-400">akf enrich</span> ~/Documents/reports/{'\n\n'}<span className="text-gray-500"># Preview changes first</span>{'\n'}<span className="text-emerald-400">akf enrich</span> ./data/ <span className="text-sky-400">--dry-run</span>{'\n\n'}<span className="text-gray-500"># Then audit for compliance</span>{'\n'}<span className="text-emerald-400">akf audit</span> ./reports/ <span className="text-sky-400">--framework</span> eu-ai-act</pre>
              </div>
              <div className="px-6 py-4 flex gap-4 text-xs text-text-tertiary">
                <span><span className="font-semibold text-text-secondary">20+</span> formats</span>
                <span><span className="font-semibold text-text-secondary">--parallel</span> support</span>
                <span><span className="font-semibold text-text-secondary">--dry-run</span> preview</span>
              </div>
            </div>

            {/* Office / Workspace */}
            <div className="rounded-xl border border-border-subtle bg-surface overflow-hidden">
              <div className="px-6 pt-6 pb-4">
                <p className="text-xs font-mono text-accent uppercase tracking-wider mb-2">For teams &amp; knowledge workers</p>
                <h3 className="text-xl font-bold text-text-primary mb-1">Office &amp; Workspace</h3>
                <p className="text-sm text-text-secondary">No terminal required.</p>
              </div>
              <div className="px-6 py-5 border-t border-border-subtle">
                <div className="space-y-5">
                  {/* Microsoft */}
                  <div>
                    <div className="flex items-center gap-2.5 mb-2.5">
                      <div className="w-7 h-7 rounded bg-blue-500/10 flex items-center justify-center">
                        <span className="text-blue-500 font-bold text-xs">M</span>
                      </div>
                      <span className="text-sm font-semibold text-text-primary">Microsoft Office Add-in</span>
                      <span className="text-[10px] text-text-tertiary">Word · Excel · PowerPoint</span>
                    </div>
                    <ul className="space-y-1.5 text-sm text-text-secondary ml-9">
                      <li className="flex items-center gap-2">
                        <span className="text-accent text-xs">&#10003;</span>
                        Trust panel in the ribbon
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="text-accent text-xs">&#10003;</span>
                        Enrich and audit from SharePoint
                      </li>
                    </ul>
                  </div>

                  {/* Divider */}
                  <div className="border-t border-border-subtle" />

                  {/* Google */}
                  <div>
                    <div className="flex items-center gap-2.5 mb-2.5">
                      <div className="w-7 h-7 rounded bg-emerald-500/10 flex items-center justify-center">
                        <span className="text-emerald-500 font-bold text-xs">G</span>
                      </div>
                      <span className="text-sm font-semibold text-text-primary">Google Workspace Add-on</span>
                      <span className="text-[10px] text-text-tertiary">Docs · Sheets · Slides</span>
                    </div>
                    <ul className="space-y-1.5 text-sm text-text-secondary ml-9">
                      <li className="flex items-center gap-2">
                        <span className="text-accent text-xs">&#10003;</span>
                        Trust sidebar for every document
                      </li>
                      <li className="flex items-center gap-2">
                        <span className="text-accent text-xs">&#10003;</span>
                        Enrich and audit from Drive
                      </li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── AFTER CONVERSION ── */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary mb-3">
            After conversion, everything unlocks
          </h2>
          <p className="text-text-secondary mb-12 max-w-lg mx-auto">
            Converted files participate in the full AKF ecosystem — audit, scan, and detect across your entire organization.
          </p>

          <div className="grid sm:grid-cols-3 gap-4 text-left">
            <div className="rounded-xl border border-border-subtle bg-surface-raised p-5">
              <code className="text-xs font-mono text-emerald-400 bg-gray-900 px-2.5 py-1 rounded-md">akf audit</code>
              <h3 className="font-semibold text-text-primary mt-3 mb-1.5 text-sm">Compliance</h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                EU AI Act, HIPAA, SOX, GDPR — run compliance checks across every converted file. Generate audit-ready reports.
              </p>
            </div>

            <div className="rounded-xl border border-border-subtle bg-surface-raised p-5">
              <code className="text-xs font-mono text-emerald-400 bg-gray-900 px-2.5 py-1 rounded-md">akf scan</code>
              <h3 className="font-semibold text-text-primary mt-3 mb-1.5 text-sm">Security</h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                10 AI-specific detection classes. Flag unreviewed content, trust degradation, hallucination risk, and provenance gaps.
              </p>
            </div>

            <div className="rounded-xl border border-border-subtle bg-surface-raised p-5">
              <code className="text-xs font-mono text-emerald-400 bg-gray-900 px-2.5 py-1 rounded-md">akf read</code>
              <h3 className="font-semibold text-text-primary mt-3 mb-1.5 text-sm">Visibility</h3>
              <p className="text-xs text-text-secondary leading-relaxed">
                Read trust metadata from any file. Track review progress. Verify integrity. Full organizational visibility.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-20 px-6 bg-surface-raised/50">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-text-primary mb-4">
            Your files are already there.<br />
            Give them <span className="text-accent">trust metadata</span>.
          </h2>
          <p className="text-text-secondary mb-8 max-w-lg mx-auto">
            One command. Full inventory. Integrity verification. Actionable review queue.
            The foundation for AI governance — in minutes.
          </p>

          <div className="inline-flex flex-col sm:flex-row gap-3 mb-8">
            <div className="bg-gray-900 rounded-xl px-6 py-3.5 border border-gray-700">
              <code className="text-base font-mono">
                <span className="text-gray-500">python </span>
                <span className="text-emerald-400">pip install</span>
                <span className="text-gray-300"> akf</span>
              </code>
            </div>
            <div className="bg-gray-900 rounded-xl px-6 py-3.5 border border-gray-700">
              <code className="text-base font-mono">
                <span className="text-gray-500">npm </span>
                <span className="text-emerald-400">npm install</span>
                <span className="text-gray-300"> akf-format</span>
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

          <p className="mt-6 text-xs text-text-tertiary">Open format · MIT Licensed</p>
        </div>
      </section>
    </div>
  );
}
