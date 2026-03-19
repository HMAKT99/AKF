const agents = [
  { name: 'Claude Code', category: 'Agent' },
  { name: 'GitHub Copilot', category: 'Agent' },
  { name: 'Cursor', category: 'Agent' },
  { name: 'Windsurf', category: 'Agent' },
  { name: 'OpenAI Codex', category: 'Agent' },
  { name: 'Devin', category: 'Agent' },
  { name: 'Manus', category: 'Agent' },
  { name: 'GPT-4o', category: 'Model' },
  { name: 'Gemini', category: 'Model' },
  { name: 'M365 Copilot', category: 'Enterprise' },
  { name: 'LangChain', category: 'Framework' },
  { name: 'LlamaIndex', category: 'Framework' },
  { name: 'CrewAI', category: 'Framework' },
  { name: 'Claude Agent SDK', category: 'Framework' },
  { name: 'OpenAI Agents SDK', category: 'Framework' },
  { name: 'MCP', category: 'Protocol' },
  { name: 'A2A Protocol', category: 'Protocol' },
];

const formats = [
  'DOCX', 'PDF', 'XLSX', 'PPTX', 'HTML', 'Markdown',
  'PNG', 'JPEG', 'JSON', 'CSV', 'Git',
  'MP4', 'MOV', 'WebM', 'MP3', 'WAV', 'FLAC',
];

const categoryColor: Record<string, string> = {
  Agent: 'bg-blue-500',
  Model: 'bg-violet-500',
  Enterprise: 'bg-rose-500',
  Framework: 'bg-emerald-500',
  Protocol: 'bg-amber-500',
};

export default function WorksWith() {
  return (
    <section className="py-20 px-6 relative overflow-hidden">
      {/* Subtle gradient background */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-accent/[0.03] to-transparent pointer-events-none" />

      <div className="max-w-5xl mx-auto relative">
        {/* Section header */}
        <div className="text-center mb-12">
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-text-primary">
            Universal compatibility
          </h2>
          <p className="mt-3 text-lg text-text-secondary max-w-2xl mx-auto">
            Works with the tools you already use — every agent, model, framework, and file format.
          </p>
        </div>

        {/* Agents & Frameworks */}
        <div className="mb-14">
          <div className="flex items-center justify-center gap-2 mb-6">
            <div className="h-px flex-1 max-w-16 bg-gradient-to-r from-transparent to-border-subtle" />
            <p className="text-[11px] font-semibold text-text-tertiary uppercase tracking-[0.2em]">
              AI Agents & Frameworks
            </p>
            <div className="h-px flex-1 max-w-16 bg-gradient-to-l from-transparent to-border-subtle" />
          </div>

          <div className="flex flex-wrap items-center justify-center gap-3">
            {agents.map((a) => (
              <span
                key={a.name}
                className="group inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl border border-border-subtle bg-white shadow-sm hover:shadow-md hover:border-accent/30 hover:-translate-y-0.5 transition-all duration-200 cursor-default"
              >
                <span className={`w-2 h-2 rounded-full ${categoryColor[a.category]} shadow-sm`} />
                <span className="text-sm font-semibold text-text-primary tracking-tight">{a.name}</span>
              </span>
            ))}
          </div>

          {/* Legend */}
          <div className="flex items-center justify-center gap-5 mt-5">
            {Object.entries(categoryColor).map(([label, color]) => (
              <span key={label} className="inline-flex items-center gap-1.5 text-[11px] text-text-tertiary">
                <span className={`w-1.5 h-1.5 rounded-full ${color}`} />
                {label}
              </span>
            ))}
          </div>
        </div>

        {/* File Formats */}
        <div>
          <div className="flex items-center justify-center gap-2 mb-6">
            <div className="h-px flex-1 max-w-16 bg-gradient-to-r from-transparent to-border-subtle" />
            <p className="text-[11px] font-semibold text-text-tertiary uppercase tracking-[0.2em]">
              30+ File Formats
            </p>
            <div className="h-px flex-1 max-w-16 bg-gradient-to-l from-transparent to-border-subtle" />
          </div>

          <div className="flex flex-wrap items-center justify-center gap-2.5">
            {formats.map((f) => (
              <span
                key={f}
                className="px-4 py-2 rounded-lg border border-border-subtle bg-white shadow-sm font-mono text-sm font-medium text-text-primary tracking-tight hover:border-accent/30 hover:shadow-md hover:-translate-y-0.5 transition-all duration-200 cursor-default"
              >
                .{f.toLowerCase()}
              </span>
            ))}
            <span className="px-4 py-2 rounded-lg border-2 border-accent/40 bg-gradient-to-br from-accent/5 to-accent/10 font-mono text-sm font-semibold text-accent tracking-tight shadow-sm">
              + sidecar for everything else
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
