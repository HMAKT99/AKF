/**
 * AKF v1.0 — TypeScript interfaces for Agent Knowledge Format.
 *
 * Field names use compact form (c, t, src, etc.) as the canonical wire format.
 * Descriptive aliases (content, confidence, source, etc.) are accepted on input
 * via the normalize() functions.
 */

/** Multi-resolution fidelity for a claim. */
export interface Fidelity {
  /** Headline (~5 tokens) */
  h?: string;
  /** Summary (~50 tokens) */
  s?: string;
  /** Full detail (~2000 tokens) */
  f?: string;
}

/** A single knowledge claim with trust metadata. */
export interface Claim {
  /** Content (required) */
  c: string;
  /** Trust score 0.0-1.0 (required) */
  t: number;
  /** Claim identifier */
  id?: string;
  /** Source attribution */
  src?: string;
  /** URI reference */
  uri?: string;
  /** Authority tier 1-5 */
  tier?: number;
  /** Verified flag */
  ver?: boolean;
  /** Verified by */
  ver_by?: string;
  /** AI-generated flag */
  ai?: boolean;
  /** Risk description */
  risk?: string;
  /** Temporal decay half-life in days */
  decay?: number;
  /** Expiration timestamp */
  exp?: string;
  /** Tags */
  tags?: string[];
  /** Contradicting claim reference */
  contra?: string;
  /** Multi-resolution fidelity */
  fidelity?: Fidelity;
  /** Extensible: unknown fields */
  [key: string]: unknown;
}

/** A single hop in the provenance chain. */
export interface ProvHop {
  /** Hop number (sequential from 0) */
  hop: number;
  /** Actor who performed the action */
  by: string;
  /** Action: created|enriched|reviewed|consumed|transformed */
  do: string;
  /** ISO-8601 timestamp */
  at: string;
  /** Chained hash of this hop */
  h?: string;
  /** Penalty applied (must be negative) */
  pen?: number;
  /** Claim IDs added */
  adds?: string[];
  /** Claim IDs dropped/rejected */
  drops?: string[];
  /** Extensible: unknown fields */
  [key: string]: unknown;
}

/** Root AKF envelope — the top-level knowledge unit. */
export interface AKFUnit {
  /** Version (required) */
  v: string;
  /** Non-empty array of claims (required) */
  claims: Claim[];
  /** Unit identifier */
  id?: string;
  /** Author */
  by?: string;
  /** AI agent identifier */
  agent?: string;
  /** ISO-8601 creation timestamp */
  at?: string;
  /** Security classification */
  label?: string;
  /** Whether children inherit classification */
  inherit?: boolean;
  /** Whether external sharing is allowed */
  ext?: boolean;
  /** Retention period in days */
  ttl?: number;
  /** Provenance chain */
  prov?: ProvHop[];
  /** Integrity hash (algorithm-prefixed) */
  hash?: string;
  /** Free-form metadata */
  meta?: Record<string, unknown>;
  /** Extensible: unknown fields */
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Descriptive name normalization
// ---------------------------------------------------------------------------

/** Maps descriptive claim field names to compact names. */
const CLAIM_ALIASES: Record<string, string> = {
  content: "c",
  confidence: "t",
  source: "src",
  authority_tier: "tier",
  verified: "ver",
  verified_by: "ver_by",
  ai_generated: "ai",
  decay_half_life: "decay",
  expires: "exp",
  contradicts: "contra",
};

/** Maps descriptive ProvHop field names to compact names. */
const PROVHOP_ALIASES: Record<string, string> = {
  actor: "by",
  action: "do",
  timestamp: "at",
  hash: "h",
  penalty: "pen",
  claims_added: "adds",
  claims_removed: "drops",
};

/** Maps descriptive AKFUnit field names to compact names. */
const UNIT_ALIASES: Record<string, string> = {
  version: "v",
  author: "by",
  created: "at",
  classification: "label",
  inherit_classification: "inherit",
  allow_external: "ext",
  integrity_hash: "hash",
  provenance: "prov",
};

/** Remap keys in an object using an alias map. Unknown keys pass through. */
function remapKeys(obj: Record<string, unknown>, aliases: Record<string, string>): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(obj)) {
    const mappedKey = aliases[key] || key;
    result[mappedKey] = value;
  }
  return result;
}

/** Normalize a claim object, converting descriptive names to compact. */
export function normalizeClaim(raw: Record<string, unknown>): Claim {
  return remapKeys(raw, CLAIM_ALIASES) as unknown as Claim;
}

/** Normalize a ProvHop object, converting descriptive names to compact. */
export function normalizeProvHop(raw: Record<string, unknown>): ProvHop {
  return remapKeys(raw, PROVHOP_ALIASES) as unknown as ProvHop;
}

/** Normalize an AKFUnit object, converting descriptive names to compact. */
export function normalizeUnit(raw: Record<string, unknown>): AKFUnit {
  const mapped = remapKeys(raw, UNIT_ALIASES);

  // Also normalize nested claims
  if (Array.isArray(mapped.claims)) {
    mapped.claims = (mapped.claims as Record<string, unknown>[]).map(
      (c) => normalizeClaim(c)
    );
  }

  // Also normalize nested provenance
  if (Array.isArray(mapped.prov)) {
    mapped.prov = (mapped.prov as Record<string, unknown>[]).map(
      (p) => normalizeProvHop(p)
    );
  }

  return mapped as unknown as AKFUnit;
}

/** Convert a compact claim to descriptive field names (for human display). */
export function toDescriptiveClaim(claim: Claim): Record<string, unknown> {
  const reverseMap: Record<string, string> = {
    c: "content",
    t: "confidence",
    src: "source",
    tier: "authority_tier",
    ver: "verified",
    ver_by: "verified_by",
    ai: "ai_generated",
    decay: "decay_half_life",
    exp: "expires",
    contra: "contradicts",
  };
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(claim)) {
    if (value !== undefined && value !== null) {
      result[reverseMap[key] || key] = value;
    }
  }
  return result;
}

/** Convert a compact AKFUnit to descriptive field names (for human display). */
export function toDescriptive(unit: AKFUnit): Record<string, unknown> {
  const reverseMap: Record<string, string> = {
    v: "version",
    by: "author",
    at: "created",
    label: "classification",
    inherit: "inherit_classification",
    ext: "allow_external",
    hash: "integrity_hash",
    prov: "provenance",
  };
  const result: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(unit)) {
    if (value !== undefined && value !== null) {
      if (key === "claims") {
        result["claims"] = (value as Claim[]).map(toDescriptiveClaim);
      } else {
        result[reverseMap[key] || key] = value;
      }
    }
  }
  return result;
}
