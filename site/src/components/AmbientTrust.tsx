import React from 'react';
import SectionHeading from '../ui/SectionHeading';

const integrations = [
  {
    label: 'Claude Code',
    file: 'CLAUDE.md',
    description: 'Claude reads your project\'s CLAUDE.md and stamps every file it creates with trust metadata — confidence scores, evidence, and provenance chain.',
    color: 'text-orange-400',
    bgColor: 'bg-orange-500/10',
  },
  {
    label: 'Cursor / Windsurf',
    file: '.cursorrules / .windsurfrules',
    description: 'Drop a .cursorrules or .windsurfrules file into your project. Every AI edit carries a trust score. Agents stamp their work before you even review it.',
    color: 'text-violet-400',
    bgColor: 'bg-violet-500/10',
  },
  {
    label: 'GitHub Copilot',
    file: 'copilot-instructions.md',
    description: 'Copilot Coding Agent reads .github/copilot-instructions.md natively. Every file it creates or modifies gets stamped with trust metadata and evidence.',
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
  },
  {
    label: 'OpenAI Codex',
    file: 'AGENTS.md',
    description: 'Codex reads AGENTS.md for project instructions. Stamps files with trust metadata in cloud sandbox and local environments.',
    color: 'text-cyan-400',
    bgColor: 'bg-cyan-500/10',
  },
  {
    label: 'Enterprise Copilots',
    file: 'Office / Workspace Add-in',
    description: 'M365 Copilot via Office Add-in and Google Workspace add-on. Trust metadata flows through enterprise document workflows.',
    color: 'text-rose-400',
    bgColor: 'bg-rose-500/10',
  },
  {
    label: 'Any MCP Agent',
    file: '9 MCP Tools',
    description: 'Any MCP-compatible agent can stamp files, run audits, embed metadata, detect threats, and compute trust — all through the protocol.',
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
  },
];

const trustPipeline = [
  { step: 'Agent team writes code', icon: 'edit', detail: 'Delegation policies cap trust ceilings per agent' },
  { step: 'Git commit stamped', icon: 'git', detail: 'Post-commit hook writes trust metadata to git notes' },
  { step: 'CI validates trust', icon: 'check', detail: 'akf certify --team checks per-agent trust scores' },
  { step: 'Team reviews with context', icon: 'eye', detail: 'Per-agent breakdowns, confidence, and provenance' },
];

const icons: Record<string, React.ReactNode> = {
  edit: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="m16.862 4.487 1.687-1.688a1.875 1.875 0 1 1 2.652 2.652L10.582 16.07a4.5 4.5 0 0 1-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 0 1 1.13-1.897l8.932-8.931Zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0 1 15.75 21H5.25A2.25 2.25 0 0 1 3 18.75V8.25A2.25 2.25 0 0 1 5.25 6H10" />
    </svg>
  ),
  git: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
    </svg>
  ),
  check: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
    </svg>
  ),
  eye: (
    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
    </svg>
  ),
};

export default function AmbientTrust() {
  return (
    <section id="ambient-trust" className="py-20 px-6">
      <div className="max-w-5xl mx-auto">
        <SectionHeading
          title="Ambient Trust"
          subtitle="Trust metadata flows automatically through your entire AI workflow — from agent to commit to PR to production. No manual stamping."
        />

        {/* Agent integrations grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-12">
          {integrations.map((item) => (
            <div
              key={item.label}
              className="rounded-xl border border-border-subtle bg-surface-raised p-5 flex flex-col gap-3 hover:border-accent/30 transition-colors"
            >
              <div className="flex items-center justify-between">
                <span className={`text-sm font-bold ${item.color}`}>{item.label}</span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded-full ${item.bgColor} ${item.color}`}>
                  {item.file}
                </span>
              </div>
              <p className="text-sm text-text-secondary leading-relaxed">{item.description}</p>
            </div>
          ))}
        </div>

        {/* Trust Pipeline visual */}
        <div className="rounded-xl border border-border-subtle bg-surface-raised p-6 mb-8">
          <h3 className="text-lg font-bold text-text-primary mb-1">The Trust Pipeline</h3>
          <p className="text-sm text-text-secondary mb-6">Every step in your AI workflow produces trust metadata automatically.</p>

          <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
            {trustPipeline.map((item, i) => (
              <div key={item.step} className="relative flex flex-col items-center text-center">
                <div className="w-10 h-10 rounded-full bg-accent/10 text-accent flex items-center justify-center mb-2">
                  {icons[item.icon]}
                </div>
                <p className="text-xs font-semibold text-text-primary mb-1">{item.step}</p>
                <p className="text-[11px] text-text-tertiary leading-snug">{item.detail}</p>
                {i < trustPipeline.length - 1 && (
                  <div className="hidden sm:block absolute top-5 -right-2 text-accent/40">
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                    </svg>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* How it works — code snippets */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="rounded-xl border border-border-subtle bg-surface-raised p-5">
            <p className="text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-3">For your project</p>
            <div className="space-y-2 font-mono text-xs">
              <div className="rounded-lg bg-surface border border-border-subtle px-4 py-3">
                <span className="text-text-tertiary"># Agent stamps its own work</span>
                <br />
                <span className="text-accent">CLAUDE.md</span>
                <span className="text-text-secondary"> + </span>
                <span className="text-accent">.cursorrules</span>
              </div>
              <div className="rounded-lg bg-surface border border-border-subtle px-4 py-3">
                <span className="text-text-tertiary"># Git hooks stamp every commit</span>
                <br />
                <span className="text-text-primary">akf init --git-hooks</span>
              </div>
              <div className="rounded-lg bg-surface border border-border-subtle px-4 py-3">
                <span className="text-text-tertiary"># CI validates trust on every PR</span>
                <br />
                <span className="text-text-primary">- uses: HMAKT99/AKF/extensions/github-action@main</span>
              </div>
            </div>
          </div>

          <div className="rounded-xl border border-border-subtle bg-surface-raised p-5">
            <p className="text-xs font-semibold text-text-tertiary uppercase tracking-wider mb-3">For your terminal</p>
            <div className="space-y-2 font-mono text-xs">
              <div className="rounded-lg bg-surface border border-border-subtle px-4 py-3">
                <span className="text-text-tertiary"># Intercept all AI CLI tools</span>
                <br />
                <span className="text-text-primary">eval "$(akf shell-hook)"</span>
              </div>
              <div className="rounded-lg bg-surface border border-border-subtle px-4 py-3">
                <span className="text-text-tertiary"># Background daemon for file monitoring</span>
                <br />
                <span className="text-text-primary">akf install</span>
              </div>
              <div className="rounded-lg bg-surface border border-border-subtle px-4 py-3">
                <span className="text-text-tertiary"># Smart context: git, xattr, rules</span>
                <br />
                <span className="text-text-primary">akf watch ~/Documents</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
