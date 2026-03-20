import SectionHeading from '../ui/SectionHeading';

const features = [
  {
    title: 'Shell Hook',
    description: 'One line in your shell config. Every file Claude, ChatGPT, Aider, or Ollama touches gets stamped automatically. Also pre-stamps before upload to Google Workspace, Box, M365, Dropbox, and Rclone.',
    code: 'eval "$(akf shell-hook)"',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="m6.75 7.5 3 2.25-3 2.25m4.5 0h3m-9 8.25h13.5A2.25 2.25 0 0 0 21 18V6a2.25 2.25 0 0 0-2.25-2.25H5.25A2.25 2.25 0 0 0 3 6v12a2.25 2.25 0 0 0 2.25 2.25Z" />
      </svg>
    ),
  },
  {
    title: 'Background Daemon',
    description: 'Watches ~/Downloads, ~/Desktop, ~/Documents. New files get stamped with context-aware metadata instantly.',
    code: 'akf install',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 0 1 0-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178Z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
      </svg>
    ),
  },
  {
    title: 'VS Code Extension',
    description: 'Auto-stamps files edited by Copilot, Cursor, and other AI coding tools. Detects large AI-style insertions and stamps on save.',
    code: 'ext install akf-ai-monitor',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75 22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3-4.5 16.5" />
      </svg>
    ),
  },
  {
    title: 'Smart Context Detection',
    description: 'Automatically infers git author, download source, project classification rules, and AI-generated flags. No configuration needed.',
    code: 'akf watch ~/Documents',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9.813 15.904 9 18.75l-.813-2.846a4.5 4.5 0 0 0-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 0 0 3.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 0 0 3.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 0 0-3.09 3.09ZM18.259 8.715 18 9.75l-.259-1.035a3.375 3.375 0 0 0-2.455-2.456L14.25 6l1.036-.259a3.375 3.375 0 0 0 2.455-2.456L18 2.25l.259 1.035a3.375 3.375 0 0 0 2.455 2.456L21.75 6l-1.036.259a3.375 3.375 0 0 0-2.455 2.456ZM16.894 20.567 16.5 21.75l-.394-1.183a2.25 2.25 0 0 0-1.423-1.423L13.5 18.75l1.183-.394a2.25 2.25 0 0 0 1.423-1.423l.394-1.183.394 1.183a2.25 2.25 0 0 0 1.423 1.423l1.183.394-1.183.394a2.25 2.25 0 0 0-1.423 1.423Z" />
      </svg>
    ),
  },
];

export default function AutoStamping() {
  return (
    <section id="auto-stamping" className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="Zero-Touch Auto-Stamping"
          subtitle="If AI touched it, AKF knows about it. No manual intervention."
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-12">
          {features.map((f) => (
            <div
              key={f.title}
              className="rounded-xl border border-border-subtle bg-surface-raised p-6 flex flex-col gap-3"
            >
              <div className="flex items-center gap-3">
                <div className="text-accent">{f.icon}</div>
                <h3 className="font-bold text-text-primary">{f.title}</h3>
              </div>
              <p className="text-sm text-text-secondary leading-relaxed">{f.description}</p>
              <code className="mt-auto text-xs bg-surface px-3 py-2 rounded-lg font-mono text-accent border border-border-subtle">
                {f.code}
              </code>
            </div>
          ))}
        </div>

        <div className="rounded-xl border border-accent/20 bg-accent/5 p-6 text-center">
          <p className="text-sm text-text-secondary mb-3">
            Intercepts <span className="text-text-primary font-medium">Claude</span>,{' '}
            <span className="text-text-primary font-medium">ChatGPT</span>,{' '}
            <span className="text-text-primary font-medium">Aider</span>,{' '}
            <span className="text-text-primary font-medium">Ollama</span>,{' '}
            <span className="text-text-primary font-medium">Copilot</span>,{' '}
            <span className="text-text-primary font-medium">Cursor</span>, and more.
          </p>
          <p className="text-xs text-text-secondary">
            Project rules in <code className="text-accent">.akf/config.json</code> auto-classify files by path pattern.
          </p>
        </div>
      </div>
    </section>
  );
}
