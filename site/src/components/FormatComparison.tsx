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

        <div className="overflow-x-auto rounded-xl border border-border-subtle">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-surface-overlay">
                <th className="px-4 py-3 text-xs font-semibold text-text-tertiary uppercase tracking-wider sticky left-0 bg-surface-overlay z-10">
                  Format
                </th>
                {features.map((f) => (
                  <th key={f} className="px-3 py-3 text-xs font-semibold text-text-tertiary uppercase tracking-wider text-center whitespace-nowrap">
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
                  <td className={`px-4 py-3.5 text-sm font-medium whitespace-nowrap sticky left-0 z-10 ${i === 0 ? 'text-accent font-semibold bg-accent/5' : 'text-text-primary bg-surface-raised'}`}>
                    {fmt.name}
                  </td>
                  {fmt.checks.map((checked, j) => (
                    <td key={j} className="px-3 py-3.5">
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
      </div>
    </section>
  );
}
