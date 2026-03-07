import { Link } from 'react-router-dom';

const gaps = [
  { q: 'Is this AI-generated?', md: 'No idea', akf: 'origin tracking, ai flag' },
  { q: 'How sure is this claim?', md: 'Can\'t express it', akf: '0.98 confidence per claim' },
  { q: 'Where did it come from?', md: 'A footnote, maybe', akf: 'Provenance chain with hops' },
  { q: 'Who\'s allowed to see it?', md: 'Nothing', akf: 'Classification with inheritance' },
  { q: 'Has a human reviewed it?', md: 'No signal', akf: 'Review verdicts + oversight' },
  { q: 'Is it still valid?', md: 'No expiry', akf: 'Temporal decay + freshness' },
  { q: 'Is it compliant?', md: 'Manual audit', akf: 'EU AI Act, HIPAA, SOX, GDPR' },
];

export default function ComparePage() {
  return (
    <div className="pt-14">
      <section className="py-16 px-6">
        <div className="max-w-3xl mx-auto">
          <Link to="/" className="text-sm text-accent hover:underline mb-10 inline-block">← Home</Link>

          {/* Hero */}
          <p className="text-xs font-mono text-accent tracking-widest uppercase">You know .md</p>
          <h1 className="mt-2 text-4xl sm:text-5xl font-extrabold tracking-tight text-text-primary">
            What's <span className="text-accent">.akf</span>?
          </h1>
          <p className="mt-4 text-lg text-text-secondary max-w-xl">
            Markdown tells the world how your content <em>looks</em>.<br />
            It never tells the world how much to <em>trust</em> it.
          </p>

          {/* Before / After */}
          <div className="mt-12">
            <div className="grid sm:grid-cols-2 gap-4">
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2 h-2 rounded-full bg-text-tertiary/40" />
                  <p className="text-xs font-mono text-text-tertiary uppercase tracking-wider">Before — report.md</p>
                </div>
                <pre className="text-sm font-mono bg-surface-raised rounded-xl border border-border-subtle p-5 text-text-tertiary leading-relaxed h-full">
{`# Q3 Earnings

Revenue was $4.2B, up 12% YoY.

H2 will accelerate growth.

Market share expanded to 34%.`}
                </pre>
              </div>
              <div>
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2 h-2 rounded-full bg-accent" />
                  <p className="text-xs font-mono text-accent uppercase tracking-wider">After — same file + AKF</p>
                </div>
                <pre className="text-sm font-mono bg-surface-raised rounded-xl border border-accent/20 p-5 text-text-secondary leading-relaxed h-full">
{`---
akf:
  claims:
    - c: "Revenue $4.2B, up 12%"
      `}<span className="text-emerald-500 font-bold">t: 0.98</span>{`
      src: "SEC 10-Q"
    - c: "H2 will accelerate"
      `}<span className="text-amber-500 font-bold">t: 0.63</span>{`
      ai: true
    - c: "Market share 34%"
      `}<span className="text-emerald-500 font-bold">t: 0.91</span>{`
      src: "Gartner"
---`}
                </pre>
              </div>
            </div>
            <p className="mt-5 text-center text-sm text-text-secondary font-medium">
              Same Markdown. Now every claim carries its own confidence score, source, and AI flag.
            </p>
          </div>

          {/* The 7 questions */}
          <div className="mt-20">
            <h2 className="text-xl font-bold text-text-primary">7 questions Markdown can't answer</h2>
            <p className="mt-1 text-sm text-text-secondary mb-8">AKF answers all of them in ~15 tokens of JSON.</p>

            <div className="rounded-xl border border-border-subtle overflow-hidden">
              <table className="w-full text-left">
                <thead>
                  <tr className="bg-surface-overlay">
                    <th className="px-5 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">Question</th>
                    <th className="px-5 py-3.5 text-xs font-semibold text-text-secondary uppercase tracking-wider">.md</th>
                    <th className="px-5 py-3.5 text-xs font-bold text-accent uppercase tracking-wider">.akf</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border-subtle">
                  {gaps.map((r) => (
                    <tr key={r.q} className="bg-surface-raised hover:bg-surface-overlay transition-colors">
                      <td className="px-5 py-3.5 text-sm font-medium text-text-primary">{r.q}</td>
                      <td className="px-5 py-3.5 text-sm text-red-400/70 italic">{r.md}</td>
                      <td className="px-5 py-3.5 text-sm text-emerald-400 font-mono font-medium">{r.akf}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* How it fits */}
          <div className="mt-16">
            <h2 className="text-xl font-bold text-text-primary">Not a replacement. A layer.</h2>
            <div className="mt-5 grid gap-4 sm:grid-cols-3">
              {[
                { emoji: '', title: 'Lives inside .md', desc: 'YAML frontmatter. Your renderer ignores it. Your trust engine reads it.' },
                { emoji: '', title: 'Per-claim precision', desc: 'One claim is 98% sure from an SEC filing. Another is 63% AI inference. AKF knows.' },
                { emoji: '', title: '15 tokens', desc: 'The overhead of a tweet. The value of an audit trail.' },
              ].map((item) => (
                <div key={item.title} className="rounded-xl border border-border-subtle bg-surface-raised p-5">
                  <h3 className="text-sm font-semibold text-text-primary">{item.title}</h3>
                  <p className="mt-2 text-xs text-text-secondary leading-relaxed">{item.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Closer */}
          <div className="mt-16 border-l-2 border-accent pl-5 py-1">
            <p className="text-base text-text-primary font-medium">
              Every AI agent writes Markdown.
            </p>
            <p className="text-base text-text-secondary mt-1">
              Not one of them tells you which parts to believe.
            </p>
            <p className="text-base text-accent font-semibold mt-1">
              That's what .akf is for.
            </p>
          </div>

          <div className="mt-10">
            <Link to="/#get-started" className="inline-flex items-center gap-2 text-sm font-medium text-accent hover:underline">
              Get started →
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
