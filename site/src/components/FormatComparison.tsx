import SectionHeading from '../ui/SectionHeading';

const features = [
  'Trust Score',
  'Provenance Chain',
  'AI Labeling',
  'Compact Size',
  'Office/PDF Native',
  'Streaming',
  'Compliance Audit',
  'Open Standard',
];

interface FormatRow {
  name: string;
  checks: boolean[];
}

const formats: FormatRow[] = [
  { name: 'AKF',              checks: [true, true, true, true, true, true, true, true] },
  { name: 'C2PA',             checks: [false, true, true, false, false, false, false, true] },
  { name: 'IPTC',             checks: [false, false, true, true, false, false, false, true] },
  { name: 'Watermarking',     checks: [false, false, true, false, false, false, false, false] },
  { name: 'Custom JSON/YAML', checks: [true, false, false, false, false, false, false, false] },
];

function Check() {
  return (
    <svg className="w-5 h-5 text-emerald-500 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 12.75l6 6 9-13.5" />
    </svg>
  );
}

function Dash() {
  return <span className="block w-3 h-0.5 bg-text-tertiary/40 mx-auto rounded" />;
}

export default function FormatComparison() {
  return (
    <section className="py-20 px-6">
      <div className="max-w-5xl mx-auto">
        <SectionHeading
          title="How AKF compares"
          subtitle="Purpose-built for AI content trust — not retrofitted from photo metadata or media authenticity."
        />

        <div className="rounded-xl border border-border-subtle">
          <table className="w-full table-fixed text-left">
            <thead>
              <tr className="bg-surface-overlay">
                <th className="w-[18%] px-3 py-3 text-[10px] sm:text-xs font-semibold text-text-tertiary uppercase tracking-wider">
                  Format
                </th>
                {features.map((f) => (
                  <th key={f} className="px-1 sm:px-2 py-3 text-[10px] sm:text-xs font-semibold text-text-tertiary uppercase tracking-wider text-center leading-tight">
                    {f}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {formats.map((fmt, i) => (
                <tr
                  key={fmt.name}
                  className={`${i === 0 ? 'bg-accent/5' : 'bg-surface-raised'} hover:bg-surface-overlay transition-colors`}
                >
                  <td className={`px-3 py-3.5 text-xs sm:text-sm font-medium ${i === 0 ? 'text-accent font-semibold' : 'text-text-primary'}`}>
                    {fmt.name}
                  </td>
                  {fmt.checks.map((checked, j) => (
                    <td key={j} className="px-1 sm:px-2 py-3.5">
                      {checked ? <Check /> : <Dash />}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className="mt-6 text-sm text-text-secondary text-center max-w-2xl mx-auto">
          C2PA and IPTC solve important problems in media authenticity and photo metadata.
          Watermarking detects AI-generated images. AKF is purpose-built for a different challenge:
          embedding trust, provenance, and compliance metadata into <em>all</em> AI-generated content —
          documents, code, data, and streaming outputs — in a compact, auditable format.
        </p>

        {/* .md → .akf callout */}
        <div className="mt-12 rounded-2xl border border-accent/20 bg-gradient-to-br from-accent/5 to-transparent p-8 max-w-2xl mx-auto text-center">
          <p className="text-xs font-mono text-accent tracking-widest uppercase mb-3">You know .md</p>
          <h3 className="text-2xl font-bold text-text-primary">Now meet <span className="text-accent">.akf</span></h3>
          <p className="mt-3 text-sm text-text-secondary max-w-md mx-auto">
            <code className="text-accent">.md</code> says how content looks.
            It never says how much to <em>trust</em> it.
          </p>

          <div className="mt-6 grid sm:grid-cols-2 gap-3 text-left">
            <div>
              <p className="text-[10px] font-mono text-text-tertiary uppercase tracking-wider mb-1.5 pl-1">report.md</p>
              <pre className="text-xs font-mono bg-surface-overlay/80 rounded-lg p-3 text-text-tertiary leading-relaxed h-full">
{`# Q3 Report
Revenue grew 12% to $4.2B.
H2 will accelerate growth.`}
              </pre>
            </div>
            <div>
              <p className="text-[10px] font-mono text-accent uppercase tracking-wider mb-1.5 pl-1">report.md + akf</p>
              <pre className="text-xs font-mono bg-surface-overlay/80 rounded-lg p-3 text-text-secondary leading-relaxed h-full">
{`---
akf: {"claims":[
  {"c":"Revenue grew 12%",`}<span className="text-emerald-500 font-semibold">{`"t":0.98`}</span>{`,
   "src":"SEC 10-Q"},
  {"c":"H2 will accelerate",`}<span className="text-amber-500 font-semibold">{`"t":0.63`}</span>{`,
   "ai":true}
]}
---`}
              </pre>
            </div>
          </div>

          <p className="mt-5 text-xs text-text-tertiary">
            Same file. Now it knows what it's sure about.
          </p>
          <a href="/compare" className="inline-block mt-3 text-sm font-medium text-accent hover:underline">
            See what Markdown can't tell you →
          </a>
        </div>
      </div>
    </section>
  );
}
