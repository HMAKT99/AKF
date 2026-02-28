/**
 * AKF v1.0 — TypeScript interfaces for Agent Knowledge Format.
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
