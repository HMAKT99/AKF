import { useState } from 'react';

// ── Validate logic ──

interface CheckResult {
  rule: string;
  passed: boolean;
  detail: string;
}

function validateAKF(text: string): { valid: boolean; checks: CheckResult[]; error?: string } {
  const checks: CheckResult[] = [];

  let json: any;
  try {
    json = JSON.parse(text);
  } catch {
    return { valid: false, checks: [], error: 'Invalid JSON' };
  }

  const hasVersion = !!(json.v || json.version);
  checks.push({ rule: 'Version', passed: hasVersion, detail: hasVersion ? `v${json.v || json.version}` : 'Missing "v" or "version" field' });

  const claims = json.claims || [];
  const hasClaims = Array.isArray(claims) && claims.length > 0;
  checks.push({ rule: 'Claims present', passed: hasClaims, detail: hasClaims ? `${claims.length} claim(s)` : 'No claims array or empty' });

  const confValid = claims.every((c: any) => {
    const t = c.t ?? c.confidence;
    return typeof t === 'number' && t >= 0 && t <= 1;
  });
  checks.push({ rule: 'Confidence range', passed: confValid, detail: confValid ? 'All in [0, 1]' : 'Some confidence values out of range' });

  const tierValid = claims.every((c: any) => {
    const tier = c.tier ?? c.authority_tier;
    return tier === undefined || (typeof tier === 'number' && tier >= 1 && tier <= 5);
  });
  checks.push({ rule: 'Authority tier', passed: tierValid, detail: tierValid ? 'All tiers valid (1-5)' : 'Some tiers out of range' });

  const validLabels = ['public', 'internal', 'confidential', 'highly-confidential', 'restricted'];
  const label = json.label || json.classification;
  const labelValid = !label || validLabels.includes(label);
  checks.push({ rule: 'Classification', passed: labelValid, detail: labelValid ? (label || 'Not set') : `Invalid: "${label}"` });

  const prov = json.prov || json.provenance || [];
  const provSeq = prov.length === 0 || prov.every((h: any, i: number) => h.hop === i);
  checks.push({ rule: 'Provenance sequence', passed: provSeq, detail: provSeq ? `${prov.length} hop(s)` : 'Hop numbers not sequential' });

  const hash = json.hash || json.integrity_hash;
  const hashValid = !hash || /^(sha256|sha3-512|blake3):/.test(hash);
  checks.push({ rule: 'Hash format', passed: hashValid, detail: hashValid ? (hash ? hash.slice(0, 20) + '...' : 'Not set') : 'Invalid hash prefix' });

  const valid = checks.every(c => c.passed);
  return { valid, checks };
}

// ── Audit logic ──

interface AuditCheck {
  check: string;
  passed: boolean;
}

interface AuditResult {
  compliant: boolean;
  score: number;
  checks: AuditCheck[];
  recommendations: string[];
  error?: string;
}

function auditAKF(text: string): AuditResult {
  let json: any;
  try {
    json = JSON.parse(text);
  } catch {
    return { compliant: false, score: 0, checks: [], recommendations: [], error: 'Invalid JSON' };
  }

  const checks: AuditCheck[] = [];
  let scorePoints = 0;
  let maxPoints = 0;
  const recommendations: string[] = [];

  maxPoints++;
  const prov = json.prov || json.provenance || [];
  const hasProv = Array.isArray(prov) && prov.length > 0;
  checks.push({ check: 'Provenance present', passed: hasProv });
  if (hasProv) scorePoints++; else recommendations.push('Add provenance to track data lineage');

  maxPoints++;
  const hasHash = !!(json.hash || json.integrity_hash);
  checks.push({ check: 'Integrity hash', passed: hasHash });
  if (hasHash) scorePoints++; else recommendations.push('Compute integrity hash for tamper detection');

  maxPoints++;
  const hasClass = !!(json.label || json.classification);
  checks.push({ check: 'Classification set', passed: hasClass });
  if (hasClass) scorePoints++; else recommendations.push('Set security classification');

  maxPoints++;
  const claims = json.claims || [];
  const allSourced = claims.length === 0 || claims.every((c: any) => {
    const src = c.src || c.source;
    return src && src !== 'unspecified';
  });
  checks.push({ check: 'All claims sourced', passed: allSourced });
  if (allSourced) scorePoints++; else recommendations.push('Add source attribution to all claims');

  maxPoints++;
  const aiLabeled = claims.every((c: any) => (c.ai ?? c.ai_generated) !== undefined);
  checks.push({ check: 'AI claims labeled', passed: aiLabeled });
  if (aiLabeled) scorePoints++;

  maxPoints++;
  const riskyAi = claims.filter((c: any) => (c.ai ?? c.ai_generated) && (c.tier ?? c.authority_tier ?? 3) >= 4);
  const allRiskyDescribed = riskyAi.length === 0 || riskyAi.every((c: any) => !!c.risk);
  checks.push({ check: 'AI risk described', passed: allRiskyDescribed });
  if (allRiskyDescribed) scorePoints++; else recommendations.push('Add risk descriptions to AI-generated speculative claims');

  maxPoints++;
  const validStructure = claims.length > 0 && claims.every((c: any) => {
    const content = c.c || c.content;
    const conf = c.t ?? c.confidence;
    return content && typeof conf === 'number' && conf >= 0 && conf <= 1;
  });
  checks.push({ check: 'Valid structure', passed: validStructure });
  if (validStructure) scorePoints++;

  const score = maxPoints > 0 ? Math.round((scorePoints / maxPoints) * 100) / 100 : 0;
  return { compliant: score >= 0.7, score, checks, recommendations };
}

// ── Combined page ──

type Tab = 'validate' | 'audit';

export default function ValidatePage() {
  const [tab, setTab] = useState<Tab>('validate');
  const [input, setInput] = useState('');
  const [valResult, setValResult] = useState<ReturnType<typeof validateAKF> | null>(null);
  const [auditResult, setAuditResult] = useState<AuditResult | null>(null);

  const sampleAKF = JSON.stringify({
    v: '1.0',
    label: 'confidential',
    hash: 'sha256:abc123',
    claims: [
      { c: 'Q3 revenue $4.2B', t: 0.98, src: 'SEC 10-Q', tier: 1, ai: false },
      { c: 'Market share 23%', t: 0.85, src: 'Gartner', ai: false }
    ],
    prov: [{ hop: 0, by: 'sarah@acme.com', do: 'created', at: '2025-07-15T09:30:00Z' }]
  }, null, 2);

  const runAction = () => {
    if (tab === 'validate') setValResult(validateAKF(input));
    else setAuditResult(auditAKF(input));
  };

  return (
    <div className="pt-14">
      <div className="max-w-3xl mx-auto px-6 py-16">
        <h1 className="text-3xl font-bold text-text-primary mb-2">Validate & Audit</h1>
        <p className="text-text-secondary mb-8">
          Check structural validity or run a compliance audit on any AKF JSON. All checks run client-side.
        </p>

        {/* Tab switcher */}
        <div className="flex gap-1 p-1 rounded-lg bg-surface-raised border border-border-subtle mb-6 w-fit">
          <button
            onClick={() => setTab('validate')}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${tab === 'validate' ? 'bg-accent text-white' : 'text-text-secondary hover:text-text-primary'}`}
          >
            Validate
          </button>
          <button
            onClick={() => setTab('audit')}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${tab === 'audit' ? 'bg-accent text-white' : 'text-text-secondary hover:text-text-primary'}`}
          >
            Audit
          </button>
        </div>

        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Paste AKF JSON here..."
          className="w-full h-64 bg-surface-raised border border-border-subtle rounded-lg p-4 font-mono text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50 resize-y"
        />

        <div className="flex gap-3 mt-4">
          <button
            onClick={runAction}
            disabled={!input.trim()}
            className="px-6 py-2 rounded-lg bg-accent hover:bg-accent-hover text-white font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {tab === 'validate' ? 'Validate' : 'Run Audit'}
          </button>
          <button
            onClick={() => { setInput(sampleAKF); setValResult(null); setAuditResult(null); }}
            className="px-4 py-2 rounded-lg border border-border-subtle text-text-secondary hover:text-text-primary transition-colors"
          >
            Load Sample
          </button>
        </div>

        {/* Validate results */}
        {tab === 'validate' && valResult && (
          <div className="mt-8 space-y-4">
            <div className={`p-4 rounded-lg border ${valResult.valid ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
              <span className={`font-semibold ${valResult.valid ? 'text-green-400' : 'text-red-400'}`}>
                {valResult.valid ? 'Valid AKF' : 'Invalid AKF'}
              </span>
              {valResult.error && <span className="ml-2 text-red-400">{valResult.error}</span>}
            </div>

            {valResult.checks.length > 0 && (
              <div className="space-y-2">
                {valResult.checks.map((check, i) => (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-surface-raised">
                    <span className="text-lg">{check.passed ? '\u2705' : '\u274c'}</span>
                    <div>
                      <span className="font-medium text-text-primary">{check.rule}</span>
                      <span className="ml-2 text-sm text-text-secondary">{check.detail}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Audit results */}
        {tab === 'audit' && auditResult && (
          <div className="mt-8 space-y-6">
            <div className={`p-6 rounded-lg border ${auditResult.compliant ? 'border-green-500/30 bg-green-500/5' : 'border-red-500/30 bg-red-500/5'}`}>
              <div className="flex items-center justify-between">
                <div>
                  <span className={`text-2xl font-bold ${auditResult.compliant ? 'text-green-400' : 'text-red-400'}`}>
                    {auditResult.compliant ? 'COMPLIANT' : 'NON-COMPLIANT'}
                  </span>
                  {auditResult.error && <p className="text-red-400 mt-1">{auditResult.error}</p>}
                </div>
                <div className="text-right">
                  <div className="text-3xl font-mono font-bold text-text-primary">{(auditResult.score * 100).toFixed(0)}%</div>
                  <div className="text-sm text-text-secondary">audit score</div>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {auditResult.checks.map((check, i) => (
                <div key={i} className={`p-4 rounded-lg border ${check.passed ? 'border-green-500/20 bg-green-500/5' : 'border-red-500/20 bg-red-500/5'}`}>
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{check.passed ? '\u2705' : '\u274c'}</span>
                    <span className="font-medium text-text-primary">{check.check}</span>
                  </div>
                </div>
              ))}
            </div>

            {auditResult.recommendations.length > 0 && (
              <div className="p-4 rounded-lg bg-surface-raised border border-border-subtle">
                <h3 className="font-semibold text-text-primary mb-3">Recommendations</h3>
                <ul className="space-y-2">
                  {auditResult.recommendations.map((rec, i) => (
                    <li key={i} className="flex items-start gap-2 text-text-secondary">
                      <span className="text-accent mt-0.5">&bull;</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
