import { Link } from 'react-router-dom';
import SectionHeading from '../ui/SectionHeading';

const stats = [
  { value: '~15', label: 'tokens per stamp', detail: 'smaller than a tweet' },
  { value: '30+', label: 'formats supported', detail: 'DOCX, PDF, video, audio, code' },
  { value: '10', label: 'detection classes', detail: 'AI-specific security' },
  { value: 'Multi', label: 'agent teams', detail: 'delegation & streaming' },
];

const personaPreviews = [
  {
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
    title: 'Knowledge Workers',
    oneLiner: 'Trust what you read',
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25z" />
      </svg>
    ),
    title: 'AI Agents',
    oneLiner: 'Ship trusted output',
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
    title: 'Security & CISOs',
    oneLiner: 'Detect what others miss',
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.125 2.25h-4.5c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125v-9M10.125 2.25h.375a9 9 0 019 9v.375M10.125 2.25A3.375 3.375 0 0113.5 5.625v1.5c0 .621.504 1.125 1.125 1.125h1.5a3.375 3.375 0 013.375 3.375M9 15l2.25 2.25L15 12" />
      </svg>
    ),
    title: 'Governance',
    oneLiner: 'Prove it. Automatically.',
  },
  {
    icon: (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
      </svg>
    ),
    title: 'Developers',
    oneLiner: 'Build trust into everything',
  },
];

export default function ValueProps() {
  return (
    <section id="ai-native" className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="AI-native by design"
          subtitle="Purpose-built for the way AI agents and humans actually work."
        />

        {/* Stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-16">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-xl border border-border-subtle bg-surface-raised p-6 text-center"
            >
              <div className="text-3xl font-bold text-accent">{stat.value}</div>
              <div className="text-sm font-semibold text-text-primary mt-1">{stat.label}</div>
              <div className="text-xs text-text-secondary mt-0.5">{stat.detail}</div>
            </div>
          ))}
        </div>

        {/* Persona previews */}
        <h3 className="text-lg font-semibold text-text-primary text-center mb-6">Who uses AKF?</h3>
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          {personaPreviews.map((p) => (
            <Link
              key={p.title}
              to="/personas"
              className="rounded-xl border border-border-subtle bg-surface-raised p-4 flex flex-col items-center gap-2 text-center hover:border-accent/40 transition-colors group"
            >
              <div className="w-9 h-9 rounded-lg bg-accent/10 text-accent flex items-center justify-center group-hover:bg-accent/20 transition-colors">
                {p.icon}
              </div>
              <div className="text-sm font-semibold text-text-primary">{p.title}</div>
              <div className="text-xs text-text-secondary">{p.oneLiner}</div>
            </Link>
          ))}
        </div>

        <div className="mt-8 text-center">
          <Link
            to="/personas"
            className="inline-flex items-center gap-1.5 text-sm font-medium text-accent hover:underline"
          >
            See all personas & scenarios
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
          </Link>
        </div>
      </div>
    </section>
  );
}
