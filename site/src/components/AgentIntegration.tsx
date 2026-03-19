import SectionHeading from '../ui/SectionHeading';

const mcpToolIcon = (
  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
    <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 0 1 1.37.49l1.296 2.247a1.125 1.125 0 0 1-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 0 1 0 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.955.26 1.43l-1.298 2.247a1.125 1.125 0 0 1-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 0 1-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 0 1-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 0 1-1.369-.49l-1.297-2.247a1.125 1.125 0 0 1 .26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 0 1 0-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 0 1-.26-1.43l1.297-2.247a1.125 1.125 0 0 1 1.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.086.22-.128.332-.183.582-.495.644-.869l.214-1.28Z" />
  </svg>
);

const mcpTools = [
  { name: 'create_claim', description: 'Create trust metadata' },
  { name: 'validate_file', description: 'Validate AKF files' },
  { name: 'scan_file', description: 'Security scan any file' },
  { name: 'trust_score', description: 'Compute trust scores' },
  { name: 'stamp_file', description: 'Stamp any file with metadata' },
  { name: 'audit_file', description: 'Compliance audit' },
  { name: 'embed_file', description: 'Embed into DOCX/PDF/images' },
  { name: 'extract_file', description: 'Extract metadata from files' },
  { name: 'detect_threats', description: '10 security detections' },
];

const frameworks = [
  {
    name: 'LangChain',
    status: 'Beta',
    statusColor: 'text-amber-400',
    description: 'Callback handler + document loader',
  },
  {
    name: 'LlamaIndex',
    status: 'Beta',
    statusColor: 'text-amber-400',
    description: 'Node parser + trust filter',
  },
  {
    name: 'CrewAI',
    status: 'Ready',
    statusColor: 'text-emerald-400',
    description: 'Trust-aware agent tools',
  },
];

const skills = [
  { name: 'stamp', description: 'Stamp trust metadata' },
  { name: 'audit', description: 'Compliance audit' },
  { name: 'scan', description: 'Security scan' },
  { name: 'embed', description: 'Embed into files' },
  { name: 'detect', description: '10 detection classes' },
  { name: 'stream', description: 'Real-time streaming' },
  { name: 'git', description: 'Trust-annotated git' },
  { name: 'convert', description: 'Format conversion' },
  { name: 'delegate', description: 'Agent-to-agent trust' },
  { name: 'team', description: 'Multi-agent sessions' },
];

export default function AgentIntegration() {
  return (
    <section id="agents" className="py-20 px-6">
      <div className="max-w-5xl mx-auto">
        <SectionHeading
          title="Built for AI agents"
          subtitle="MCP server, agent skills, and framework integrations — so any AI agent can create, validate, and audit trust metadata."
        />

        {/* MCP Server */}
        <div className="mb-12">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 rounded-lg bg-accent/10 text-accent flex items-center justify-center">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5.25 14.25h13.5m-13.5 0a3 3 0 01-3-3m3 3a3 3 0 100 6h13.5a3 3 0 100-6m-16.5-3a3 3 0 013-3h13.5a3 3 0 013 3m-19.5 0a4.5 4.5 0 01.9-2.7L5.737 5.1a3.375 3.375 0 012.7-1.35h7.126c1.062 0 2.062.5 2.7 1.35l2.587 3.45a4.5 4.5 0 01.9 2.7m0 0a3 3 0 01-3 3m0 3h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008zm-3 6h.008v.008h-.008v-.008zm0-6h.008v.008h-.008v-.008z" />
              </svg>
            </div>
            <div>
              <h3 className="text-xl font-bold text-text-primary">MCP Server</h3>
              <p className="text-sm text-text-secondary">Works with Claude Desktop, Cursor, and any MCP-compatible agent</p>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mb-6">
            {mcpTools.map((tool) => (
              <div
                key={tool.name}
                className="rounded-lg border border-border-subtle bg-surface-raised px-3 py-2.5 flex items-center gap-2"
              >
                <div className="text-accent shrink-0">{mcpToolIcon}</div>
                <div className="min-w-0">
                  <code className="text-xs font-mono font-semibold text-accent">{tool.name}</code>
                  <p className="text-[11px] text-text-tertiary truncate">{tool.description}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="rounded-xl border border-border-subtle bg-surface-raised p-5">
            <p className="text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-3">Quick setup</p>
            <div className="rounded-lg bg-surface border border-border-subtle p-4 font-mono text-xs text-text-primary overflow-x-auto">
              <pre>{`{
  "mcpServers": {
    "akf": {
      "command": "python",
      "args": ["-m", "mcp_server_akf"]
    }
  }
}`}</pre>
            </div>
          </div>
        </div>

        {/* Agent Skills + Frameworks side by side */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Agent Skills */}
          <div className="rounded-xl border border-border-subtle bg-surface-raised p-6">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-lg bg-accent/10 text-accent flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
                </svg>
              </div>
              <h3 className="text-lg font-bold text-text-primary">10 Agent Skills</h3>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              Drop-in markdown skill files for any AI agent to discover AKF capabilities.
            </p>
            <div className="grid grid-cols-2 gap-2">
              {skills.map((skill) => (
                <div key={skill.name} className="flex items-center gap-2 px-3 py-2 rounded-lg bg-surface border border-border-subtle">
                  <code className="text-xs font-mono text-accent">{skill.name}</code>
                  <span className="text-xs text-text-tertiary truncate">{skill.description}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Framework Integrations */}
          <div className="rounded-xl border border-border-subtle bg-surface-raised p-6">
            <div className="flex items-center gap-2.5 mb-4">
              <div className="w-8 h-8 rounded-lg bg-accent/10 text-accent flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M14.25 6.087c0-.355.186-.676.401-.959.221-.29.349-.634.349-1.003 0-1.036-1.007-1.875-2.25-1.875s-2.25.84-2.25 1.875c0 .369.128.713.349 1.003.215.283.401.604.401.959v0a.64.64 0 01-.657.643 48.39 48.39 0 01-4.163-.3c.186 1.613.293 3.25.315 4.907a.656.656 0 01-.658.663v0c-.355 0-.676-.186-.959-.401a1.647 1.647 0 00-1.003-.349c-1.036 0-1.875 1.007-1.875 2.25s.84 2.25 1.875 2.25c.369 0 .713-.128 1.003-.349.283-.215.604-.401.959-.401v0c.31 0 .555.26.532.57a48.039 48.039 0 01-.642 5.056c1.518.19 3.058.309 4.616.354a.64.64 0 00.657-.643v0c0-.355-.186-.676-.401-.959a1.647 1.647 0 01-.349-1.003c0-1.035 1.008-1.875 2.25-1.875 1.243 0 2.25.84 2.25 1.875 0 .369-.128.713-.349 1.003-.215.283-.4.604-.4.959v0c0 .333.277.599.61.58a48.1 48.1 0 005.427-.63 48.05 48.05 0 00.582-4.717.532.532 0 00-.533-.57v0c-.355 0-.676.186-.959.401-.29.221-.634.349-1.003.349-1.035 0-1.875-1.007-1.875-2.25s.84-2.25 1.875-2.25c.37 0 .713.128 1.003.349.283.215.604.401.959.401v0a.656.656 0 00.658-.663 48.422 48.422 0 00-.37-5.36c-1.886.342-3.81.574-5.766.689a.578.578 0 01-.61-.58v0z" />
                </svg>
              </div>
              <h3 className="text-lg font-bold text-text-primary">Framework Integrations</h3>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              First-class support for popular AI frameworks.
            </p>
            <div className="space-y-3">
              {frameworks.map((fw) => (
                <div key={fw.name} className="flex items-center justify-between px-4 py-3 rounded-lg bg-surface border border-border-subtle">
                  <div>
                    <span className="text-sm font-semibold text-text-primary">{fw.name}</span>
                    <p className="text-xs text-text-tertiary mt-0.5">{fw.description}</p>
                  </div>
                  <span className={`text-xs font-medium ${fw.statusColor}`}>{fw.status}</span>
                </div>
              ))}
            </div>

            {/* Extensions */}
            <div className="mt-4 pt-4 border-t border-border-subtle">
              <p className="text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-2">Extensions</p>
              <div className="flex flex-wrap gap-2">
                {['VS Code', 'GitHub Action', 'Google Workspace', 'Office Add-in'].map((ext) => (
                  <span key={ext} className="px-2.5 py-1 rounded-md bg-surface border border-border-subtle text-xs text-text-secondary">
                    {ext}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
