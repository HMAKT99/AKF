import { useState } from 'react';
import { Link } from 'react-router-dom';
import GitHubStats from './GitHubStats';

function CopyCommand({ command }: { command: string }) {
  const [copied, setCopied] = useState(false);

  function handleCopy() {
    navigator.clipboard.writeText(command).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-3 px-4 py-2.5 rounded-lg bg-surface-raised border border-border-subtle font-mono text-sm hover:border-text-tertiary transition-colors cursor-pointer group"
      aria-label={`Copy "${command}" to clipboard`}
    >
      <span className="text-text-tertiary select-none">$</span>
      <span className="text-text-primary">{command}</span>
      <span className="text-text-tertiary opacity-0 group-hover:opacity-100 transition-opacity ml-1">
        {copied ? (
          <svg className="w-4 h-4 text-emerald-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        ) : (
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
          </svg>
        )}
      </span>
    </button>
  );
}

const steps = [
  {
    title: 'Install once',
    description: 'One command. Works with Office, git, and every AI agent.',
    code: 'pip install akf',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3" />
      </svg>
    ),
  },
  {
    title: 'It just embeds',
    description: 'Trust metadata auto-attaches to every file — .docx, .pdf, images, code, and more.',
    code: 'native format support',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
      </svg>
    ),
  },
  {
    title: 'Audit anytime',
    description: 'Check compliance when you need it — EU AI Act, HIPAA, and more.',
    code: 'akf audit report.pdf',
    icon: (
      <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
  },
];

export default function Hero() {
  return (
    <section id="workflow" className="pt-32 pb-20 px-6">
      <div className="max-w-4xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-accent/10 border border-accent/20 text-accent text-sm font-medium mb-8">
          <span className="w-1.5 h-1.5 rounded-full bg-accent" />
          Open format &middot; MIT Licensed
        </div>

        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight leading-[1.1]">
          The AI native
          <br />
          <span className="text-accent">file format.</span>
        </h1>

        <p className="mt-6 text-lg sm:text-xl text-text-secondary max-w-2xl mx-auto">
          Trust scores, provenance, and compliance metadata that embed natively into every file your AI touches — DOCX, PDF, images, and code.
        </p>

        {/* 3-step workflow */}
        <div className="mt-14 grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-0 items-stretch">
          {steps.map((step, i) => (
            <div key={step.title} className="relative flex flex-col items-center">
              <div className="w-full rounded-xl border border-border-subtle bg-surface-raised p-6 flex flex-col items-center gap-3 h-full">
                <div className="w-10 h-10 rounded-lg bg-accent/10 text-accent flex items-center justify-center">
                  {step.icon}
                </div>
                <h3 className="text-lg font-semibold text-text-primary">{step.title}</h3>
                <p className="text-sm text-text-secondary">{step.description}</p>
                <code className="mt-auto px-3 py-1.5 rounded-md bg-surface text-xs font-mono text-accent border border-border-subtle">
                  {step.code}
                </code>
              </div>
              {i < steps.length - 1 && (
                <svg className="hidden sm:block absolute -right-3 top-1/2 -translate-y-1/2 w-6 h-6 text-text-tertiary z-10" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
                </svg>
              )}
            </div>
          ))}
        </div>

        <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-3">
          <CopyCommand command="pip install akf" />
          <CopyCommand command="npm install akf-format" />
        </div>

        <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
          <a
            href="https://github.com/HMAKT99/AKF"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-accent hover:bg-accent-hover text-white font-medium text-sm transition-colors"
          >
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
            </svg>
            View on GitHub
          </a>
          <Link
            to="/get-started"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-surface-raised border border-border-subtle hover:border-accent/40 text-text-primary font-medium text-sm transition-colors"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
            </svg>
            Get Started
          </Link>
        </div>

        <GitHubStats />
      </div>
    </section>
  );
}
