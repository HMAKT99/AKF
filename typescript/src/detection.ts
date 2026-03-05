/**
 * AKF v1.1 — 10 AI-specific detection classes for enterprise security.
 *
 * Each detection class examines an AKF unit for a specific category of AI
 * content risk and returns structured findings.
 */

import type { AKFUnit, Claim } from "./models.js";
import { effectiveTrust } from "./trust.js";

export interface DetectionResult {
  detectionClass: string;
  triggered: boolean;
  severity: "critical" | "high" | "medium" | "low" | "info";
  findings: string[];
  affectedClaims: string[];
  recommendation: string;
}

export interface DetectionReport {
  results: DetectionResult[];
  triggeredCount: number;
  criticalCount: number;
  highCount: number;
  clean: boolean;
}

function claimId(c: Claim): string {
  return (c.id as string) || "unknown";
}

function preview(c: Claim, max = 50): string {
  return c.c.length > max ? c.c.slice(0, max) + "..." : c.c;
}

// 1. AI Content Without Review
export function detectAiWithoutReview(unit: AKFUnit): DetectionResult {
  const findings: string[] = [];
  const affected: string[] = [];
  const aiClaims = unit.claims.filter((c) => c.ai);
  if (!aiClaims.length) {
    return { detectionClass: "ai_content_without_review", triggered: false, severity: "info", findings: ["No AI-generated claims found"], affectedClaims: [], recommendation: "" };
  }
  for (const claim of aiClaims) {
    const hasReview = Array.isArray((claim as any).reviews) && (claim as any).reviews.length > 0;
    const unitReviews = Array.isArray((unit as any).reviews) && (unit as any).reviews.length > 0;
    if (!hasReview && !unitReviews) {
      affected.push(claimId(claim));
      findings.push(`AI claim [${claimId(claim)}] has no human review`);
    }
  }
  const triggered = affected.length > 0;
  return { detectionClass: "ai_content_without_review", triggered, severity: triggered ? "high" : "info", findings: findings.length ? findings : ["All AI content has been reviewed"], affectedClaims: affected, recommendation: triggered ? "Add human review stamps to AI-generated claims." : "" };
}

// 2. Trust Below Threshold
export function detectTrustBelowThreshold(unit: AKFUnit, threshold = 0.7): DetectionResult {
  const findings: string[] = [];
  const affected: string[] = [];
  for (const claim of unit.claims) {
    const trust = effectiveTrust(claim);
    if (trust.score < threshold) {
      affected.push(claimId(claim));
      findings.push(`Claim [${claimId(claim)}] trust ${trust.score.toFixed(2)} < ${threshold}`);
    }
  }
  const triggered = affected.length > 0;
  return { detectionClass: "trust_below_threshold", triggered, severity: triggered ? "high" : "info", findings: findings.length ? findings : [`All claims meet threshold ${threshold}`], affectedClaims: affected, recommendation: triggered ? "Review low-trust claims and add evidence." : "" };
}

// 3. Hallucination Risk
export function detectHallucinationRisk(unit: AKFUnit): DetectionResult {
  const findings: string[] = [];
  const affected: string[] = [];
  for (const claim of unit.claims) {
    if (!claim.ai) continue;
    const risks: string[] = [];
    if (claim.t < 0.5) risks.push(`low confidence (${claim.t.toFixed(2)})`);
    if (!claim.evidence || claim.evidence.length === 0) risks.push("no evidence");
    if (!claim.src || claim.src === "unspecified") risks.push("no source");
    if (claim.tier && claim.tier >= 5) risks.push(`lowest tier (${claim.tier})`);
    if (risks.length) {
      affected.push(claimId(claim));
      findings.push(`Claim [${claimId(claim)}] "${preview(claim)}": ${risks.join(", ")}`);
    }
  }
  const triggered = affected.length > 0;
  return { detectionClass: "hallucination_risk", triggered, severity: triggered ? "critical" : "info", findings: findings.length ? findings : ["No hallucination risk"], affectedClaims: affected, recommendation: triggered ? "Add evidence and source references." : "" };
}

// 4. Knowledge Laundering
export function detectKnowledgeLaundering(unit: AKFUnit): DetectionResult {
  const findings: string[] = [];
  const affected: string[] = [];
  if (unit.label === "public" || !unit.label) {
    for (const claim of unit.claims) {
      if (claim.ai && !claim.risk) {
        affected.push(claimId(claim));
        findings.push(`AI claim [${claimId(claim)}] in public unit without risk disclosure`);
      }
    }
  }
  if (unit.agent) {
    for (const claim of unit.claims) {
      if (!claim.ai) {
        const cid = claimId(claim);
        if (affected.indexOf(cid) === -1) {
          affected.push(cid);
          findings.push(`Unit has agent '${unit.agent}' but claim [${cid}] not labeled as AI`);
        }
      }
    }
  }
  const triggered = findings.length > 0;
  return { detectionClass: "knowledge_laundering", triggered, severity: triggered ? "critical" : "info", findings: findings.length ? findings : ["No laundering indicators"], affectedClaims: affected, recommendation: triggered ? "Label all AI content with origin tracking." : "" };
}

// 5. Classification Downgrade
export function detectClassificationDowngrade(unit: AKFUnit): DetectionResult {
  const findings: string[] = [];
  if (unit.prov) {
    for (let i = 0; i < unit.prov.length; i++) {
      if (["downgraded", "declassified", "reclassified"].indexOf(unit.prov[i].do) >= 0) {
        findings.push(`Hop ${i} by '${unit.prov[i].by}': action '${unit.prov[i].do}'`);
      }
    }
  }
  if (unit.inherit === false) {
    findings.push("Classification inheritance disabled");
  }
  const triggered = findings.length > 0;
  return { detectionClass: "classification_downgrade", triggered, severity: triggered ? "critical" : "info", findings: findings.length ? findings : ["Classification integrity maintained"], affectedClaims: [], recommendation: triggered ? "Enable inherit_classification." : "" };
}

// 6. Stale Claims
export function detectStaleClaims(unit: AKFUnit): DetectionResult {
  const findings: string[] = [];
  const affected: string[] = [];
  const now = new Date();
  for (const claim of unit.claims) {
    if (claim.exp) {
      const expDate = new Date(claim.exp);
      if (expDate < now) {
        affected.push(claimId(claim));
        findings.push(`Claim [${claimId(claim)}] expired at ${claim.exp}`);
      }
    }
  }
  const triggered = affected.length > 0;
  return { detectionClass: "stale_claims", triggered, severity: triggered ? "medium" : "info", findings: findings.length ? findings : ["All claims are fresh"], affectedClaims: affected, recommendation: triggered ? "Refresh or remove expired claims." : "" };
}

// 7. Ungrounded AI Claims
export function detectUngroundedClaims(unit: AKFUnit): DetectionResult {
  const findings: string[] = [];
  const affected: string[] = [];
  for (const claim of unit.claims) {
    if (!claim.ai) continue;
    const issues: string[] = [];
    if (!claim.evidence || claim.evidence.length === 0) issues.push("no evidence");
    if (!claim.src || claim.src === "unspecified") issues.push("no source");
    if (issues.length) {
      affected.push(claimId(claim));
      findings.push(`Claim [${claimId(claim)}] "${preview(claim)}": ${issues.join(", ")}`);
    }
  }
  const triggered = affected.length > 0;
  return { detectionClass: "ungrounded_ai_claims", triggered, severity: triggered ? "high" : "info", findings: findings.length ? findings : ["All AI claims grounded"], affectedClaims: affected, recommendation: triggered ? "Add evidence and source references." : "" };
}

// 8. Trust Degradation Chain
export function detectTrustDegradationChain(unit: AKFUnit): DetectionResult {
  const findings: string[] = [];
  if (!unit.prov || unit.prov.length < 2) {
    return { detectionClass: "trust_degradation_chain", triggered: false, severity: "info", findings: ["No multi-hop chain"], affectedClaims: [], recommendation: "" };
  }
  let totalPenalty = 0;
  for (const hop of unit.prov) {
    if (hop.pen) totalPenalty += hop.pen;
    if (hop.pen && hop.pen < -0.1) {
      findings.push(`Hop by '${hop.by}' has penalty ${hop.pen.toFixed(2)}`);
    }
  }
  if (totalPenalty < -0.1) {
    findings.push(`Cumulative penalty: ${totalPenalty.toFixed(2)} across ${unit.prov.length} hops`);
  }
  const triggered = findings.length > 0;
  return { detectionClass: "trust_degradation_chain", triggered, severity: triggered ? "high" : "info", findings: findings.length ? findings : ["Trust chain healthy"], affectedClaims: [], recommendation: triggered ? "Review provenance for unnecessary transformations." : "" };
}

// 9. Excessive AI Concentration
export function detectExcessiveAiConcentration(unit: AKFUnit, maxRatio = 0.8): DetectionResult {
  const total = unit.claims.length;
  const aiCount = unit.claims.filter((c) => c.ai).length;
  const ratio = total > 0 ? aiCount / total : 0;
  const findings: string[] = [];
  if (ratio > maxRatio) {
    findings.push(`AI ratio ${(ratio * 100).toFixed(0)}% exceeds ${(maxRatio * 100).toFixed(0)}% (${aiCount}/${total})`);
  }
  if (aiCount === total && total > 0) {
    findings.push("No human-authored claims");
  }
  const triggered = findings.length > 0;
  return { detectionClass: "excessive_ai_concentration", triggered, severity: triggered ? "medium" : "info", findings: findings.length ? findings : [`AI concentration ${(ratio * 100).toFixed(0)}% within range`], affectedClaims: [], recommendation: triggered ? "Add human-reviewed claims." : "" };
}

// 10. Provenance Gap
export function detectProvenanceGap(unit: AKFUnit): DetectionResult {
  const findings: string[] = [];
  if (!unit.prov || unit.prov.length === 0) {
    findings.push("No provenance chain");
  } else {
    for (let i = 0; i < unit.prov.length; i++) {
      if (unit.prov[i].hop !== i) findings.push(`Gap: expected hop ${i}, found ${unit.prov[i].hop}`);
      if (!unit.prov[i].by) findings.push(`Hop ${i} has no actor`);
    }
    if (["unknown", "unspecified"].indexOf(unit.prov[0].by) >= 0) {
      findings.push("Origin actor is unknown");
    }
  }
  const triggered = findings.length > 0;
  return { detectionClass: "provenance_gap", triggered, severity: triggered ? "high" : "info", findings: findings.length ? findings : ["Complete provenance chain"], affectedClaims: [], recommendation: triggered ? "Add provenance chain." : "" };
}

// Run all 10 detection classes
export function runAllDetections(unit: AKFUnit, opts?: { trustThreshold?: number; maxAiRatio?: number }): DetectionReport {
  const results: DetectionResult[] = [
    detectAiWithoutReview(unit),
    detectTrustBelowThreshold(unit, opts?.trustThreshold),
    detectHallucinationRisk(unit),
    detectKnowledgeLaundering(unit),
    detectClassificationDowngrade(unit),
    detectStaleClaims(unit),
    detectUngroundedClaims(unit),
    detectTrustDegradationChain(unit),
    detectExcessiveAiConcentration(unit, opts?.maxAiRatio),
    detectProvenanceGap(unit),
  ];
  const triggered = results.filter((r) => r.triggered);
  return {
    results,
    triggeredCount: triggered.length,
    criticalCount: triggered.filter((r) => r.severity === "critical").length,
    highCount: triggered.filter((r) => r.severity === "high").length,
    clean: triggered.length === 0,
  };
}
