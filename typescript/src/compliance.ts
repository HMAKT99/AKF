/**
 * AKF v1.1 — Compliance auditing for TypeScript.
 */

import type { AKFUnit } from "./models.js";
import { validate } from "./core.js";

export interface AuditCheck {
  check: string;
  passed: boolean;
}

export interface AuditResult {
  compliant: boolean;
  score: number;
  checks: AuditCheck[];
  recommendations: string[];
  regulation: string;
}

export function audit(unit: AKFUnit, opts?: { regulation?: string }): AuditResult {
  if (opts?.regulation) {
    return checkRegulation(unit, opts.regulation);
  }

  const checks: AuditCheck[] = [];
  const recommendations: string[] = [];
  let points = 0;
  let maxPoints = 0;

  // 1. Provenance
  maxPoints++;
  const hasProv = Array.isArray(unit.prov) && unit.prov.length > 0;
  checks.push({ check: "provenance_present", passed: hasProv });
  if (hasProv) points++;
  else recommendations.push("Add provenance to track data lineage");

  // 2. Integrity hash
  maxPoints++;
  const hasHash = !!unit.hash;
  checks.push({ check: "integrity_hash", passed: hasHash });
  if (hasHash) points++;
  else recommendations.push("Compute integrity hash for tamper detection");

  // 3. Classification set
  maxPoints++;
  const hasLabel = !!unit.label;
  checks.push({ check: "classification_set", passed: hasLabel });
  if (hasLabel) points++;
  else recommendations.push("Set security classification");

  // 4. All claims sourced
  maxPoints++;
  const allSourced = unit.claims.every((c) => c.src && c.src !== "unspecified");
  checks.push({ check: "all_claims_sourced", passed: allSourced });
  if (allSourced) points++;
  else recommendations.push("Add source attribution to all claims");

  // 5. AI claims labeled
  maxPoints++;
  const aiLabeled = unit.claims.every((c) => c.ai !== undefined && c.ai !== null);
  checks.push({ check: "ai_claims_labeled", passed: aiLabeled });
  if (aiLabeled) points++;

  // 6. AI risk described
  maxPoints++;
  const riskyAi = unit.claims.filter((c) => c.ai && (c.tier ?? 3) >= 4);
  const allRisky = riskyAi.length === 0 || riskyAi.every((c) => !!c.risk);
  checks.push({ check: "ai_risk_described", passed: allRisky });
  if (allRisky) points++;
  else recommendations.push("Add risk descriptions to AI claims");

  // 7. Valid structure
  maxPoints++;
  const vr = validate(unit);
  checks.push({ check: "valid_structure", passed: vr.valid });
  if (vr.valid) points++;

  // 8. Origin tracking
  maxPoints++;
  const aiClaims = unit.claims.filter((c) => c.ai);
  const originTracked = aiClaims.length === 0 || aiClaims.every((c) => !!(c as any).origin);
  checks.push({ check: "origin_tracking", passed: originTracked });
  if (originTracked) points++;
  else recommendations.push("Add origin fields to AI claims");

  // 9. Reviews present
  maxPoints++;
  const hasReviews = !!(unit as any).reviews?.length || unit.claims.some((c) => !!(c as any).reviews?.length);
  checks.push({ check: "review_present", passed: hasReviews });
  if (hasReviews) points++;
  else recommendations.push("Add reviews for human oversight");

  // 10. Freshness valid
  maxPoints++;
  const now = new Date();
  let freshnessValid = true;
  for (const c of unit.claims) {
    if (c.exp) {
      const expDate = new Date(c.exp);
      if (expDate < now) { freshnessValid = false; break; }
    }
  }
  checks.push({ check: "freshness_valid", passed: freshnessValid });
  if (freshnessValid) points++;
  else recommendations.push("Refresh or remove expired claims");

  const score = maxPoints > 0 ? points / maxPoints : 0;
  return {
    compliant: score >= 0.7,
    score: Math.round(score * 100) / 100,
    checks,
    recommendations,
    regulation: "general",
  };
}

function checkRegulation(unit: AKFUnit, regulation: string): AuditResult {
  const checks: AuditCheck[] = [];
  const recommendations: string[] = [];
  let points = 0;
  let maxPoints = 0;

  if (regulation === "eu_ai_act") {
    // Art 13: AI transparency
    maxPoints++;
    const aiLabeled = unit.claims.every((c) => c.ai !== undefined);
    checks.push({ check: "art13_transparency", passed: aiLabeled });
    if (aiLabeled) points++;
    else recommendations.push("Label all AI-generated content (Art. 13)");

    // Art 14: Human oversight
    maxPoints++;
    const hasHuman = Array.isArray(unit.prov) && unit.prov.some((h) => h.by.slice(0, 3) !== "ai-");
    checks.push({ check: "art14_human_oversight", passed: hasHuman });
    if (hasHuman) points++;
    else recommendations.push("Add human oversight to provenance (Art. 14)");

    // Art 15: Accuracy
    maxPoints++;
    const riskyAi = unit.claims.filter((c) => c.ai && c.t < 0.5);
    const allDescribed = riskyAi.length === 0 || riskyAi.every((c) => !!c.risk);
    checks.push({ check: "art15_accuracy", passed: allDescribed });
    if (allDescribed) points++;
    else recommendations.push("Add risk descriptions for low-confidence AI (Art. 15)");

    // Art 12: Traceability
    maxPoints++;
    const hasProv = Array.isArray(unit.prov) && unit.prov.length > 0;
    checks.push({ check: "art12_traceability", passed: hasProv });
    if (hasProv) points++;
    else recommendations.push("Add provenance chain for traceability (Art. 12)");
  }

  const score = maxPoints > 0 ? points / maxPoints : 0;
  return {
    compliant: score >= 0.7,
    score: Math.round(score * 100) / 100,
    checks,
    recommendations,
    regulation,
  };
}
