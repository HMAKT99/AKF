import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

const TARGET = new Date('2026-08-02T00:00:00Z').getTime();

function useCountdown() {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, []);
  const diff = Math.max(0, TARGET - now);
  const days = Math.floor(diff / 86_400_000);
  const hours = Math.floor((diff % 86_400_000) / 3_600_000);
  const mins = Math.floor((diff % 3_600_000) / 60_000);
  const secs = Math.floor((diff % 60_000) / 1000);
  return { days, hours, mins, secs };
}

function Digit({ value, label }: { value: number; label: string }) {
  return (
    <div className="flex flex-col items-center">
      <span className="text-3xl sm:text-5xl font-extrabold font-mono tabular-nums text-text-primary leading-none">
        {String(value).padStart(2, '0')}
      </span>
      <span className="mt-1 text-[10px] sm:text-xs font-semibold uppercase tracking-widest text-text-tertiary">
        {label}
      </span>
    </div>
  );
}

const regulations = [
  {
    name: 'EU AI Act — Article 50',
    date: 'Aug 2, 2026',
    status: 'upcoming' as const,
    penalty: 'Up to EUR 35M / 7% global turnover',
    requirement: 'AI-generated text for public interest must be labeled. Deepfake disclosure mandatory.',
    akf: 'ai flag + embedded provenance = transparency compliance out of the box',
    fields: ['ai', 'src', 'provenance'],
  },
  {
    name: 'Colorado AI Act (SB 205)',
    date: 'Jun 30, 2026',
    status: 'upcoming' as const,
    penalty: 'AG enforcement + private action',
    requirement: 'High-risk AI deployers must perform impact assessments and issue consumer notices.',
    akf: 'NIST AI RMF compliance is an explicit affirmative defense — akf audit provides it',
    fields: ['risk', 'tier', 'classification'],
  },
  {
    name: 'EU AI Act — GPAI Rules',
    date: 'Aug 2, 2025',
    status: 'active' as const,
    penalty: 'Up to EUR 15M / 3% global turnover',
    requirement: 'General-purpose AI model providers must document transparency and training data.',
    akf: 'Claim-level provenance chain + source tiers satisfy documentation requirements',
    fields: ['src', 'tier', 'confidence'],
  },
  {
    name: 'DORA',
    date: 'Jan 17, 2025',
    status: 'active' as const,
    penalty: 'Up to 2% global turnover',
    requirement: 'Financial entities must manage ICT third-party risk with full audit trails.',
    akf: 'Trust scores + audit trail cover AI-as-ICT-service provenance for financial workflows',
    fields: ['confidence', 'verified', 'audit'],
  },
  {
    name: 'ISO 42001',
    date: 'Voluntary',
    status: 'voluntary' as const,
    penalty: 'Competitive disadvantage',
    requirement: 'AI Management System — risk assessment, documentation, continuous improvement.',
    akf: 'AKF provides the artifact layer (trust metadata per file) that auditors inspect',
    fields: ['classification', 'risk', 'verified_by'],
  },
];

const statusStyle = {
  active: 'bg-rose-500/10 text-rose-600 border-rose-500/20',
  upcoming: 'bg-amber-500/10 text-amber-700 border-amber-500/20',
  voluntary: 'bg-sky-500/10 text-sky-600 border-sky-500/20',
};
const statusLabel = { active: 'ENFORCED', upcoming: 'UPCOMING', voluntary: 'VOLUNTARY' };

export default function ComplianceCountdown() {
  const { days, hours, mins, secs } = useCountdown();

  return (
    <section id="compliance" className="py-20 px-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="text-center mb-6">
          <p className="text-xs font-mono text-accent tracking-widest uppercase mb-3">
            Regulatory Deadlines
          </p>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-text-primary">
            Compliance is not optional
          </h2>
          <p className="mt-4 text-lg text-text-secondary max-w-2xl mx-auto">
            The EU AI Act's transparency obligations take effect in
          </p>
        </div>

        {/* Countdown */}
        <div className="flex items-center justify-center gap-4 sm:gap-6 mb-4">
          <Digit value={days} label="days" />
          <span className="text-2xl sm:text-4xl font-bold text-text-tertiary -mt-4">:</span>
          <Digit value={hours} label="hrs" />
          <span className="text-2xl sm:text-4xl font-bold text-text-tertiary -mt-4">:</span>
          <Digit value={mins} label="min" />
          <span className="text-2xl sm:text-4xl font-bold text-text-tertiary -mt-4">:</span>
          <Digit value={secs} label="sec" />
        </div>

        <p className="text-center text-sm text-text-tertiary mb-12">
          until <span className="font-semibold text-text-secondary">EU AI Act Article 50</span> — August 2, 2026
        </p>

        {/* Regulation cards */}
        <div className="space-y-3">
          {regulations.map((r) => (
            <div
              key={r.name}
              className="rounded-xl border border-border-subtle bg-surface-raised p-5 sm:p-6 hover:border-accent/30 transition-colors"
            >
              <div className="flex flex-col sm:flex-row sm:items-start gap-3 sm:gap-5">
                {/* Left: name + status */}
                <div className="sm:w-56 shrink-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-wider border ${statusStyle[r.status]}`}
                    >
                      {statusLabel[r.status]}
                    </span>
                    <span className="text-xs font-mono text-text-tertiary">{r.date}</span>
                  </div>
                  <h3 className="font-bold text-text-primary text-sm leading-snug">{r.name}</h3>
                  <p className="text-[11px] text-rose-500 font-medium mt-1">{r.penalty}</p>
                </div>

                {/* Middle: requirement */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-text-secondary leading-relaxed">{r.requirement}</p>
                  <p className="mt-2 text-sm text-emerald-600 font-medium">
                    <span className="text-emerald-500 mr-1">&#10003;</span> {r.akf}
                  </p>
                </div>

                {/* Right: AKF fields */}
                <div className="flex flex-wrap gap-1.5 sm:w-40 shrink-0 sm:justify-end">
                  {r.fields.map((f) => (
                    <code
                      key={f}
                      className="px-2 py-0.5 rounded-md bg-accent/5 border border-accent/15 text-[11px] font-mono text-accent"
                    >
                      {f}
                    </code>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* CTA */}
        <div className="mt-10 rounded-xl border border-accent/20 bg-accent/5 p-6 text-center">
          <p className="text-sm text-text-secondary mb-1">
            One command maps your files to every framework.
          </p>
          <code className="inline-block text-sm font-mono text-accent bg-surface px-4 py-2 rounded-lg border border-border-subtle mt-2 mb-4">
            akf audit report.akf --regulation eu_ai_act
          </code>
          <div className="flex flex-wrap items-center justify-center gap-3 mt-2">
            <Link
              to="/certify"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-accent hover:bg-accent-hover text-white font-medium text-sm transition-colors"
            >
              See Trust Certification
            </Link>
            <Link
              to="/validate"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-surface-raised border border-border-subtle hover:border-accent/40 text-text-primary font-medium text-sm transition-colors"
            >
              Try Compliance Audit
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
