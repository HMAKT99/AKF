// AKF v1.0 — Inline SDK (spec-aligned field names)

export interface Claim {
  c: string;
  t: number;
  id?: string;
  src?: string;
  tier?: number;
  ver?: boolean;
  ver_by?: string;
  ai?: boolean;
  risk?: string;
  tags?: string[];
  [key: string]: unknown;
}

export interface ProvHop {
  hop: number;
  by: string;
  do: string;
  at: string;
  adds?: string[];
  drops?: string[];
  pen?: number;
}

export interface AKFUnit {
  v: string;
  claims: Claim[];
  id?: string;
  by?: string;
  agent?: string;
  at?: string;
  label?: string;
  inherit?: boolean;
  ext?: boolean;
  prov?: ProvHop[];
  meta?: Record<string, unknown>;
  [key: string]: unknown;
}

const AUTHORITY_WEIGHTS: Record<number, number> = {
  1: 1.0, 2: 0.85, 3: 0.7, 4: 0.5, 5: 0.3,
};

let _counter = 0;
function makeId(): string {
  _counter++;
  return `akf-${Date.now().toString(36)}${_counter.toString(36)}`;
}

function makeClaimId(): string {
  _counter++;
  return `c-${_counter.toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

export function createUnit(
  claims: Claim[],
  opts: {
    by?: string;
    agent?: string;
    label?: string;
    inherit?: boolean;
    ext?: boolean;
    meta?: Record<string, unknown>;
  } = {}
): AKFUnit {
  const now = new Date().toISOString();
  const filled = claims.map((c) => ({ ...c, id: c.id || makeClaimId() }));
  return stripNulls({
    v: "1.0",
    id: makeId(),
    at: now,
    claims: filled,
    by: opts.by,
    agent: opts.agent,
    label: opts.label,
    inherit: opts.inherit,
    ext: opts.ext,
    meta: opts.meta,
    prov: [{
      hop: 0,
      by: opts.by || opts.agent || "unknown",
      do: "created",
      at: now,
      adds: filled.map((c) => c.id!),
    }],
  }) as AKFUnit;
}

export function addHop(
  unit: AKFUnit,
  by: string,
  action: string,
  opts?: { adds?: string[]; drops?: string[]; pen?: number }
): AKFUnit {
  const existing = unit.prov || [];
  const hop: ProvHop = stripNulls({
    hop: existing.length,
    by,
    do: action,
    at: new Date().toISOString(),
    adds: opts?.adds,
    drops: opts?.drops,
    pen: opts?.pen,
  }) as ProvHop;
  return { ...unit, prov: [...existing, hop] };
}

export interface TrustResult {
  score: number;
  decision: "ACCEPT" | "LOW" | "REJECT";
}

export function effectiveTrust(claim: Claim): TrustResult {
  const w = AUTHORITY_WEIGHTS[claim.tier ?? 3] ?? 0.7;
  const score = Math.round(claim.t * w * 10000) / 10000;
  return {
    score,
    decision: score >= 0.7 ? "ACCEPT" : score >= 0.4 ? "LOW" : "REJECT",
  };
}

export function stripNulls<T>(obj: T): T {
  if (obj === null || obj === undefined) return obj;
  if (Array.isArray(obj)) return obj.map(stripNulls) as T;
  if (typeof obj === "object") {
    const out: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(obj as Record<string, unknown>)) {
      if (v !== null && v !== undefined) out[k] = stripNulls(v);
    }
    return out as T;
  }
  return obj;
}
