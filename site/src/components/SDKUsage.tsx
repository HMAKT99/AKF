import SectionHeading from '../ui/SectionHeading';
import TabSwitcher from '../ui/TabSwitcher';
import CodeBlock from '../ui/CodeBlock';

const pythonCode = `import akf

# Create a knowledge unit
unit = akf.create(
    "Revenue was $4.2B, up 12% YoY",
    t=0.98, src="SEC 10-Q", tier=1
)
unit.save("report.akf")

# Builder API for multiple claims
unit = (akf.AKFBuilder()
    .by("sarah@woodgrove.com")
    .label("confidential")
    .claim("Revenue $4.2B", 0.98, src="SEC 10-Q", tier=1, ver=True)
    .claim("Cloud growth 15-18%", 0.85, src="Gartner", tier=2)
    .claim("Pipeline strong", 0.72, src="estimate", tier=4)
    .build())

# Compute effective trust
for claim in unit.claims:
    result = akf.effective_trust(claim)
    print(f"{result.decision}: {result.score:.2f}")

# Embed into any format
import akf.universal as akf_u
akf_u.embed("report.docx", claims=[...], classification="confidential")`;

const typescriptCode = `import { AKFBuilder, effectiveTrust } from 'akf';

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
});`;

const cliCode = `# Create a knowledge unit
akf create report.akf \\
  --claim "Revenue $4.2B" --trust 0.98 --src "SEC 10-Q" \\
  --claim "Cloud growth 15%" --trust 0.85 --src "Gartner" \\
  --by sarah@woodgrove.com --label confidential

# Validate, inspect, and compute trust
akf validate report.akf
akf inspect report.akf
akf trust report.akf

# Embed into documents
akf embed report.docx --classification confidential \\
  --claim "Revenue $4.2B" --trust 0.98

# Scan a directory for AKF metadata
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
          subtitle="SDKs for Python and TypeScript, plus a full CLI."
        />
        <TabSwitcher tabs={tabs} />
      </div>
    </section>
  );
}
