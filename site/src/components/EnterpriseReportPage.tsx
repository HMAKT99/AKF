import { useState } from 'react';
import { Link } from 'react-router-dom';
import SectionHeading from '../ui/SectionHeading';
import CodeBlock from '../ui/CodeBlock';

/* ── Copy button ── */
function CopyCmd({ cmd }: { cmd: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(cmd).then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        }).catch(() => {});
      }}
      aria-label={`Copy "${cmd}" to clipboard`}
      className="flex items-center gap-3 px-4 py-2.5 rounded-lg bg-surface-raised border border-border-subtle font-mono text-sm hover:border-text-tertiary transition-colors cursor-pointer group"
    >
      <span className="text-text-tertiary select-none">$</span>
      <span className="text-text-primary">{cmd}</span>
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

/* ── Hero ── */
function Hero() {
  return (
    <section className="pt-28 pb-16 px-6 text-center">
      <div className="max-w-3xl mx-auto">
        <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold bg-accent/10 text-accent mb-6">
          Free &amp; Open Source
        </span>
        <h1 className="text-4xl sm:text-5xl font-bold tracking-tight text-text-primary mb-6">
          AI Governance in One Command
        </h1>
        <p className="text-lg text-text-secondary max-w-2xl mx-auto mb-10">
          Know exactly what AI built, at what confidence, from which model — across every file in your project.
          No SaaS, no agents, no cost. Just <code className="text-accent whitespace-nowrap">pip install akf</code>.
        </p>
        <div className="max-w-md mx-auto">
          <CodeBlock
            code={`$ akf report .

# AI Governance Report

| Metric         | Value          |
|----------------|----------------|
| Total files    | 12             |
| Total claims   | 47             |
| Average trust  | 0.87           |
| Security grade | A (9.1/10)     |
| Compliance     | 92%            |
| Quality score  | 0.91           |`}
            language="bash"
            filename="terminal"
          />
        </div>
      </div>
    </section>
  );
}

/* ── KPI Dashboard ── */
const kpis = [
  { label: 'Files Scanned', value: '12', color: 'text-text-primary' },
  { label: 'Total Claims', value: '47', color: 'text-text-primary' },
  { label: 'Avg Trust', value: '0.87', color: 'text-emerald-500' },
  { label: 'Security Grade', value: 'A', color: 'text-emerald-500' },
  { label: 'Compliance', value: '92%', color: 'text-sky-400' },
  { label: 'Quality Score', value: '0.91', color: 'text-purple-400' },
];

function KPIDashboard() {
  return (
    <section className="py-16 px-6">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="Your project's AI health at a glance"
          subtitle="Trust, security, compliance, and model usage — computed from the metadata already in your files."
        />
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
          {kpis.map((k) => (
            <div
              key={k.label}
              className="rounded-xl border border-border-subtle bg-surface-raised p-4 text-center"
            >
              <div className={`text-2xl font-bold ${k.color}`}>{k.value}</div>
              <div className="text-xs text-text-secondary mt-1">{k.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── Format Showcase ── */
const formatTabs = [
  {
    label: 'Markdown',
    code: `# AI Governance Report

| Metric          | Value              |
|-----------------|--------------------|
| Total files     | 12                 |
| Average trust   | 0.87               |
| Security grade  | **A** (9.1/10)     |
| Compliance rate  | 92%                |

## Trust Distribution
  High     [████████████████████] 38
  Moderate [████░░░░░░░░░░░░░░░░]  7
  Low      [█░░░░░░░░░░░░░░░░░░░]  2`,
    lang: 'markdown',
  },
  {
    label: 'HTML',
    code: `<!-- Print-ready: Cmd+P produces clean PDF -->
<!DOCTYPE html>
<html lang="en">
<head>
  <style>
    .grid { display: grid; grid-template-columns: repeat(6,1fr); }
    .card { background: #f9fafb; border-radius: 8px; }
    @media print {
      .card { break-inside: avoid; }
      body  { color: #000; }
    }
  </style>
</head>
<body>
  <h1>AI Governance Report</h1>
  <div class="grid">
    <div class="card">12 Files</div>
    ...
  </div>
</body>
</html>`,
    lang: 'bash',
  },
  {
    label: 'CSV',
    code: `file,claims,avg_trust,ai_claims,human_claims,security_grade,security_score,compliant,classification,detections,critical,high,quality_score
report-q4.akf,23,0.92,18,5,A,9.4,True,internal,0,0,0,0.95
analysis.akf,8,0.71,8,0,B,7.2,True,public,1,0,1,0.82
memo.akf,3,0.45,1,2,C,5.1,False,confidential,2,1,1,0.61`,
    lang: 'plain',
  },
  {
    label: 'PDF',
    code: `# Programmatic PDF (optional fpdf2 dependency)
pip install akf[report]
akf report /data/ --format pdf -o governance.pdf

# Or print-ready HTML → PDF (zero deps)
akf report /data/ --format html -o report.html
# Open in browser → Cmd+P → Save as PDF`,
    lang: 'bash',
  },
];

function FormatShowcase() {
  const [active, setActive] = useState(0);
  return (
    <section className="py-16 px-6 bg-surface-raised/50">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="Export in any format"
          subtitle="Markdown for devs, HTML for dashboards, CSV for analysts, PDF for the board."
        />
        <div className="flex gap-1 mb-6 bg-surface-overlay rounded-lg p-1 inline-flex">
          {formatTabs.map((tab, i) => (
            <button
              key={tab.label}
              onClick={() => setActive(i)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                active === i
                  ? 'bg-accent text-white'
                  : 'text-text-secondary hover:text-text-primary'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
        <CodeBlock
          code={formatTabs[active].code}
          language={formatTabs[active].lang}
          filename={formatTabs[active].label === 'PDF' ? 'terminal' : `report.${formatTabs[active].label.toLowerCase()}`}
        />
      </div>
    </section>
  );
}

/* ── USP Cards ── */
const usps = [
  {
    title: 'Zero-config governance',
    desc: 'akf report . scans everything — no setup, no config files, no SaaS subscription.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    title: 'Compliance-ready',
    desc: 'Pre-mapped to EU AI Act, SOX, HIPAA, and NIST frameworks out of the box.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
  },
  {
    title: 'Model visibility',
    desc: 'See exactly which AI models you\'re using — GPT-4o, Claude, Gemini — and how much.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
  {
    title: 'Risk heatmap',
    desc: 'Critical and high-severity detections surfaced across your entire corpus instantly.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M15.362 5.214A8.252 8.252 0 0112 21 8.25 8.25 0 016.038 7.048 8.287 8.287 0 009 9.6a8.983 8.983 0 013.361-6.867 8.21 8.21 0 003 2.48z" />
      </svg>
    ),
  },
  {
    title: 'Export anywhere',
    desc: 'PDF for the board, CSV for analysts, JSON for your SIEM, Markdown for docs.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" />
      </svg>
    ),
  },
  {
    title: 'No vendor lock-in',
    desc: 'Runs locally, open standard, no cloud dependency. Your data never leaves your infrastructure.',
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 10.5V6.75a4.5 4.5 0 119 0v3.75M3.75 21.75h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H3.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z" />
      </svg>
    ),
  },
];

function USPCards() {
  return (
    <section className="py-16 px-6">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="Why this matters"
          subtitle="AI governance shouldn't require a six-figure budget and a six-month rollout."
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {usps.map((u) => (
            <div
              key={u.title}
              className="rounded-xl border border-border-subtle bg-surface-raised p-5 flex flex-col gap-3"
            >
              <div className="w-9 h-9 rounded-lg bg-accent/10 text-accent flex items-center justify-center">
                {u.icon}
              </div>
              <h3 className="text-sm font-semibold text-text-primary">{u.title}</h3>
              <p className="text-xs text-text-secondary leading-relaxed">{u.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ── Comparison Table ── */
const compRows = [
  { feature: 'Setup time', manual: 'Weeks', saas: 'Days', akf: 'Seconds' },
  { feature: 'Annual cost', manual: '$200K+', saas: '$50K+', akf: 'Free / OSS' },
  { feature: 'Runs locally', manual: 'Yes', saas: 'No', akf: 'Yes' },
  { feature: 'Compliance mapping', manual: 'Manual', saas: 'Partial', akf: 'Built-in' },
  { feature: 'Model visibility', manual: 'None', saas: 'Limited', akf: 'Full' },
  { feature: 'Export formats', manual: 'PDF only', saas: 'Varies', akf: 'MD / HTML / CSV / PDF / JSON' },
  { feature: 'Vendor lock-in', manual: 'N/A', saas: 'High', akf: 'None' },
];

function ComparisonTable() {
  return (
    <section className="py-16 px-6 bg-surface-raised/50">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="How AKF Report compares"
          subtitle="You shouldn't need a $50K GRC contract to know what AI built in your repo."
        />
        <div className="overflow-x-auto">
          <table className="w-full text-sm border-collapse">
            <thead>
              <tr className="border-b border-border-subtle">
                <th className="text-left py-3 px-4 text-text-secondary font-medium">Feature</th>
                <th className="text-center py-3 px-4 text-text-secondary font-medium">Manual Audit</th>
                <th className="text-center py-3 px-4 text-text-secondary font-medium">SaaS GRC</th>
                <th className="text-center py-3 px-4 text-accent font-semibold">AKF Report</th>
              </tr>
            </thead>
            <tbody>
              {compRows.map((r) => (
                <tr key={r.feature} className="border-b border-border-subtle/50">
                  <td className="py-3 px-4 text-text-primary font-medium">{r.feature}</td>
                  <td className="py-3 px-4 text-center text-text-secondary">{r.manual}</td>
                  <td className="py-3 px-4 text-center text-text-secondary">{r.saas}</td>
                  <td className="py-3 px-4 text-center text-text-primary font-medium">{r.akf}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}

/* ── CLI Quick Start ── */
function CLIQuickStart() {
  return (
    <section className="py-16 px-6">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="Get started in seconds"
          subtitle="One install, one command. Every format."
        />
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 max-w-2xl mx-auto">
          <div>
            <p className="text-xs text-text-secondary mb-2 font-medium">Markdown (default)</p>
            <CopyCmd cmd="akf report ." />
          </div>
          <div>
            <p className="text-xs text-text-secondary mb-2 font-medium">HTML (print-ready)</p>
            <CopyCmd cmd="akf report . --format html -o report.html" />
          </div>
          <div>
            <p className="text-xs text-text-secondary mb-2 font-medium">CSV (for analysts)</p>
            <CopyCmd cmd="akf report . --format csv -o report.csv" />
          </div>
          <div>
            <p className="text-xs text-text-secondary mb-2 font-medium">PDF (for the board)</p>
            <CopyCmd cmd="akf report . --format pdf -o report.pdf" />
          </div>
          <div>
            <p className="text-xs text-text-secondary mb-2 font-medium">JSON (for SIEM)</p>
            <CopyCmd cmd="akf report . --format json -o report.json" />
          </div>
          <div>
            <p className="text-xs text-text-secondary mb-2 font-medium">Install PDF support</p>
            <CopyCmd cmd="pip install akf[report]" />
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── CI/CD Integration ── */
function CICDIntegration() {
  return (
    <section className="py-16 px-6 bg-surface-raised/50">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="Automate with CI/CD"
          subtitle="Add governance checks to every pull request. Block merges that fail trust thresholds."
        />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* GitHub Actions workflow */}
          <div>
            <p className="text-xs text-text-secondary mb-3 font-semibold uppercase tracking-wider">GitHub Actions</p>
            <CodeBlock
              code={`name: AKF Governance
on: [pull_request]
jobs:
  governance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install akf
      - run: akf report . --format json -o governance.json
      - run: akf report . --format html -o governance.html
      - name: Upload report
        uses: actions/upload-artifact@v4
        with:
          name: governance-report
          path: governance.html
      - name: Check compliance
        run: |
          RATE=$(python3 -c "
          import json
          r = json.load(open('governance.json'))
          print(r['compliance_rate'])
          ")
          echo "Compliance rate: $RATE"
          python3 -c "
          import json, sys
          r = json.load(open('governance.json'))
          if r['compliance_rate'] < 0.8:
            print('FAIL: compliance below 80%')
            sys.exit(1)
          if r['critical_risks'] > 0:
            print('FAIL: critical risks detected')
            sys.exit(1)
          print('PASS: governance checks OK')
          "`}
              language="bash"
              filename=".github/workflows/akf.yml"
            />
          </div>

          {/* Features list */}
          <div className="flex flex-col gap-4">
            <p className="text-xs text-text-secondary mb-1 font-semibold uppercase tracking-wider">What you get</p>

            <div className="rounded-xl border border-border-subtle bg-surface-raised p-4 flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-500 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-text-primary">PR gate</h4>
                <p className="text-xs text-text-secondary mt-1">Block merges when compliance drops below your threshold or critical risks are detected.</p>
              </div>
            </div>

            <div className="rounded-xl border border-border-subtle bg-surface-raised p-4 flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-sky-500/10 text-sky-500 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-text-primary">Report artifacts</h4>
                <p className="text-xs text-text-secondary mt-1">HTML report uploaded as a build artifact on every PR. Always audit-ready.</p>
              </div>
            </div>

            <div className="rounded-xl border border-border-subtle bg-surface-raised p-4 flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-500 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
                </svg>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-text-primary">Model tracking per PR</h4>
                <p className="text-xs text-text-secondary mt-1">See which AI models contributed to each pull request. Track adoption over time.</p>
              </div>
            </div>

            <div className="rounded-xl border border-border-subtle bg-surface-raised p-4 flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-500 flex items-center justify-center shrink-0">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <div>
                <h4 className="text-sm font-semibold text-text-primary">Zero infrastructure</h4>
                <p className="text-xs text-text-secondary mt-1">No agents, no SaaS dashboard, no API keys. Just pip install in your workflow.</p>
              </div>
            </div>

            <div className="mt-2 p-4 rounded-xl border border-border-subtle bg-surface-raised">
              <p className="text-xs text-text-secondary mb-2 font-medium">Works with any CI system</p>
              <div className="flex flex-wrap gap-2">
                {['GitHub Actions', 'GitLab CI', 'CircleCI', 'Jenkins', 'Bitbucket Pipelines'].map((ci) => (
                  <span key={ci} className="px-2.5 py-1 rounded-md bg-surface-overlay text-xs text-text-secondary font-mono">
                    {ci}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

/* ── CTA ── */
function CTA() {
  return (
    <section className="py-20 px-6 text-center">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-3xl font-bold text-text-primary mb-4">
          Ready to govern your AI content?
        </h2>
        <p className="text-text-secondary mb-8">
          Install AKF, run one command, and know exactly what AI built in your project.
        </p>
        <Link
          to="/get-started"
          className="inline-flex items-center gap-2 px-6 py-3 rounded-lg bg-accent hover:bg-accent-hover text-white font-medium transition-colors"
        >
          Get Started
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
          </svg>
        </Link>
      </div>
    </section>
  );
}

/* ── Page ── */
export default function EnterpriseReportPage() {
  return (
    <div className="pt-14">
      <Hero />
      <KPIDashboard />
      <FormatShowcase />
      <USPCards />
      <ComparisonTable />
      <CICDIntegration />
      <CLIQuickStart />
      <CTA />
    </div>
  );
}
