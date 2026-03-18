import CodeBlock from '../ui/CodeBlock';

const checks = [
  {
    title: 'Trust Scoring',
    description: 'Computes effective trust scores across all claims, provenance chains, and authority tiers. Fails if any file falls below --min-trust threshold.',
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
  },
  {
    title: 'Threat Detection',
    description: 'Scans for prompt injection, data exfiltration patterns, PII leakage, and supply-chain risks. Any critical finding fails certification.',
    color: 'text-rose-400',
    bgColor: 'bg-rose-500/10',
  },
  {
    title: 'Compliance Audit',
    description: 'Checks EU AI Act, SOX, and NIST requirements — provenance, classification, integrity hashes, AI labeling, and risk descriptions.',
    color: 'text-sky-400',
    bgColor: 'bg-sky-500/10',
  },
];

const cliUsage = `# Certify a single file
akf certify report.akf

# Set minimum trust threshold (default: 0.7)
akf certify src/ --min-trust 0.8

# Attach external test evidence
akf certify app.akf --evidence-file test-results.xml

# JSON output for CI pipelines
akf certify . --format json

# Fail CI if any file is untrusted
akf certify . --fail-on-untrusted`;

const ghActionYaml = `name: AKF Trust Gate
on: [pull_request]

jobs:
  certify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: HMAKT99/AKF/extensions/github-action@main
        with:
          command: certify
          min_trust: '0.7'
          fail_on_untrusted: 'true'
          comment_on_pr: 'true'`;

const failureExample = `  FAIL  src/predictions.py  (trust=0.32)
         detection: [CRITICAL] ungrounded_ai_claims
         compliance: AI claims labeled

  Total: 3  Certified: 2  Failed: 1  Skipped: 0
  Average trust: 0.6533

  Certification incomplete.`;

const junitExample = `<!-- test-results.xml -->
<testsuites tests="3" failures="0">
  <testsuite name="unit">
    <testcase name="test_parse" classname="test_core" />
    <testcase name="test_stamp" classname="test_core" />
    <testcase name="test_audit" classname="test_core" />
  </testsuite>
</testsuites>`;

const jsonEvidenceExample = `{
  "tests": { "passed": 42, "failed": 0 },
  "coverage": 87.5,
  "linter": "clean",
  "reviewed_by": "alice@acme.com"
}`;

export default function CertifyPage() {
  return (
    <div className="pt-14 min-h-screen bg-gradient-to-b from-surface to-surface-raised/30">
      <div className="max-w-4xl mx-auto px-6 py-16">
        {/* Header */}
        <div className="text-center mb-12">
          <p className="text-xs font-mono text-accent tracking-widest uppercase mb-2">CLI &amp; CI</p>
          <h1 className="text-4xl font-extrabold tracking-tight text-text-primary">Trust Certification</h1>
          <p className="mt-3 text-text-secondary max-w-lg mx-auto">
            One command aggregates trust scoring, threat detection, and compliance auditing into a single pass/fail gate for your AI-generated content.
          </p>
        </div>

        {/* What it checks — 3 cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-12">
          {checks.map((item) => (
            <div
              key={item.title}
              className="rounded-xl border border-border-subtle bg-surface-raised p-5 flex flex-col gap-3 hover:border-accent/30 transition-colors"
            >
              <span className={`text-sm font-bold ${item.color}`}>{item.title}</span>
              <p className="text-sm text-text-secondary leading-relaxed">{item.description}</p>
            </div>
          ))}
        </div>

        {/* CLI Usage */}
        <section className="mb-12">
          <h2 className="text-xl font-bold text-text-primary mb-1">CLI Usage</h2>
          <p className="text-sm text-text-secondary mb-4">
            Run <code className="text-accent font-mono text-xs">akf certify</code> on any file or directory. It returns exit code 0 on pass, 1 on fail.
          </p>
          <CodeBlock code={cliUsage} language="bash" filename="terminal" />
        </section>

        {/* GitHub Action */}
        <section className="mb-12">
          <h2 className="text-xl font-bold text-text-primary mb-1">GitHub Action</h2>
          <p className="text-sm text-text-secondary mb-4">
            Add trust certification as a PR gate. The composite action installs AKF, runs <code className="text-accent font-mono text-xs">akf certify</code>, and optionally posts results as a PR comment.
          </p>
          <CodeBlock code={ghActionYaml} filename=".github/workflows/akf-certify.yml" />
        </section>

        {/* Evidence Ingestion */}
        <section className="mb-12">
          <h2 className="text-xl font-bold text-text-primary mb-1">Evidence Ingestion</h2>
          <p className="text-sm text-text-secondary mb-4">
            Attach external test results or review data with <code className="text-accent font-mono text-xs">--evidence-file</code>. Supports JUnit XML and JSON formats.
          </p>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <CodeBlock code={junitExample} filename="test-results.xml" />
            <CodeBlock code={jsonEvidenceExample} language="json" filename="evidence.json" />
          </div>
        </section>

        {/* What Failure Looks Like */}
        <section className="mb-12">
          <h2 className="text-xl font-bold text-text-primary mb-1">What Failure Looks Like</h2>
          <p className="text-sm text-text-secondary mb-4">
            When certification fails, the output tells you exactly why — which detections triggered and which compliance checks failed. Fix the issues and re-run.
          </p>
          <CodeBlock code={failureExample} language="bash" filename="terminal" />
        </section>

        {/* CTA */}
        <div className="rounded-xl border border-border-subtle bg-surface-raised p-6 text-center">
          <p className="text-sm text-text-secondary mb-3">
            Ready to add trust gates to your pipeline?
          </p>
          <code className="text-accent font-mono text-sm">pip install akf && akf certify .</code>
        </div>
      </div>
    </div>
  );
}
