import { useState } from 'react';
import { Link } from 'react-router-dom';
import SectionHeading from '../ui/SectionHeading';

interface Scenario {
  title: string;
  description: string;
}

interface Persona {
  icon: React.ReactNode;
  title: string;
  subtitle: string;
  intro: string;
  scenarios: Scenario[];
}

const personas: Persona[] = [
  {
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
    title: 'Knowledge Workers',
    subtitle: 'Trust What You Read',
    intro: 'Every report, brief, and analysis you consume may contain AI-generated content. AKF gives you instant visibility into what was machine-generated, how trustworthy the claims are, and whether a human reviewed it.',
    scenarios: [
      { title: 'Review AI-generated reports', description: 'See trust scores and evidence for every claim before sharing with stakeholders. Know exactly which sections were AI-generated and which were human-verified.' },
      { title: 'Audit compliance documents', description: 'Verify that regulatory filings meet trust thresholds. AKF metadata shows the full provenance chain from source data to final document.' },
      { title: 'Validate research summaries', description: 'Check whether AI-summarized research accurately represents the source material. Trust scores highlight potential hallucination risks.' },
      { title: 'Collaborate with confidence', description: 'When sharing documents across teams, embedded AKF metadata travels with the file — no external tools needed to verify trust.' },
      { title: 'Track document lineage', description: 'See the full history of how a document evolved: who created it, what AI models were used, and every review checkpoint along the way.' },
    ],
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 3v1.5M4.5 8.25H3m18 0h-1.5M4.5 12H3m18 0h-1.5m-15 3.75H3m18 0h-1.5M8.25 19.5V21M12 3v1.5m0 15V21m3.75-18v1.5m0 15V21m-9-1.5h10.5a2.25 2.25 0 002.25-2.25V6.75a2.25 2.25 0 00-2.25-2.25H6.75A2.25 2.25 0 004.5 6.75v10.5a2.25 2.25 0 002.25 2.25z" />
      </svg>
    ),
    title: 'AI Agents & Pipelines',
    subtitle: 'Ship Trusted Output',
    intro: 'When AI agents produce content at scale, trust can\'t be an afterthought. AKF stamps every output with provenance, trust scores, and evidence — so downstream consumers always know what they\'re getting.',
    scenarios: [
      { title: 'Stamp agent output automatically', description: 'Add AKF metadata to every file your agent produces. One SDK call embeds trust scores, model info, and evidence into the output format.' },
      { title: 'Stream trust in real-time', description: 'For streaming pipelines, AKF attaches incremental trust metadata as content is generated — no waiting for the full document to complete.' },
      { title: 'Build provenance chains', description: 'When agents consume and transform content, AKF tracks the full chain: source trust, transformation steps, and final output confidence.' },
      { title: 'Enforce trust thresholds', description: 'Set minimum trust scores for pipeline outputs. Content below threshold gets flagged for human review before publishing.' },
      { title: 'Integrate with any stack', description: 'Python SDK, CLI, and REST API. Works with LangChain, AutoGen, CrewAI, and any custom pipeline architecture.' },
    ],
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
    title: 'Security & CISOs',
    subtitle: 'Detect What Others Miss',
    intro: 'AI content introduces novel security risks that traditional DLP can\'t catch. AKF integrates with Microsoft Purview and enterprise security tools to detect 10 classes of AI-specific threats.',
    scenarios: [
      { title: 'Detect unreviewed AI content', description: 'Automatically flag documents where AI-generated content has no human review stamp. Prevent unverified AI output from reaching customers or regulators.' },
      { title: 'Monitor trust degradation', description: 'Track trust scores across your document ecosystem. Get alerts when content falls below organizational thresholds or shows signs of knowledge laundering.' },
      { title: 'Enforce classification policies', description: 'Prevent AI from downgrading document classification levels. AKF metadata makes classification changes auditable and enforceable.' },
      { title: 'Identify hallucination risk', description: 'AKF\'s evidence-backed trust scores highlight content with weak grounding. Security teams can prioritize review of high-risk documents.' },
      { title: 'Integrate with Microsoft Purview', description: '10 pre-built detection classes for AI content risks — from provenance gaps to excessive AI concentration. Deploy in hours, not months.' },
    ],
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.125 2.25h-4.5c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125v-9M10.125 2.25h.375a9 9 0 019 9v.375M10.125 2.25A3.375 3.375 0 0113.5 5.625v1.5c0 .621.504 1.125 1.125 1.125h1.5a3.375 3.375 0 013.375 3.375M9 15l2.25 2.25L15 12" />
      </svg>
    ),
    title: 'Governance & Compliance',
    subtitle: 'Prove It. Automatically.',
    intro: 'Regulatory frameworks like the EU AI Act and HIPAA require organizations to demonstrate AI transparency. AKF generates machine-readable audit trails that satisfy compliance requirements out of the box.',
    scenarios: [
      { title: 'EU AI Act compliance', description: 'AKF metadata satisfies AI Act transparency requirements: model identification, human oversight markers, and risk classification — all embedded in the document itself.' },
      { title: 'HIPAA audit trails', description: 'For healthcare AI, AKF provides complete provenance from source data to clinical output. Every transformation step is recorded and auditable.' },
      { title: 'Automated compliance reports', description: 'Generate compliance reports from AKF metadata across your document corpus. No manual evidence gathering — it\'s already in the files.' },
      { title: 'Policy enforcement at scale', description: 'Define organizational trust policies and enforce them across all AI-generated content. Non-compliant documents are flagged before distribution.' },
      { title: 'Regulator-ready evidence', description: 'When regulators ask "how was this AI content verified?", point them to the embedded AKF metadata. Machine-readable, tamper-evident, and standards-based.' },
    ],
  },
  {
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5" />
      </svg>
    ),
    title: 'Developers',
    subtitle: 'Build Trust Into Everything',
    intro: 'AKF is designed for developers first. pip install, import, and start embedding trust metadata in minutes. Full SDK, CLI, git hooks, and support for every major file format.',
    scenarios: [
      { title: 'Get started in 5 minutes', description: 'pip install akf, import the SDK, and stamp your first file. No configuration, no API keys, no infrastructure to set up.' },
      { title: 'Use the Python SDK', description: 'Pythonic API for creating, reading, and validating AKF metadata. Type-safe, well-documented, and designed for both scripts and production services.' },
      { title: 'Add git hooks for trust', description: 'Pre-commit hooks that automatically stamp or validate AKF metadata on every commit. Ensure nothing ships without trust metadata.' },
      { title: 'Support every format', description: 'Native embedding for Office docs, PDFs, images, HTML, Markdown, and JSON. Sidecar support for everything else. One API, every format.' },
      { title: 'Extend and customize', description: 'Custom trust engines, pluggable evidence sources, and extensible metadata schemas. Build exactly the trust pipeline your application needs.' },
    ],
  },
];

function PersonaCard({ persona }: { persona: Persona }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-xl border border-border-subtle bg-surface-raised overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full p-6 flex items-start gap-4 text-left hover:bg-surface-overlay transition-colors cursor-pointer"
      >
        <div className="w-12 h-12 rounded-lg bg-accent/10 text-accent flex items-center justify-center shrink-0">
          {persona.icon}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-xl font-semibold text-text-primary">{persona.title}</h3>
          <p className="text-sm font-medium text-accent mt-0.5">{persona.subtitle}</p>
          <p className="text-sm text-text-secondary mt-2">{persona.intro}</p>
        </div>
        <svg
          className={`w-5 h-5 text-text-tertiary shrink-0 mt-1 transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
        </svg>
      </button>

      {expanded && (
        <div className="px-6 pb-6 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {persona.scenarios.map((scenario) => (
            <div
              key={scenario.title}
              className="rounded-lg border border-border-subtle bg-surface p-4"
            >
              <h4 className="text-sm font-semibold text-text-primary">{scenario.title}</h4>
              <p className="text-xs text-text-secondary mt-1.5 leading-relaxed">{scenario.description}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function PersonasPage() {
  return (
    <div className="pt-24 pb-20 px-6">
      <div className="max-w-4xl mx-auto">
        <SectionHeading
          title="Built for every role"
          subtitle="AKF serves everyone who creates, consumes, or governs AI-generated content."
        />

        <div className="flex flex-col gap-4">
          {personas.map((persona) => (
            <PersonaCard key={persona.title} persona={persona} />
          ))}
        </div>

        <div className="mt-12 text-center">
          <Link
            to="/"
            className="text-sm text-accent hover:underline"
          >
            &larr; Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}
