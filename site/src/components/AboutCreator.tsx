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
                Arun Kumar Thangavel
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

              {/* Links */}
              <div className="mt-8 flex flex-wrap items-center gap-3">
                <a
                  href="https://github.com/HMAKT99/AKF"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-border-subtle hover:border-accent/30 text-sm text-text-secondary hover:text-text-primary transition-colors"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
                  </svg>
                  GitHub
                </a>
                <a
                  href="https://www.linkedin.com/in/arun-kumar-thangavel/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-border-subtle hover:border-accent/30 text-sm text-text-secondary hover:text-text-primary transition-colors"
                >
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                  </svg>
                  LinkedIn
                </a>
                <a
                  href="https://pypi.org/project/akf/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-border-subtle hover:border-accent/30 text-sm text-text-secondary hover:text-text-primary transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                  PyPI
                </a>
                <a
                  href="https://www.npmjs.com/package/akf"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-border-subtle hover:border-accent/30 text-sm text-text-secondary hover:text-text-primary transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
                  </svg>
                  npm
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
