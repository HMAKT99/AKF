/**
 * AKF v1.0 — Core API: create, validate, serialize.
 */

import { randomUUID } from "node:crypto";
import type { AKFUnit, Claim } from "./models.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** Generate a short UUID-like identifier. */
function shortId(): string {
  return randomUUID().replace(/-/g, "").slice(0, 8);
}

/** Generate an AKF unit identifier. */
function unitId(): string {
  return `akf-${randomUUID().replace(/-/g, "").slice(0, 12)}`;
}

/** Current UTC ISO-8601 timestamp. */
function nowISO(): string {
  return new Date().toISOString();
}

// ---------------------------------------------------------------------------
// stripNulls
// ---------------------------------------------------------------------------

/** Recursively remove null and undefined values from an object or array. */
export function stripNulls<T>(obj: T): T {
  if (obj === null || obj === undefined) {
    return obj;
  }
  if (Array.isArray(obj)) {
    return obj.map((item) => stripNulls(item)) as T;
  }
  if (typeof obj === "object" && obj !== null) {
    const result: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj)) {
      if (value !== null && value !== undefined) {
        result[key] = stripNulls(value);
      }
    }
    return result as T;
  }
  return obj;
}

// ---------------------------------------------------------------------------
// Create
// ---------------------------------------------------------------------------

/** Create a single-claim AKF unit. */
export function create(
  content: string,
  t: number,
  opts?: Partial<Omit<Claim, "c" | "t">>
): AKFUnit {
  const claim: Claim = {
    c: content,
    t,
    id: shortId(),
    ...opts,
  };
  return {
    v: "1.0",
    claims: [claim],
    id: unitId(),
    at: nowISO(),
  };
}

/** Create a multi-claim AKF unit. */
export function createMulti(
  claims: Partial<Claim>[],
  envelope?: Partial<Omit<AKFUnit, "v" | "claims">>
): AKFUnit {
  const claimObjects: Claim[] = claims.map((c) => ({
    ...c,
    c: c.c!,
    t: c.t!,
    id: c.id || shortId(),
  }));
  return {
    v: "1.0",
    claims: claimObjects,
    id: unitId(),
    at: nowISO(),
    ...envelope,
  };
}

// ---------------------------------------------------------------------------
// Validation
// ---------------------------------------------------------------------------

const VALID_LABELS = new Set([
  "public",
  "internal",
  "confidential",
  "highly-confidential",
  "restricted",
]);

/** Result of AKF validation. */
export interface ValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  /** 0=invalid, 1=minimal, 2=practical, 3=full */
  level: number;
}

/** Quick ISO-8601 validation. */
function isValidISO(s: string): boolean {
  const d = new Date(s);
  return !isNaN(d.getTime());
}

/** Validate an AKF unit against all spec rules. */
export function validate(unit: AKFUnit): ValidationResult {
  const result: ValidationResult = {
    valid: true,
    errors: [],
    warnings: [],
    level: 0,
  };

  // RULE 1: v must be present
  if (!unit.v) {
    result.valid = false;
    result.errors.push("RULE 1: 'v' (version) is required");
  }

  // RULE 2: claims must be non-empty
  if (!unit.claims || unit.claims.length === 0) {
    result.valid = false;
    result.errors.push("RULE 2: 'claims' must be a non-empty array");
  }

  // RULE 3: Each claim must have c and t in range
  if (unit.claims) {
    for (let i = 0; i < unit.claims.length; i++) {
      const claim = unit.claims[i];
      if (
        typeof claim.t !== "number" ||
        claim.t < 0.0 ||
        claim.t > 1.0
      ) {
        result.valid = false;
        result.errors.push(
          `RULE 3: claim[${i}].t must be float 0.0-1.0, got ${claim.t}`
        );
      }
    }
  }

  // RULE 4: tier must be 1-5
  if (unit.claims) {
    for (let i = 0; i < unit.claims.length; i++) {
      const claim = unit.claims[i];
      if (
        claim.tier !== undefined &&
        (claim.tier < 1 || claim.tier > 5)
      ) {
        result.valid = false;
        result.errors.push(
          `RULE 4: claim[${i}].tier must be 1-5, got ${claim.tier}`
        );
      }
    }
  }

  // RULE 5: label must be valid
  if (unit.label !== undefined && !VALID_LABELS.has(unit.label)) {
    result.valid = false;
    result.errors.push(`RULE 5: invalid label '${unit.label}'`);
  }

  // RULE 7: provenance hops sequential
  if (unit.prov) {
    for (let i = 0; i < unit.prov.length; i++) {
      if (unit.prov[i].hop !== i) {
        result.valid = false;
        result.errors.push(
          `RULE 7: provenance hop[${i}] has hop=${unit.prov[i].hop}, expected ${i}`
        );
      }
    }
  }

  // RULE 8: pen must be negative
  if (unit.prov) {
    for (let i = 0; i < unit.prov.length; i++) {
      const hop = unit.prov[i];
      if (hop.pen !== undefined && hop.pen >= 0) {
        result.valid = false;
        result.errors.push(
          `RULE 8: provenance hop[${i}].pen must be negative, got ${hop.pen}`
        );
      }
    }
  }

  // RULE 9: AI + tier 5 should have risk (warning)
  if (unit.claims) {
    for (let i = 0; i < unit.claims.length; i++) {
      const claim = unit.claims[i];
      if (claim.ai && claim.tier === 5 && !claim.risk) {
        result.warnings.push(
          `RULE 9: claim[${i}] is AI-generated tier 5 but has no risk description`
        );
      }
    }
  }

  // RULE 10: hash prefix
  if (unit.hash !== undefined) {
    if (!/^(sha256|sha3-512|blake3):.*$/.test(unit.hash)) {
      result.valid = false;
      result.errors.push(
        `RULE 10: hash must be prefixed with algorithm, got '${unit.hash}'`
      );
    }
  }

  // RULE 11: timestamps valid ISO-8601
  if (unit.at) {
    if (!isValidISO(unit.at)) {
      result.valid = false;
      result.errors.push(`RULE 11: invalid timestamp '${unit.at}'`);
    }
  }

  if (unit.prov) {
    for (let i = 0; i < unit.prov.length; i++) {
      if (!isValidISO(unit.prov[i].at)) {
        result.valid = false;
        result.errors.push(
          `RULE 11: invalid timestamp in prov[${i}].at '${unit.prov[i].at}'`
        );
      }
    }
  }

  // Determine level
  if (result.valid) {
    const hasProv = Boolean(unit.prov && unit.prov.length > 0);
    const hasSources = unit.claims
      ? unit.claims.some((c) => c.src)
      : false;
    const hasLabel = unit.label !== undefined;
    const hasHash = unit.hash !== undefined;

    if (hasProv && hasHash && hasLabel && hasSources) {
      result.level = 3; // Full
    } else if (hasSources || hasLabel) {
      result.level = 2; // Practical
    } else {
      result.level = 1; // Minimal
    }
  }

  return result;
}

// ---------------------------------------------------------------------------
// Serialization
// ---------------------------------------------------------------------------

/** Serialize an AKF unit to compact JSON, stripping null/undefined values. */
export function toJSON(unit: AKFUnit, indent?: number): string {
  return JSON.stringify(stripNulls(unit), null, indent);
}

/** Parse a JSON string into an AKF unit. */
export function fromJSON(json: string): AKFUnit {
  return JSON.parse(json) as AKFUnit;
}
