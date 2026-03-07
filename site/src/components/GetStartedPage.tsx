import { useState } from 'react';
import { Link } from 'react-router-dom';

/* ── Copy command button ── */
function CopyCommand({ command }: { command: string }) {
  const [copied, setCopied] = useState(false);
  function handleCopy() {
    navigator.clipboard.writeText(command).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }
  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-3 px-4 py-2.5 rounded-lg bg-surface-raised border border-border-subtle font-mono text-sm hover:border-text-tertiary transition-colors cursor-pointer group"
      aria-label={`Copy "${command}" to clipboard`}
    >
      <span className="text-text-tertiary select-none">$</span>
      <span className="text-text-primary">{command}</span>
      <span className="text-text-tertiary opacity-0 group-hover:opacity-100 transition-opacity ml-1">
        {copied ? (
          <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        )}
      </span>
    </button>
  );
}

/* ── Persona tab data ── */
interface PersonaTab {
  id: string;
  label: string;
  icon: React.ReactNode;
  pain: string;
  snippet: string;
  snippetLang: string;
  outcome: string;
}

const personaTabs: PersonaTab[] = [
  {
    id: 'workers',
    label: 'Knowledge Workers',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
    pain: '"Is this report real, or did an AI hallucinate it?"',
    snippet: `# Open any document and check trust
akf read quarterly-report.docx

# Trust: 0.92 | Model: GPT-4o | Reviewed: Yes`,
    snippetLang: 'bash',
    outcome: 'See trust scores, model provenance, and human-review status for every document you open.',
  },
  {
    id: 'agents',
    label: 'AI Agents',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25z" />
      </svg>
    ),
    pain: '"Our agent pipeline ships content with zero provenance."',
    snippet: `from akf import stamp_file
stamp_file("output.pdf",
  confidence=0.95, model="gpt-4o",
  source="internal-kb")`,
    snippetLang: 'python',
    outcome: 'Every file your agent produces carries embedded trust metadata automatically.',
  },
  {
    id: 'security',
    label: 'Security & CISOs',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
    pain: '"Traditional DLP can\'t catch AI-specific threats."',
    snippet: `# Scan for 10 classes of AI content risk
akf scan --recursive ./shared-drive/

# 3 files flagged: unreviewed AI content`,
    snippetLang: 'bash',
    outcome: 'Detect unreviewed AI content, trust degradation, and classification downgrade across your org.',
  },
  {
    id: 'governance',
    label: 'Governance',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.125 2.25h-4.5c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125v-9M10.125 2.25h.375a9 9 0 019 9v.375M10.125 2.25A3.375 3.375 0 0113.5 5.625v1.5c0 .621.504 1.125 1.125 1.125h1.5a3.375 3.375 0 013.375 3.375M9 15l2.25 2.25L15 12" />
      </svg>
    ),
    pain: '"We can\'t prove AI transparency to regulators."',
    snippet: `# Generate compliance report for EU AI Act
akf audit --regulation eu_ai_act ./reports/

# 47 files audited, 100% compliant`,
    snippetLang: 'bash',
    outcome: 'Machine-readable audit trails that satisfy EU AI Act, HIPAA, SOX, and GDPR requirements.',
  },
  {
    id: 'developers',
    label: 'Developers',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
      </svg>
    ),
    pain: '"Adding trust metadata means weeks of custom infrastructure."',
    snippet: `import { normalize } from 'akf-format';
const stamp = normalize({
  c: 0.9, t: 'analysis',
  src: 'internal-kb', model: 'claude-4' });`,
    snippetLang: 'typescript',
    outcome: 'pip install or npm install, then one function call. No infra, no API keys, no config.',
  },
];

/* ── Compliance frameworks ── */
const frameworks = [
  { name: 'EU AI Act', desc: 'Transparency & human oversight' },
  { name: 'HIPAA', desc: 'Healthcare AI audit trails' },
  { name: 'SOX', desc: 'Financial AI controls' },
  { name: 'GDPR', desc: 'Data provenance tracking' },
  { name: 'ISO 42001', desc: 'AI management systems' },
  { name: 'NIST AI RMF', desc: 'Risk management framework' },
];

/* ── Security detections ── */
const detections = [
  'Unreviewed AI content',
  'Trust score degradation',
  'Classification downgrade',
  'Provenance gaps',
  'Model hallucination risk',
  'Knowledge laundering',
  'Excessive AI concentration',
  'Ungrounded claims',
  'Stale claims',
  'Trust degradation chain',
];

/* ── Simple syntax highlight ── */
function highlightCode(code: string, lang: string): string {
  if (lang === 'bash') {
    return code
      .replace(/(#.*)/g, '<span class="text-gray-500">$1</span>')
      .replace(/("(?:[^"\\]|\\.)*")/g, '<span class="text-amber-300">$1</span>')
      .replace(/(--[\w-]+)/g, '<span class="text-sky-400">$1</span>')
      .replace(/^(\s*)(akf|pip|npm)/gm, '$1<span class="text-emerald-400">$2</span>');
  }
  if (lang === 'python') {
    return code
      .replace(/(#.*)/g, '<span class="text-gray-500">$1</span>')
      .replace(/("(?:[^"\\]|\\.)*")/g, '<span class="text-amber-300">$1</span>')
      .replace(/\b(from|import|def|class|return|if|else|for|in|with|as|True|False|None)\b/g, '<span class="text-purple-400">$1</span>')
      .replace(/\b(\d+\.?\d*)\b/g, '<span class="text-emerald-400">$1</span>');
  }
  if (lang === 'typescript') {
    return code
      .replace(/(\/\/.*)/g, '<span class="text-gray-500">$1</span>')
      .replace(/('(?:[^'\\]|\\.)*')/g, '<span class="text-amber-300">$1</span>')
      .replace(/\b(import|from|const|let|var|function|return|export|type|interface)\b/g, '<span class="text-purple-400">$1</span>')
      .replace(/\b(\d+\.?\d*)\b/g, '<span class="text-emerald-400">$1</span>');
  }
  return code;
}

/* ── Trust score color ── */
function trustColor(score: number): string {
  if (score >= 0.7) return 'text-emerald-500';
  if (score >= 0.4) return 'text-amber-500';
  return 'text-red-500';
}

function trustBg(score: number): string {
  if (score >= 0.7) return 'bg-emerald-500/10 border-emerald-500/20';
  if (score >= 0.4) return 'bg-amber-500/10 border-amber-500/20';
  return 'bg-red-500/10 border-red-500/20';
}

/* ══════════════════════════════════════════
   Main component
   ══════════════════════════════════════════ */
export default function GetStartedPage() {
  const [activeTab, setActiveTab] = useState(0);

  return (
    <div className="pt-24 pb-20 px-6">
      <div className="max-w-4xl mx-auto">

        {/* ── SECTION 1: Hero hook ── */}
        <section className="text-center mb-20">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-accent text-sm font-medium mb-6">
            <span className="w-1.5 h-1.5 rounded-full bg-accent" />
            Get started in 60 seconds
          </div>
          <h1 className="text-4xl sm:text-5xl font-bold tracking-tight leading-[1.1]">
            Start trusting your AI output
            <br />
            <span className="text-accent">in 60 seconds.</span>
          </h1>
          <p className="mt-6 text-lg text-text-secondary max-w-2xl mx-auto">
            One install. Trust scores, evidence, and provenance embed natively into every file your AI produces.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-3">
            <CopyCommand command="pip install akf" />
            <CopyCommand command="npm install akf-format" />
          </div>
        </section>

        {/* ── SECTION 2: Pick Your Path ── */}
        <section className="mb-20">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-2">Pick Your Path</h2>
          <p className="text-text-secondary text-center mb-8">Choose your role. See your first win.</p>

          {/* Tab pills */}
          <div className="flex flex-wrap justify-center gap-2 mb-8">
            {personaTabs.map((tab, i) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(i)}
                className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors cursor-pointer ${
                  activeTab === i
                    ? 'bg-accent text-white'
                    : 'bg-surface-raised border border-border-subtle text-text-secondary hover:text-text-primary hover:border-text-tertiary'
                }`}
              >
                {tab.icon}
                <span className="hidden sm:inline">{tab.label}</span>
              </button>
            ))}
          </div>

          {/* Active tab content */}
          {(() => {
            const tab = personaTabs[activeTab];
            return (
              <div className="rounded-xl border border-border-subtle bg-surface-raised p-6 sm:p-8">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-lg bg-accent/10 text-accent flex items-center justify-center">
                    {tab.icon}
                  </div>
                  <h3 className="text-xl font-semibold text-text-primary">{tab.label}</h3>
                </div>

                {/* Pain point */}
                <p className="text-text-secondary italic mb-6">{tab.pain}</p>

                {/* Code snippet */}
                <div className="rounded-lg overflow-hidden border border-gray-800 mb-6">
                  <div className="flex items-center gap-2 px-4 py-2 bg-gray-800 border-b border-gray-700">
                    <span className="w-2.5 h-2.5 rounded-full bg-red-500/80" />
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80" />
                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80" />
                    <span className="text-xs text-gray-400 ml-2 font-mono">{tab.snippetLang}</span>
                  </div>
                  <pre className="p-4 text-[13px] leading-relaxed overflow-x-auto bg-gray-900 text-gray-300 font-mono">
                    <code dangerouslySetInnerHTML={{ __html: highlightCode(tab.snippet, tab.snippetLang) }} />
                  </pre>
                </div>

                {/* Outcome */}
                <div className="flex items-start gap-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20 p-4">
                  <svg className="w-5 h-5 text-emerald-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                  <p className="text-sm text-text-primary">{tab.outcome}</p>
                </div>
              </div>
            );
          })()}
        </section>

        {/* ── SECTION 3: The Format ── */}
        <section className="mb-20">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-2">The Format</h2>
          <p className="text-text-secondary text-center mb-8">15 tokens. That's it.</p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Without AKF */}
            <div className="rounded-xl border border-border-subtle bg-surface-raised p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-red-400" />
                <span className="text-sm font-semibold text-text-primary">Without AKF</span>
              </div>
              <div className="rounded-lg bg-gray-900 border border-gray-800 p-4 font-mono text-[13px] leading-relaxed text-gray-300">
                <div className="text-gray-500"># quarterly-report.md</div>
                <div className="mt-2">Revenue grew 23% YoY...</div>
                <div className="mt-1">Customer retention improved...</div>
                <div className="mt-3 text-gray-500">---</div>
                <div className="text-red-400 text-xs mt-2">Who wrote this? AI or human?</div>
                <div className="text-red-400 text-xs">How confident should I be?</div>
                <div className="text-red-400 text-xs">What sources back this up?</div>
              </div>
            </div>

            {/* With AKF */}
            <div className="rounded-xl border border-accent/30 bg-surface-raised p-5">
              <div className="flex items-center gap-2 mb-3">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="text-sm font-semibold text-text-primary">With AKF</span>
              </div>
              <div className="rounded-lg bg-gray-900 border border-gray-800 p-4 font-mono text-[13px] leading-relaxed text-gray-300">
                <div className="text-gray-500"># quarterly-report.md</div>
                <div className="mt-2">Revenue grew 23% YoY...</div>
                <div className="mt-1">Customer retention improved...</div>
                <div className="mt-3 text-gray-500">---</div>
                <div className="mt-2">
                  <span className="text-sky-400">confidence</span>: <span className="text-emerald-400">0.92</span>
                </div>
                <div>
                  <span className="text-sky-400">model</span>: <span className="text-amber-300">"gpt-4o"</span>
                </div>
                <div>
                  <span className="text-sky-400">source</span>: <span className="text-amber-300">"finance-db"</span>
                </div>
                <div>
                  <span className="text-sky-400">reviewed</span>: <span className="text-purple-400">true</span>
                </div>
              </div>
            </div>
          </div>

          {/* Trust score color guide */}
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            {[
              { score: 0.92, label: 'High trust' },
              { score: 0.55, label: 'Needs review' },
              { score: 0.2, label: 'Low confidence' },
            ].map((item) => (
              <div
                key={item.label}
                className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg border text-sm ${trustBg(item.score)}`}
              >
                <span className={`font-mono font-semibold ${trustColor(item.score)}`}>{item.score}</span>
                <span className="text-text-secondary">{item.label}</span>
              </div>
            ))}
          </div>
        </section>

        {/* ── SECTION 4: Enterprise Ready ── */}
        <section className="mb-20">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary text-center mb-2">Enterprise Ready</h2>
          <p className="text-text-secondary text-center mb-8">Compliance and security, built in.</p>

          {/* Compliance frameworks */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-8">
            {frameworks.map((fw) => (
              <div key={fw.name} className="rounded-lg border border-border-subtle bg-surface-raised p-4">
                <div className="text-sm font-semibold text-text-primary">{fw.name}</div>
                <div className="text-xs text-text-secondary mt-1">{fw.desc}</div>
              </div>
            ))}
          </div>

          {/* Security detections */}
          <div className="rounded-xl border border-border-subtle bg-surface-raised p-6">
            <h3 className="text-lg font-semibold text-text-primary mb-4">10 AI-specific security detections</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {detections.map((d) => (
                <div key={d} className="flex items-center gap-2 text-sm text-text-secondary">
                  <svg className="w-4 h-4 text-accent shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75" />
                  </svg>
                  {d}
                </div>
              ))}
            </div>
          </div>

          {/* CLI commands */}
          <div className="mt-6 flex flex-wrap justify-center gap-3">
            {['akf audit', 'akf scan', 'akf stamp'].map((cmd) => (
              <code
                key={cmd}
                className="px-3 py-1.5 rounded-md bg-surface-raised border border-border-subtle text-xs font-mono text-accent"
              >
                {cmd}
              </code>
            ))}
          </div>
        </section>

        {/* ── SECTION 5: Download Brochure ── */}
        <section className="mb-20">
          <div className="rounded-xl border border-border-subtle bg-surface-raised p-8 text-center">
            <div className="w-12 h-12 rounded-lg bg-accent/10 text-accent flex items-center justify-center mx-auto mb-4">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m.75 12l3 3m0 0l3-3m-3 3v-6m-1.5-9H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-text-primary mb-2">Download the Brochure</h2>
            <p className="text-text-secondary mb-6 max-w-lg mx-auto">
              Get the full getting started guide with all 5 persona walkthroughs, CLI reference, compliance frameworks, and code examples.
            </p>
            <a
              href="https://github.com/HMAKT99/AKF/blob/main/docs/getting-started-guide.md"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-accent hover:bg-accent-hover text-white font-medium text-sm transition-colors"
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
              </svg>
              Download Getting Started Guide
            </a>
          </div>
        </section>

        {/* ── SECTION 6: Get Started Now ── */}
        <section className="text-center">
          <h2 className="text-2xl sm:text-3xl font-bold text-text-primary mb-2">Get Started Now</h2>
          <p className="text-text-secondary mb-8">Pick your language and go.</p>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-3 mb-8">
            <CopyCommand command="pip install akf" />
            <CopyCommand command="npm install akf-format" />
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3">
            <a
              href="https://github.com/HMAKT99/AKF"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-accent hover:bg-accent-hover text-white font-medium text-sm transition-colors"
            >
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
              </svg>
              GitHub
            </a>
            <a
              href="https://www.npmjs.com/package/akf-format"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-surface-raised border border-border-subtle hover:border-accent/40 text-text-primary font-medium text-sm transition-colors"
            >
              npm
            </a>
          </div>

          <div className="mt-12">
            <Link to="/" className="text-sm text-accent hover:underline">&larr; Back to home</Link>
          </div>
        </section>

      </div>
    </div>
  );
}
