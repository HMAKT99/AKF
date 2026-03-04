import SectionHeading from '../ui/SectionHeading';

const modules = [
  {
    name: 'Stamp API',
    pkg: 'akf.stamp',
    description: 'One-line API for AI agents. Auto-detects evidence type from strings (test_pass, type_check, lint_clean, ci_pass, human_review).',
    functions: ['stamp()', 'parse_evidence_string()'],
  },
  {
    name: 'Git Integration',
    pkg: 'akf.git_ops',
    description: 'Stamp git commits with AKF metadata via git notes (refs/notes/akf). Trust-annotated git log with ASCII indicators.',
    functions: ['stamp_commit()', 'read_commit()', 'trust_log()'],
  },
  {
    name: 'Agent Integration',
    pkg: 'akf.agent',
    description: 'Consume upstream knowledge, derive new units, generate AKF from tool calls, format claims as LLM context.',
    functions: ['consume()', 'derive()', 'from_tool_call()', 'to_context()', 'detect()'],
  },
  {
    name: 'Compliance & Audit',
    pkg: 'akf.compliance',
    description: 'Audit AKF units against EU AI Act, SOX, HIPAA, GDPR, and NIST AI RMF. Generate audit trails and verify human oversight.',
    functions: ['audit()', 'check_regulation()', 'audit_trail()', 'verify_human_oversight()'],
  },
  {
    name: 'Knowledge Base',
    pkg: 'akf.knowledge_base',
    description: 'Persistent directory-backed knowledge store. Add claims by topic, query with filters, prune stale entries, inject into LLM context.',
    functions: ['KnowledgeBase()', 'add()', 'query()', 'prune()', 'to_context()'],
  },
  {
    name: 'Views & Reporting',
    pkg: 'akf.view',
    description: 'Pretty terminal output, standalone HTML reports with trust badges, Markdown export, and plain English executive summaries.',
    functions: ['show()', 'to_html()', 'to_markdown()', 'executive_summary()'],
  },
  {
    name: 'Data Operations',
    pkg: 'akf.data',
    description: 'Load datasets from multiple files, merge units with deduplication, filter claims, and generate quality reports.',
    functions: ['load_dataset()', 'merge()', 'filter_claims()', 'quality_report()'],
  },
  {
    name: 'Security Analysis',
    pkg: 'akf.security',
    description: 'Security scoring (0-10 with A-F grades), Purview DLP signals, and classification laundering detection.',
    functions: ['security_score()', 'purview_signals()', 'detect_laundering()'],
  },
];

export default function Modules() {
  return (
    <section id="modules" className="py-20 px-6">
      <div className="max-w-6xl mx-auto">
        <SectionHeading
          title="Built-in modules"
          subtitle="Everything you need for production AI knowledge management — no extra packages required."
        />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {modules.map((m) => (
            <div
              key={m.name}
              className="p-6 rounded-xl bg-surface-raised border border-border-subtle hover:border-accent/30 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <h3 className="text-base font-semibold text-text-primary">{m.name}</h3>
              </div>
              <p className="text-xs font-mono text-accent mb-3">{m.pkg}</p>
              <p className="text-sm text-text-secondary leading-relaxed mb-4">{m.description}</p>
              <div className="flex flex-wrap gap-1.5">
                {m.functions.map((fn) => (
                  <span
                    key={fn}
                    className="px-2 py-0.5 text-xs font-mono bg-surface-overlay rounded text-text-tertiary"
                  >
                    {fn}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
