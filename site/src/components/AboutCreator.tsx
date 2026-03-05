export default function AboutCreator() {
  return (
    <section id="about" className="py-20 px-6">
      <div className="max-w-4xl mx-auto">
        <div className="rounded-2xl border border-border-subtle bg-surface-raised p-8 sm:p-12">
          <div className="flex flex-col sm:flex-row items-start gap-8">
            {/* Avatar / monogram */}
            <div className="shrink-0 w-20 h-20 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center">
              <span className="text-2xl font-bold text-accent font-mono">AKT</span>
            </div>

            <div className="flex-1">
              <p className="text-xs font-mono text-accent mb-2 tracking-wider uppercase">
                Created by
              </p>
              <h2 className="text-2xl sm:text-3xl font-bold text-text-primary">
                AKT
              </h2>
              <p className="mt-1 text-sm text-text-tertiary">
                Senior Product Manager at FAANG
              </p>

              <p className="mt-5 text-text-secondary leading-relaxed">
                AKF was born from a problem I kept hitting at scale: AI is generating
                content everywhere — documents, code, analysis, decisions — but there
                was no standard way to answer{' '}
                <span className="text-text-primary font-medium">"how much should I trust this?"</span>
              </p>

              <p className="mt-4 text-text-secondary leading-relaxed">
                After years of building AI-powered products at FAANG scale, I saw the
                same trust and provenance gaps across every team — from engineering
                pipelines to executive reports. Compliance teams wanted audit trails.
                Platform teams wanted machine-readable confidence scores. Security
                teams wanted classification that travels with the data. Everyone was
                building ad-hoc solutions.
              </p>

              <p className="mt-4 text-text-secondary leading-relaxed">
                AKF is the standard I wished existed: a lightweight, universal format
                that embeds trust metadata directly into the files AI already produces.
                No extra infrastructure. No vendor lock-in. Just{' '}
                <code className="px-1.5 py-0.5 rounded bg-surface text-accent text-sm font-mono border border-border-subtle">
                  pip install akf
                </code>{' '}
                and every file your AI touches carries its own trust score, provenance
                chain, and security label.
              </p>

            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
