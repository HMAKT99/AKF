import SectionHeading from '../ui/SectionHeading';
import TabSwitcher from '../ui/TabSwitcher';
import CodeBlock from '../ui/CodeBlock';

const pythonCode = `import akf

# Create with descriptive field names (secure defaults applied)
unit = akf.create("Revenue was $4.2B, up 12% YoY",
    confidence=0.98, source="SEC 10-Q", authority_tier=1)
unit.save("report.akf")

# Builder API for multiple claims
unit = (akf.AKFBuilder()
    .by("sarah@woodgrove.com")
    .label("confidential")
    .claim("Revenue $4.2B", 0.98, source="SEC 10-Q", authority_tier=1, verified=True)
    .claim("Cloud growth 15-18%", 0.85, source="Gartner", authority_tier=2)
    .claim("Pipeline strong", 0.72, source="estimate", authority_tier=4)
    .build())

# Compute effective trust with human-readable explanation
for claim in unit.claims:
    result = akf.effective_trust(claim)
    print(f"{result.decision}: {result.score:.2f} — {claim.content}")
print(akf.explain_trust(unit.claims[0]))

# Compliance auditing
result = akf.audit("report.akf")
print(f"Score: {result.score:.2f}, Compliant: {result.compliant}")
akf.check_regulation("report.akf", "eu_ai_act")

# Embed into any format
akf.embed("report.docx", claims=[...], classification="confidential")`;

const typescriptCode = `import { AKFBuilder, effectiveTrust, fromJSON, toDescriptive } from 'akf';

const unit = new AKFBuilder()
  .by('sarah@woodgrove.com')
  .label('confidential')
  .claim('Revenue $4.2B', 0.98, { src: 'SEC 10-Q', tier: 1, ver: true })
  .claim('Cloud growth 15-18%', 0.85, { src: 'Gartner', tier: 2 })
  .build();

// Compute effective trust for each claim
unit.claims.forEach(claim => {
  const result = effectiveTrust(claim);
  console.log(\`\${result.decision}: \${result.score} — \${claim.c}\`);
});

// Parse descriptive JSON (auto-normalizes to compact)
const loaded = fromJSON('{"version":"1.0","claims":[{"content":"test","confidence":0.8}]}');

// Convert to descriptive for display
const descriptive = toDescriptive(unit);
console.log(descriptive); // { version, classification, claims: [{ content, confidence, ... }] }`;

const cliCode = `# Quick start with demo file
akf create --demo

# Create a knowledge unit
akf create report.akf \\
  --claim "Revenue $4.2B" --trust 0.98 --src "SEC 10-Q" \\
  --claim "Cloud growth 15%" --trust 0.85 --src "Gartner" \\
  --by sarah@woodgrove.com --label confidential

# Validate, inspect, and compute trust
akf validate report.akf
akf inspect report.akf
akf trust report.akf

# Compliance auditing
akf audit report.akf
akf audit report.akf --regulation eu_ai_act
akf audit report.akf --trail

# Knowledge base management
akf kb stats ./kb
akf kb query ./kb --topic finance
akf kb prune ./kb --max-age 90 --min-trust 0.3

# Embed into documents & scan
akf embed report.docx --classification confidential \\
  --claim "Revenue $4.2B" --trust 0.98
akf scan ./knowledge-base/ --recursive`;

export default function SDKUsage() {
  const tabs = [
    {
      label: 'Python',
      content: <CodeBlock code={pythonCode} language="python" filename="example.py" />,
    },
    {
      label: 'TypeScript',
      content: <CodeBlock code={typescriptCode} language="typescript" filename="example.ts" />,
    },
    {
      label: 'CLI',
      content: <CodeBlock code={cliCode} language="bash" filename="terminal" />,
    },
  ];

  return (
    <section id="sdk" className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="Get started in minutes"
          subtitle="SDKs for Python and TypeScript, plus a full CLI with compliance auditing and knowledge base management."
        />
        <TabSwitcher tabs={tabs} />
      </div>
    </section>
  );
}
