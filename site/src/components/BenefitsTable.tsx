import SectionHeading from '../ui/SectionHeading';

const benefits = [
  {
    feature: 'Trust Scores',
    description: 'Every claim carries a 0.0–1.0 confidence score with authority tiers and temporal decay.',
    detail: 't × tier_weight × decay',
  },
  {
    feature: 'Source Provenance',
    description: 'Immutable hop-by-hop chain tracks every creator, enricher, and transformer.',
    detail: 'prov[] array',
  },
  {
    feature: 'Security Classification',
    description: 'Five-level labels from public to restricted. Inheritance propagates to children.',
    detail: 'label + inherit',
  },
  {
    feature: 'Universal Format Support',
    description: 'Embeds natively in DOCX, PDF, HTML, PNG, Markdown, JSON — or as a sidecar file.',
    detail: '9+ formats',
  },
  {
    feature: 'Agent-to-Agent',
    description: 'Agents consume, filter, penalize, and re-emit AKF units without data loss.',
    detail: 'AKFTransformer',
  },
  {
    feature: '~15 Token Overhead',
    description: 'Minimal envelope costs almost nothing in context window. Scale to full provenance only when needed.',
    detail: 'Progressive',
  },
];

export default function BenefitsTable() {
  return (
    <section id="benefits" className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="Why AKF"
          subtitle="Everything AI-generated content needs, nothing it doesn't."
        />
        <div className="overflow-x-auto rounded-xl border border-border-subtle">
          <table className="w-full text-left">
            <thead>
              <tr className="bg-surface-overlay">
                <th className="px-6 py-3 text-xs font-semibold text-text-tertiary uppercase tracking-wider">Feature</th>
                <th className="px-6 py-3 text-xs font-semibold text-text-tertiary uppercase tracking-wider">Description</th>
                <th className="px-6 py-3 text-xs font-semibold text-text-tertiary uppercase tracking-wider hidden sm:table-cell">Key</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border-subtle">
              {benefits.map((b) => (
                <tr key={b.feature} className="bg-surface-raised hover:bg-surface-overlay transition-colors">
                  <td className="px-6 py-4 text-sm font-medium text-text-primary whitespace-nowrap">{b.feature}</td>
                  <td className="px-6 py-4 text-sm text-text-secondary">{b.description}</td>
                  <td className="px-6 py-4 text-xs font-mono text-accent hidden sm:table-cell">{b.detail}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
