import SectionHeading from '../ui/SectionHeading';
import CodeBlock from '../ui/CodeBlock';

const examples = [
  {
    label: 'Minimal',
    description: '~15 tokens. Just claims and trust.',
    code: `{
  "v": "1.0",
  "claims": [
    { "c": "Revenue was $4.2B", "t": 0.98 }
  ]
}`,
  },
  {
    label: 'Practical',
    description: 'Source attribution, tiers, and classification.',
    code: `{
  "v": "1.0",
  "by": "sarah@woodgrove.com",
  "label": "confidential",
  "claims": [
    { "c": "Revenue $4.2B, up 12%", "t": 0.98, "src": "SEC 10-Q", "tier": 1, "ver": true },
    { "c": "Cloud growth 15-18%", "t": 0.85, "src": "Gartner", "tier": 2 },
    { "c": "Pipeline strong", "t": 0.72, "src": "CRM estimate", "tier": 4 }
  ]
}`,
  },
  {
    label: 'Full',
    description: 'Provenance chains, decay, and AI risk flags.',
    code: `{
  "v": "1.0",
  "by": "sarah@woodgrove.com",
  "label": "confidential",
  "inherit": true,
  "claims": [
    { "c": "Revenue $4.2B", "t": 0.98, "src": "SEC 10-Q", "tier": 1, "ver": true, "decay": 90 },
    { "c": "H2 will accelerate", "t": 0.63, "tier": 5, "ai": true, "risk": "AI inference" }
  ],
  "prov": [
    { "hop": 0, "by": "sarah@woodgrove.com", "do": "created", "at": "2025-07-15T09:30:00Z" },
    { "hop": 1, "by": "copilot-m365", "do": "enriched", "at": "2025-07-15T10:15:00Z" }
  ]
}`,
  },
];

export default function FormatGlance() {
  return (
    <section id="format" className="py-20 px-6">
      <div className="max-w-6xl mx-auto">
        <SectionHeading
          title="Format at a glance"
          subtitle="Progressive complexity — use only the fields you need."
        />
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {examples.map((ex) => (
            <div key={ex.label}>
              <div className="mb-3">
                <span className="text-sm font-semibold text-accent">{ex.label}</span>
                <p className="text-sm text-text-tertiary">{ex.description}</p>
              </div>
              <CodeBlock code={ex.code} language="json" filename={`${ex.label.toLowerCase()}.akf`} />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
