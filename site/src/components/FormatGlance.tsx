import SectionHeading from '../ui/SectionHeading';
import CodeBlock from '../ui/CodeBlock';

const examples = [
  {
    label: 'Compact',
    description: '~15 tokens. Wire format for agents.',
    code: `{
  "v": "1.0",
  "claims": [
    { "c": "Revenue was $4.2B", "t": 0.98,
      "src": "SEC 10-Q", "tier": 1 }
  ]
}`,
  },
  {
    label: 'Descriptive',
    description: 'Human-readable. Same data, clear names.',
    code: `{
  "version": "1.0",
  "classification": "confidential",
  "claims": [
    { "content": "Revenue was $4.2B",
      "confidence": 0.98,
      "source": "SEC 10-Q",
      "authority_tier": 1,
      "verified": true }
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
    { "c": "Revenue $4.2B", "t": 0.98,
      "src": "SEC 10-Q", "tier": 1,
      "ver": true, "decay": 90 },
    { "c": "H2 will accelerate", "t": 0.63,
      "tier": 5, "ai": true,
      "risk": "AI inference" }
  ],
  "prov": [
    { "hop": 0, "by": "sarah@woodgrove.com",
      "do": "created",
      "at": "2025-07-15T09:30:00Z" },
    { "hop": 1, "by": "copilot-m365",
      "do": "enriched",
      "at": "2025-07-15T10:15:00Z" }
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
