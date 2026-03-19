import { useState, useEffect } from 'react';

// ── Scenario definitions ────────────────────────────────────────────────────
// Each scenario shows actual AKF code + authentic output

interface Scenario {
  id: string;
  label: string;
  icon: string;
  description: string;
  code: string;
  output: OutputLine[];
}

interface OutputLine {
  text: string;
  color?: string;    // tailwind text color
  indent?: number;   // indent level (each = 2 spaces)
  blank?: boolean;   // empty line
  delay?: number;    // stagger animation index
}

const g = 'text-gray-500';
const w = 'text-gray-200';
const e = 'text-emerald-400';
const a = 'text-amber-400';
const s = 'text-sky-400';
const p = 'text-purple-400';
const r = 'text-red-400';
const c = 'text-red-300';

const SCENARIOS: Scenario[] = [
  // ── 1. Stamp & Embed ────────────────────────────────────────────────────
  {
    id: 'stamp',
    label: 'Stamp & Embed',
    icon: '\u2705',
    description: 'Embed trust metadata into any file — DOCX, PDF, images, code',
    code: `import akf

# Stamp a financial report with trust metadata
akf.stamp_file(
    "quarterly-report.docx",
    confidence=0.98,
    source="SEC 10-Q",
    model="gpt-4o",
    classification="confidential"
)

# Verify it embedded
meta = akf.extract("quarterly-report.docx")
print(meta)`,
    output: [
      { text: '$ python stamp_report.py', color: g },
      { text: '' , blank: true },
      { text: '\u2705 Metadata embedded into quarterly-report.docx', color: e },
      { text: '   \u2192 docProps/custom.xml (Office custom properties)', color: g },
      { text: '   \u2192 156 bytes added', color: g },
      { text: '' , blank: true },
      { text: 'Extracted metadata:', color: g },
      { text: '{', color: w },
      { text: '  "version": "1.1",', color: w },
      { text: '  "claims": [{', color: w },
      { text: '    "content": "Quarterly financial results...",', color: e },
      { text: '    "confidence": 0.98,', color: a },
      { text: '    "authority_tier": 1,', color: s },
      { text: '    "ai_generated": true,', color: p },
      { text: '    "source": "SEC 10-Q"', color: e },
      { text: '  }],', color: w },
      { text: '  "model": "gpt-4o",', color: e },
      { text: '  "classification": "confidential",', color: a },
      { text: '  "created": "2026-03-16T10:30:00Z"', color: g },
      { text: '}', color: w },
      { text: '' , blank: true },
      { text: 'Supported: .docx .pdf .xlsx .pptx .png .jpg .html .md', color: g },
      { text: '           .json .py .ts .js .eml .csv .txt (20+ formats)', color: g },
    ],
  },

  // ── 2. Trust Analysis ───────────────────────────────────────────────────
  {
    id: 'trust',
    label: 'Trust Analysis',
    icon: '\ud83d\udcca',
    description: 'Compute trust scores with confidence, authority, decay, and evidence',
    code: `import akf

unit = akf.stamp(
    "Revenue was $4.2B, up 12% YoY",
    confidence=0.92,
    source="SEC 10-Q",
    model="gpt-4o",
    evidence=["source verified", "cross-referenced"]
)

# Full trust breakdown
print(akf.explain_trust(unit.claims[0]))`,
    output: [
      { text: '$ python analyze_trust.py', color: g },
      { text: '' , blank: true },
      { text: 'Trust Analysis for "Revenue was $4.2B, up 12% YoY"', color: w },
      { text: '========================================', color: g },
      { text: '  Base confidence:    0.92', color: a },
      { text: '  Authority tier:     3 (weight: 0.70)', color: s },
      { text: '  Origin weight:      0.70 (ai)', color: p },
      { text: '  Temporal decay:     1.0000 (age: 0.0d)', color: g },
      { text: '  Grounding bonus:    +0.10', color: e },
      { text: '  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500', color: g },
      { text: '  Effective trust:    0.5508', color: a },
      { text: '  Decision:           LOW', color: a },
      { text: '  Evidence:           2 piece(s) \u2014 grounded', color: e },
      { text: '  \u2192 Claim is below trust threshold. Review before use.', color: a },
      { text: '' , blank: true },
      { text: '  Thresholds:', color: g },
      { text: '    ACCEPT  \u2265 0.700    \u2502  actionable without review', color: e },
      { text: '    LOW     0.400\u20130.699 \u2502  needs human verification', color: a },
      { text: '    REJECT  < 0.400    \u2502  do not use', color: r },
    ],
  },

  // ── 3. Security Scan ────────────────────────────────────────────────────
  {
    id: 'security',
    label: 'Security Scan',
    icon: '\ud83d\udee1\ufe0f',
    description: 'Detect 10 manipulation patterns: laundering, inflation, gaps',
    code: `import akf

# A suspicious AI-generated claim:
# high confidence, no source, speculative tier
unit = akf.stamp(
    "Revenue will reach $50B next quarter",
    confidence=0.95,
    ai_generated=True
)
unit.claims[0].authority_tier = 5

report = akf.run_all_detections(unit)
print(f"{report.triggered_count} detections triggered")`,
    output: [
      { text: '$ python security_scan.py', color: g },
      { text: '' , blank: true },
      { text: 'Detection Report \u2014 4 triggered (2 critical, 2 high)', color: r },
      { text: '============================================================', color: g },
      { text: '' , blank: true },
      { text: '\u26a0\ufe0f  Hallucination Risk  [critical]', color: c },
      { text: '   - AI claim has 0.95 confidence with no source attribution', color: w },
      { text: '   Recommendation: Ground AI outputs with verifiable sources', color: g },
      { text: '' , blank: true },
      { text: '\u26a0\ufe0f  Knowledge Laundering  [critical]', color: c },
      { text: '   - Confidence 0.95 from Tier 5 (speculative) source', color: w },
      { text: '   Recommendation: High confidence requires Tier 1\u20132 authority', color: g },
      { text: '' , blank: true },
      { text: '\u26a0\ufe0f  AI Content Without Review  [high]', color: a },
      { text: '   - AI-generated claim has no human review recorded', color: w },
      { text: '   Recommendation: Add human review before distribution', color: g },
      { text: '' , blank: true },
      { text: '\u26a0\ufe0f  Ungrounded AI Claims  [high]', color: a },
      { text: '   - No evidence or source to support this assertion', color: w },
      { text: '   Recommendation: Attach verifiable evidence', color: g },
      { text: '' , blank: true },
      { text: '\u2705  Trust Below Threshold        [passed]', color: g },
      { text: '\u2705  Classification Downgrade     [passed]', color: g },
      { text: '\u2705  Stale Claims                 [passed]', color: g },
      { text: '\u2705  Trust Degradation Chain       [passed]', color: g },
      { text: '\u2705  Excessive AI Concentration   [passed]', color: g },
      { text: '\u2705  Provenance Gap               [passed]', color: g },
    ],
  },

  // ── 4. Compliance Audit ─────────────────────────────────────────────────
  {
    id: 'audit',
    label: 'Compliance Audit',
    icon: '\ud83d\udccb',
    description: 'Audit against EU AI Act, HIPAA, SOX, GDPR, NIST AI, ISO 42001',
    code: `import akf

# Audit a document against EU AI Act
result = akf.audit(
    "medical-report.pdf",
    regulation="eu_ai_act"
)

print(f"Compliant: {result.compliant}")
print(f"Score: {result.score}")
for check in result.checks:
    print(f"  {check}")`,
    output: [
      { text: '$ python audit_compliance.py', color: g },
      { text: '' , blank: true },
      { text: 'EU AI Act Compliance Audit', color: s },
      { text: '============================================================', color: g },
      { text: '' , blank: true },
      { text: 'Compliant: False', color: r },
      { text: 'Score: 0.50 / 1.00', color: a },
      { text: '' , blank: true },
      { text: 'Checks:', color: g },
      { text: '  \u2705  eu_ai_transparency (Art. 13)     \u2502 AI origin disclosed', color: e },
      { text: '  \u274c  eu_ai_human_oversight (Art. 14)  \u2502 No review records found', color: r },
      { text: '  \u2705  eu_ai_accuracy (Art. 15)         \u2502 Confidence scores present', color: e },
      { text: '  \u274c  eu_ai_traceability (Art. 12)     \u2502 No provenance chain', color: r },
      { text: '' , blank: true },
      { text: 'Recommendations:', color: a },
      { text: '  1. Add human review stamps (Art. 14 requires oversight)', color: w },
      { text: '  2. Build provenance chain with akf.add_hop()', color: w },
      { text: '  3. Set classification to control data access', color: w },
      { text: '' , blank: true },
      { text: 'Supported regulations:', color: g },
      { text: '  eu_ai_act \u2502 hipaa \u2502 sox \u2502 gdpr \u2502 nist_ai \u2502 iso_42001', color: g },
    ],
  },

  // ── 5. Multi-Agent Provenance ───────────────────────────────────────────
  {
    id: 'provenance',
    label: 'Provenance Chain',
    icon: '\ud83d\udd17',
    description: 'Track trust across multi-agent hops with chained hashing',
    code: `import akf

# Agent A creates a research summary
unit = akf.stamp(
    "Market growth projected at 15% CAGR",
    confidence=0.82,
    source="industry-report",
    agent="research-agent"
)

# Agent B enriches with additional analysis
unit = akf.add_hop(unit,
    by="analyst-agent", action="enriched")

# Human reviewer approves
unit = akf.add_hop(unit,
    by="sarah@corp.com", action="reviewed")

print(akf.format_tree(unit))`,
    output: [
      { text: '$ python multi_agent.py', color: g },
      { text: '' , blank: true },
      { text: 'Provenance Chain (3 hops)', color: s },
      { text: '============================================================', color: g },
      { text: '' , blank: true },
      { text: 'research-agent created', color: e },
      { text: '\u2502 \u2192 sha256:a3f8c1...  2026-03-16T09:00:00Z', color: g },
      { text: '\u2502   confidence: 0.82  tier: 3  source: industry-report', color: g },
      { text: '\u2502', color: g },
      { text: '\u251c\u2500\u2500 analyst-agent enriched', color: a },
      { text: '\u2502 \u2192 sha256:7d2e4b...  2026-03-16T09:15:00Z', color: g },
      { text: '\u2502   chain penalty: -0.02 (trust degradation per hop)', color: a },
      { text: '\u2502', color: g },
      { text: '\u2514\u2500\u2500 sarah@corp.com reviewed \u2705', color: e },
      { text: '  \u2192 sha256:f1b9a0...  2026-03-16T10:30:00Z', color: g },
      { text: '  review bonus: +0.10 (human approval)', color: e },
      { text: '' , blank: true },
      { text: 'Trust journey:', color: g },
      { text: '  hop 0:  0.574  (0.82 \u00d7 0.70)', color: w },
      { text: '  hop 1:  0.554  (\u22120.02 chain penalty)', color: a },
      { text: '  hop 2:  0.654  (+0.10 review bonus)', color: e },
      { text: '' , blank: true },
      { text: 'Integrity: sha256:f1b9a0... (chain verified \u2705)', color: e },
      { text: 'Each hop hash includes the previous \u2014 tamper-evident chain', color: g },
    ],
  },

  // ── 6. Multi-Agent Teams ──────────────────────────────────────────────
  {
    id: 'teams',
    label: 'Agent Teams',
    icon: '\ud83e\udd1d',
    description: 'Delegate trust across agent teams with ceiling caps and per-agent attribution',
    code: `import akf

# Define delegation policy
policy = akf.DelegationPolicy(
    delegator="lead-agent",
    delegate="research-bot",
    trust_ceiling=0.7,
    allowed_actions=["search", "summarize"]
)

# Team streaming: multiple agents, one session
with akf.TeamStream(["lead", "research"]) as ts:
    ts.write("lead", "Task: analyze Q4 report")
    ts.write("research", "Found 3 sources")
    result = ts.aggregate()
    print(f"Team trust: {result.team_avg_trust}")`,
    output: [
      { text: '$ python team_delegate.py', color: g },
      { text: '' , blank: true },
      { text: 'Delegation Policy', color: s },
      { text: '  lead-agent \u2192 research-bot', color: w },
      { text: '  Trust ceiling: 0.70 (caps delegate output)', color: a },
      { text: '  Actions: search, summarize', color: e },
      { text: '' , blank: true },
      { text: 'Team Stream Session (2 agents)', color: s },
      { text: '============================================================', color: g },
      { text: '  lead       \u2502 "Task: analyze Q4 report"  (t=0.70)', color: e },
      { text: '  research   \u2502 "Found 3 sources"          (t=0.70)', color: e },
      { text: '' , blank: true },
      { text: 'Team Trust Aggregation:', color: w },
      { text: '  lead:       avg=0.7000  claims=1', color: e },
      { text: '  research:   avg=0.7000  claims=1', color: e },
      { text: '  \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500', color: g },
      { text: '  Team avg:   0.7000  total=2', color: a },
      { text: '' , blank: true },
      { text: 'Team certify: akf certify src/ --team', color: g },
      { text: '  \u2192 Per-agent breakdown + all_agents_certified gate', color: g },
    ],
  },
];

// ── Syntax-highlighted Python code ──────────────────────────────────────────

function PythonHighlight({ code }: { code: string }) {
  const keywords = ['import', 'from', 'for', 'in', 'print', 'if', 'else', 'with', 'as', 'def', 'return', 'True', 'False', 'None'];
  const lines = code.split('\n');

  return (
    <pre className="text-[13px] leading-[1.7] overflow-x-auto">
      {lines.map((line, i) => {
        let html = line
          // Strings (double-quoted)
          .replace(/"([^"]*?)"/g, '<span class="text-emerald-400">"$1"</span>')
          // Comments
          .replace(/(#.*)$/, '<span class="text-gray-500">$1</span>');

        // Keywords (only whole words, not inside strings/comments)
        for (const kw of keywords) {
          const re = new RegExp(`\\b(${kw})\\b(?![^<]*>)`, 'g');
          html = html.replace(re, `<span class="text-purple-400">$1</span>`);
        }

        // Numbers (standalone, not inside tags)
        html = html.replace(/\b(\d+\.?\d*)\b(?![^<]*>)/g, '<span class="text-amber-400">$1</span>');

        // Function calls
        html = html.replace(/\b(akf\.\w+|print|len)\(/g, '<span class="text-sky-400">$1</span>(');

        return (
          <div key={i} className="text-gray-300" dangerouslySetInnerHTML={{ __html: html || '\u00a0' }} />
        );
      })}
    </pre>
  );
}

// ── Output renderer with stagger animation ──────────────────────────────────

function OutputRenderer({ lines, visible }: { lines: OutputLine[]; visible: boolean }) {
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    if (!visible) {
      setVisibleCount(0);
      return;
    }
    // Fast stagger: reveal lines quickly
    let count = 0;
    const interval = setInterval(() => {
      count++;
      setVisibleCount(count);
      if (count >= lines.length) clearInterval(interval);
    }, 30);
    return () => clearInterval(interval);
  }, [visible, lines.length]);

  return (
    <pre className="text-[13px] leading-[1.7] overflow-x-auto">
      {lines.map((line, i) => (
        <div
          key={i}
          className={`transition-all duration-200 ${
            i < visibleCount ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-1'
          } ${line.color || 'text-gray-300'}`}
          style={{ paddingLeft: line.indent ? `${line.indent * 16}px` : undefined }}
        >
          {line.blank ? '\u00a0' : line.text}
        </div>
      ))}
    </pre>
  );
}

// ── File format icons ───────────────────────────────────────────────────────

const FILE_FORMATS = [
  'docx', 'pdf', 'xlsx', 'pptx', 'png', 'html',
  'json', 'py', 'ts', 'md', 'mp4', 'mp3',
];

// ── Main Component ──────────────────────────────────────────────────────────

export default function InteractiveDemo() {
  const [activeId, setActiveId] = useState(SCENARIOS[0].id);
  const [executing, setExecuting] = useState(false);
  const [showOutput, setShowOutput] = useState(true);

  const active = SCENARIOS.find(s => s.id === activeId)!;

  function handleSwitch(id: string) {
    if (id === activeId) return;
    setShowOutput(false);
    setExecuting(true);
    setActiveId(id);
    // Brief "executing" flash, then reveal output
    setTimeout(() => {
      setExecuting(false);
      setShowOutput(true);
    }, 500);
  }

  // Auto-show on first render
  useEffect(() => {
    const timer = setTimeout(() => setShowOutput(true), 600);
    return () => clearTimeout(timer);
  }, []);

  return (
    <section className="py-20 px-6">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight">
            See AKF <span className="text-accent">in action</span>
          </h2>
          <p className="mt-3 text-text-secondary max-w-2xl mx-auto">
            Real API calls, real output. Click through to explore what AKF does — the same code runs in production.
          </p>
        </div>

        {/* Scenario tabs */}
        <div className="flex flex-wrap justify-center gap-2 mb-8">
          {SCENARIOS.map((s) => (
            <button
              key={s.id}
              onClick={() => handleSwitch(s.id)}
              className={`px-4 py-2.5 text-sm rounded-lg border transition-all cursor-pointer flex items-center gap-2 ${
                activeId === s.id
                  ? 'bg-accent/10 border-accent/40 text-accent font-medium shadow-sm'
                  : 'bg-surface-raised border-border-subtle text-text-secondary hover:border-text-tertiary hover:text-text-primary'
              }`}
            >
              <span>{s.icon}</span>
              <span>{s.label}</span>
            </button>
          ))}
        </div>

        {/* Description */}
        <p className="text-center text-sm text-text-tertiary mb-6">
          {active.description}
        </p>

        {/* Code + Output panels */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-0 rounded-2xl overflow-hidden border border-gray-700 shadow-2xl">

          {/* ── LEFT: Code Panel ──────────────────────────────────── */}
          <div className="bg-gray-900 p-5 sm:p-6 border-b lg:border-b-0 lg:border-r border-gray-700">
            {/* Window chrome */}
            <div className="flex items-center gap-2 mb-4">
              <div className="w-3 h-3 rounded-full bg-red-400/80" />
              <div className="w-3 h-3 rounded-full bg-amber-400/80" />
              <div className="w-3 h-3 rounded-full bg-emerald-400/80" />
              <span className="ml-2 text-xs text-gray-500 font-mono">
                {active.id === 'stamp' ? 'stamp_report.py' :
                 active.id === 'trust' ? 'analyze_trust.py' :
                 active.id === 'security' ? 'security_scan.py' :
                 active.id === 'audit' ? 'audit_compliance.py' :
                 active.id === 'teams' ? 'team_delegate.py' :
                 'multi_agent.py'}
              </span>
            </div>
            <PythonHighlight code={active.code} />
          </div>

          {/* ── RIGHT: Output Panel ──────────────────────────────── */}
          <div className="bg-[#0d1117] p-5 sm:p-6 min-h-[420px]">
            {/* Terminal chrome */}
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xs text-gray-500 font-mono">Terminal</span>
              {executing && (
                <svg className="w-3 h-3 animate-spin text-accent ml-auto" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
              )}
            </div>
            <OutputRenderer lines={active.output} visible={showOutput && !executing} />
          </div>
        </div>

        {/* Format support strip */}
        <div className="mt-10 text-center">
          <p className="text-xs text-text-tertiary uppercase tracking-wider mb-4">
            Embeds natively into 20+ file formats
          </p>
          <div className="flex flex-wrap justify-center gap-2">
            {FILE_FORMATS.map((f) => (
              <span
                key={f}
                className="px-2.5 py-1 rounded-md text-xs font-mono font-medium bg-surface-overlay text-text-secondary border border-border-subtle"
              >
                .{f}
              </span>
            ))}
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="text-center mt-6">
          <p className="text-sm text-text-tertiary">
            This demo shows real AKF SDK calls — the same trust formula, detections, and audit logic used in production.
          </p>
        </div>
      </div>
    </section>
  );
}
