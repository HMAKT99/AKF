const agents = [
  { name: 'Claude Code', category: 'Agent' },
  { name: 'GitHub Copilot', category: 'Agent' },
  { name: 'Cursor', category: 'Agent' },
  { name: 'Devin', category: 'Agent' },
  { name: 'GPT-4o', category: 'Model' },
  { name: 'Gemini', category: 'Model' },
  { name: 'LangChain', category: 'Framework' },
  { name: 'LlamaIndex', category: 'Framework' },
  { name: 'CrewAI', category: 'Framework' },
  { name: 'MCP', category: 'Protocol' },
];

const formats = [
  'DOCX', 'PDF', 'XLSX', 'PPTX', 'HTML', 'Markdown',
  'PNG', 'JPEG', 'JSON', 'CSV', 'Git',
];

export default function WorksWith() {
  return (
    <section className="py-16 px-6 border-t border-border-subtle">
      <div className="max-w-5xl mx-auto">
        {/* Agents & frameworks */}
        <p className="text-center text-xs font-semibold text-text-tertiary uppercase tracking-widest mb-6">
          Works with every AI agent, model, and framework
        </p>
        <div className="flex flex-wrap items-center justify-center gap-2 mb-10">
          {agents.map((a) => (
            <span
              key={a.name}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-border-subtle bg-surface-raised text-sm text-text-secondary"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-accent/60" />
              {a.name}
            </span>
          ))}
        </div>

        {/* File formats */}
        <p className="text-center text-xs font-semibold text-text-tertiary uppercase tracking-widest mb-6">
          Embeds natively into 20+ file formats
        </p>
        <div className="flex flex-wrap items-center justify-center gap-2">
          {formats.map((f) => (
            <span
              key={f}
              className="px-3 py-1.5 rounded-lg border border-border-subtle bg-surface-raised font-mono text-xs text-text-secondary"
            >
              .{f.toLowerCase()}
            </span>
          ))}
          <span className="px-3 py-1.5 rounded-lg border border-accent/30 bg-accent/5 font-mono text-xs text-accent font-medium">
            + everything else via sidecar
          </span>
        </div>
      </div>
    </section>
  );
}
