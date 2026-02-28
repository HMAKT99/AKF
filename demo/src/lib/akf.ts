// ── AKF (Agent Knowledge Format) Inline TypeScript SDK ──────────────────────

export interface Claim {
  c: string;           // claim content
  t: number;           // trust score 0-1
  src?: string;        // source
  tier?: number;       // authority tier 1-5
  ai?: boolean;        // AI-generated flag
  verified?: boolean;  // human-verified flag
  risk?: string;       // risk annotation
}

export interface ProvHop {
  by: string;          // who performed this hop
  action: string;      // what action was performed
  ts: string;          // ISO timestamp
  delta?: string;      // description of changes
}

export interface AKFUnit {
  "$akf": "1.0";
  id: string;
  ts: string;
  author: string;
  classification: string;
  claims: Claim[];
  prov: ProvHop[];
}

const AUTHORITY_WEIGHTS: Record<number, number> = {
  1: 1.0,
  2: 0.85,
  3: 0.7,
  4: 0.5,
  5: 0.3,
};

/** Compute effective trust = claim.t * authority weight for the tier */
export function effectiveTrust(claim: Claim): number {
  const tierWeight = AUTHORITY_WEIGHTS[claim.tier ?? 3] ?? 0.7;
  return parseFloat((claim.t * tierWeight).toFixed(3));
}

/** Remove null/undefined keys from an object (shallow) */
export function stripNulls<T extends Record<string, unknown>>(obj: T): Partial<T> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(obj)) {
    if (v !== null && v !== undefined) {
      out[k] = v;
    }
  }
  return out as Partial<T>;
}

/** Generate a short unique-ish ID */
function makeId(): string {
  return 'akf-' + Math.random().toString(36).substring(2, 10);
}

export interface CreateUnitOpts {
  author?: string;
  classification?: string;
  id?: string;
}

/** Create a new AKF unit from claims */
export function createUnit(claims: Claim[], opts: CreateUnitOpts = {}): AKFUnit {
  const now = new Date().toISOString();
  const author = opts.author || 'anonymous';
  return {
    "$akf": "1.0",
    id: opts.id || makeId(),
    ts: now,
    author,
    classification: opts.classification || 'internal',
    claims: claims.map(c => stripNulls(c) as Claim),
    prov: [
      {
        by: author,
        action: 'created',
        ts: now,
        delta: `+${claims.length} claims`,
      },
    ],
  };
}

export interface AddHopOpts {
  delta?: string;
}

/** Append a provenance hop to an existing AKF unit */
export function addHop(
  unit: AKFUnit,
  by: string,
  action: string,
  opts: AddHopOpts = {}
): AKFUnit {
  return {
    ...unit,
    prov: [
      ...unit.prov,
      {
        by,
        action,
        ts: new Date().toISOString(),
        delta: opts.delta,
      },
    ],
  };
}
