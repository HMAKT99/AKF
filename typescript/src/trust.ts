/**
 * AKF v1.0 — Trust computation engine.
 */

import type { Claim } from "./models.js";

/** Authority weights by tier. */
export const AUTHORITY_WEIGHTS: Record<number, number> = {
  1: 1.0,
  2: 0.85,
  3: 0.7,
  4: 0.5,
  5: 0.3,
};

/** Decay presets: name -> half-life in days. */
export const DECAY_PRESETS: Record<string, number> = {
  realtime: 0.001,
  daily: 1,
  weekly: 7,
  monthly: 30,
  quarterly: 90,
  annual: 365,
  legal: 1825,
  scientific: 3650,
  permanent: 365000,
};

/** Trust decision: ACCEPT, LOW, or REJECT. */
export type TrustDecision = "ACCEPT" | "LOW" | "REJECT";

/** Result of trust computation for a single claim. */
export interface TrustResult {
  score: number;
  decision: TrustDecision;
  breakdown: {
    confidence: number;
    authority: number;
    tier: number;
    decay: number;
    penalty: number;
    penalty_factor: number;
  };
}

/**
 * Compute effective trust for a single claim.
 *
 * Formula: effective_trust = t * authority_weight * temporal_decay * (1 + cumulative_penalty)
 */
export function effectiveTrust(
  claim: Claim,
  ageDays: number = 0,
  penalty: number = 0
): TrustResult {
  const confidence = claim.t;
  const tier = claim.tier !== undefined ? claim.tier : 3;
  const authority = AUTHORITY_WEIGHTS[tier] ?? 0.7;

  // Temporal decay: 0.5^(age_days / half_life_days)
  const halfLife = claim.decay || 0;
  let decay: number;
  if (halfLife > 0 && ageDays > 0) {
    decay = Math.pow(0.5, ageDays / halfLife);
  } else {
    decay = 1.0;
  }

  // Penalty factor: (1 + cumulative_penalty) where penalty is negative
  const penaltyFactor = 1.0 + penalty;

  let score = confidence * authority * decay * penaltyFactor;
  score = Math.max(0.0, Math.min(1.0, score)); // clamp

  let decision: TrustDecision;
  if (score >= 0.7) {
    decision = "ACCEPT";
  } else if (score >= 0.4) {
    decision = "LOW";
  } else {
    decision = "REJECT";
  }

  return {
    score: round4(score),
    decision,
    breakdown: {
      confidence,
      authority,
      tier,
      decay: round4(decay),
      penalty,
      penalty_factor: round4(penaltyFactor),
    },
  };
}

/** Round to 4 decimal places. */
function round4(n: number): number {
  return Math.round(n * 10000) / 10000;
}
