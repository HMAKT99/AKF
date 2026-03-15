/**
 * AKF Core — self-contained trust scoring, audit, detection, and metadata types.
 * Mirrors the Python SDK's trust, compliance, and detection logic (v1.1).
 */

// ---------------------------------------------------------------------------
// Interfaces
// ---------------------------------------------------------------------------

export interface AKFOrigin {
  type: string;
  model?: string;
  version?: string;
  provider?: string;
}

export interface AKFReview {
  reviewer: string;
  verdict?: "approved" | "rejected" | "needs_changes";
  comment?: string;
  at?: string;
  timestamp?: string;
}

export interface AKFFreshness {
  retrieved_at?: string;
  valid_until?: string;
  refresh_url?: string;
  stale_after_hours?: number;
}

export interface AKFClaim {
  id?: string;
  content: string;
  confidence: number;
  source?: string;
  authority_tier?: number;
  verified?: boolean;
  ai_generated?: boolean;
  risk?: string;
  evidence?: string[];
  reasoning?: string;
  origin?: AKFOrigin | string;
  reviews?: AKFReview[];
  expires_at?: string;
  last_verified?: string;
  freshness?: AKFFreshness;
  decay_half_life?: number;
  fidelity?: { headline?: string; summary?: string; full?: string };
  made_by?: { actor: string; role?: string; at?: string }[];
  cost_metadata?: { input_tokens?: number; output_tokens?: number; model?: string; cost_usd?: number };
  annotations?: { key: string; value: unknown; scope?: string; at?: string }[];
  contradicts?: string;
  supersedes?: string;
  depends_on?: string[];
  relationship?: string;
  calibration?: { method?: string; verifier?: string; verified_at?: string };
}

export interface AKFProvHop {
  hop: number;
  actor: string;
  action: string;
  timestamp: string;
  claims_added?: string[];
  claims_removed?: string[];
  penalty?: number;
}

export interface AKFMetadata {
  version?: string;
  id?: string;
  author?: string;
  classification?: string;
  claims: AKFClaim[];
  provenance?: AKFProvHop[];
  integrity_hash?: string;
  created?: string;
  ttl?: number;
  model?: string;
  agent?: string;
  allow_external?: boolean;
  inherit_classification?: boolean;
  reviews?: AKFReview[];
}

export interface TrustResult {
  score: number;
  decision: "ACCEPT" | "LOW" | "REJECT";
}

export interface AuditCheck {
  check: string;
  passed: boolean;
}

export interface AuditResult {
  compliant: boolean;
  score: number;
  checks: AuditCheck[];
  recommendations: string[];
}

export interface DetectionResult {
  detection_class: string;
  triggered: boolean;
  severity: "critical" | "high" | "medium" | "low" | "info";
  findings: string[];
  affected_claims: string[];
  recommendation: string;
}

export interface DetectionReport {
  results: DetectionResult[];
  triggered_count: number;
  critical_count: number;
  high_count: number;
  clean: boolean;
}

// ---------------------------------------------------------------------------
// Constants (matching Python SDK)
// ---------------------------------------------------------------------------

const AUTHORITY_WEIGHTS: Record<number, number> = {
  1: 1.0,
  2: 0.85,
  3: 0.7,
  4: 0.5,
  5: 0.3,
};

const ORIGIN_WEIGHTS: Record<string, number> = {
  human: 1.0,
  ai_supervised_by_human: 0.9,
  collaboration: 0.85,
  human_assisted_by_ai: 0.85,
  ai: 0.7,
  multi_agent: 0.6,
  ai_chain: 0.5,
};

const GROUNDING_BONUS = 0.05; // per evidence piece, max 0.15
const REVIEW_BONUS: Record<string, number> = {
  approved: 0.1,
  needs_changes: 0.0,
  rejected: -0.2,
};

// Matches Python security.py HIERARCHY
const CLASSIFICATION_RANK: Record<string, number> = {
  public: 0,
  internal: 1,
  confidential: 2,
  "highly-confidential": 3,
  restricted: 4,
};

// ---------------------------------------------------------------------------
// Trust computation (v1.1 — matches Python trust.py)
// ---------------------------------------------------------------------------

export function effectiveTrust(claim: AKFClaim): TrustResult {
  const conf = claim.confidence;
  const tier = claim.authority_tier ?? 3;
  const authority = AUTHORITY_WEIGHTS[tier] ?? 0.7;

  // Origin weight
  let originWeight = 1.0;
  if (claim.origin) {
    const originType = typeof claim.origin === "string" ? claim.origin : claim.origin.type;
    originWeight = ORIGIN_WEIGHTS[originType] ?? 0.7;
  }

  // Base score
  let score = conf * authority * originWeight;

  // Grounding bonus: +0.05 per evidence, max 0.15
  const evCount = claim.evidence?.length ?? 0;
  score += Math.min(evCount * GROUNDING_BONUS, 0.15);

  // Review bonus
  if (claim.reviews) {
    for (const review of claim.reviews) {
      const verdict = review.verdict ?? "approved";
      score += REVIEW_BONUS[verdict] ?? 0;
    }
  }

  // Clamp to [0, 1]
  score = Math.max(0, Math.min(1, score));

  let decision: TrustResult["decision"];
  if (score >= 0.7) decision = "ACCEPT";
  else if (score >= 0.4) decision = "LOW";
  else decision = "REJECT";
  return { score, decision };
}

export function trustColor(confidence: number): string {
  if (confidence >= 0.8) return "#22c55e";
  if (confidence >= 0.5) return "#eab308";
  return "#ef4444";
}

export function trustLabel(confidence: number): string {
  if (confidence >= 0.8) return "High";
  if (confidence >= 0.5) return "Medium";
  return "Low";
}

export function overallTrust(claims: AKFClaim[]): number {
  if (claims.length === 0) return 0;
  const sum = claims.reduce((acc, c) => acc + c.confidence, 0);
  return sum / claims.length;
}

// ---------------------------------------------------------------------------
// Freshness helpers (matching Python trust.py)
// ---------------------------------------------------------------------------

function getExpiryString(claim: AKFClaim): string | null {
  if (claim.expires_at) return claim.expires_at;
  if (claim.freshness?.valid_until) return claim.freshness.valid_until;
  return null;
}

function isExpired(claim: AKFClaim): boolean {
  const expires = getExpiryString(claim);
  if (!expires) return false;
  try {
    return Date.now() > new Date(expires).getTime();
  } catch { return false; }
}

function freshnessStatus(claim: AKFClaim): "fresh" | "stale" | "expired" | "no_expiry" {
  if (!getExpiryString(claim)) return "no_expiry";
  if (isExpired(claim)) return "expired";
  if (!claim.last_verified) return "stale";
  return "fresh";
}

// ---------------------------------------------------------------------------
// Audit
// ---------------------------------------------------------------------------

export function audit(meta: AKFMetadata): AuditResult {
  const checks: AuditCheck[] = [];
  let scorePoints = 0;
  let maxPoints = 0;
  const recommendations: string[] = [];

  maxPoints++;
  const hasProv = !!meta.provenance && meta.provenance.length > 0;
  checks.push({ check: "provenance_present", passed: hasProv });
  if (hasProv) scorePoints++;
  else recommendations.push("Add provenance to track data lineage");

  maxPoints++;
  const hasHash = !!meta.integrity_hash;
  checks.push({ check: "integrity_hash", passed: hasHash });
  if (hasHash) scorePoints++;
  else recommendations.push("Compute integrity hash for tamper detection");

  maxPoints++;
  const hasClass = !!meta.classification;
  checks.push({ check: "classification_set", passed: hasClass });
  if (hasClass) scorePoints++;
  else recommendations.push("Set security classification");

  maxPoints++;
  const allSourced = meta.claims.every(
    (c) => c.source && c.source !== "unspecified"
  );
  checks.push({ check: "all_claims_sourced", passed: allSourced });
  if (allSourced) scorePoints++;
  else recommendations.push("Add source attribution to all claims");

  maxPoints++;
  const aiLabeled = meta.claims.every((c) => c.ai_generated !== undefined);
  checks.push({ check: "ai_claims_labeled", passed: aiLabeled });
  if (aiLabeled) scorePoints++;

  maxPoints++;
  const riskyAi = meta.claims.filter(
    (c) => c.ai_generated && (c.authority_tier ?? 3) >= 4
  );
  const allRiskyDescribed =
    riskyAi.length === 0 || riskyAi.every((c) => !!c.risk);
  checks.push({ check: "ai_risk_described", passed: allRiskyDescribed });
  if (allRiskyDescribed) scorePoints++;
  else recommendations.push("Add risk descriptions to AI-generated speculative claims");

  maxPoints++;
  const validStructure = meta.claims.length > 0 && meta.claims.every(
    (c) => c.content && c.confidence >= 0 && c.confidence <= 1
  );
  checks.push({ check: "valid_structure", passed: validStructure });
  if (validStructure) scorePoints++;

  const score = maxPoints > 0 ? scorePoints / maxPoints : 0;

  return {
    compliant: score >= 0.7,
    score: Math.round(score * 100) / 100,
    checks,
    recommendations,
  };
}

export function createDefaultMetadata(): AKFMetadata {
  return {
    version: "1.0",
    id: crypto.randomUUID(),
    classification: "internal",
    claims: [],
    provenance: [
      {
        hop: 1,
        actor: "office-addin",
        action: "created",
        timestamp: new Date().toISOString(),
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// Detection Class 1: AI Content Without Review
// ---------------------------------------------------------------------------

function detectAiWithoutReview(meta: AKFMetadata): DetectionResult {
  const findings: string[] = [];
  const affected: string[] = [];

  const aiClaims = meta.claims.filter((c) => c.ai_generated);
  if (aiClaims.length === 0) {
    return {
      detection_class: "ai_content_without_review",
      triggered: false,
      severity: "info",
      findings: ["No AI-generated claims found"],
      affected_claims: [],
      recommendation: "",
    };
  }

  // Check unit-level reviews (mirrors Python: unit_has_review = bool(unit.reviews))
  const unitHasReview = !!meta.reviews && meta.reviews.length > 0;

  for (const claim of aiClaims) {
    const claimHasReview = claim.reviews && claim.reviews.length > 0;
    if (!claimHasReview && !unitHasReview) {
      const cid = claim.id || "unknown";
      affected.push(cid);
      const preview = claim.content.length > 60
        ? claim.content.slice(0, 60) + "..."
        : claim.content;
      findings.push(`AI claim [${cid}] has no human review: "${preview}"`);
    }
  }

  const triggered = affected.length > 0;
  return {
    detection_class: "ai_content_without_review",
    triggered,
    severity: triggered ? "high" : "info",
    findings: findings.length > 0 ? findings : ["All AI content has been reviewed"],
    affected_claims: affected,
    recommendation: triggered
      ? "Add human review stamps to AI-generated claims before distribution."
      : "",
  };
}

// ---------------------------------------------------------------------------
// Detection Class 2: Trust Below Threshold
// ---------------------------------------------------------------------------

function detectTrustBelowThreshold(meta: AKFMetadata, threshold = 0.7): DetectionResult {
  const findings: string[] = [];
  const affected: string[] = [];

  for (const claim of meta.claims) {
    const trust = effectiveTrust(claim);
    if (trust.score < threshold) {
      const cid = claim.id || "unknown";
      affected.push(cid);
      findings.push(
        `Claim [${cid}] trust ${trust.score.toFixed(2)} < threshold ${threshold} (decision: ${trust.decision})`
      );
    }
  }

  const triggered = affected.length > 0;
  return {
    detection_class: "trust_below_threshold",
    triggered,
    severity: triggered ? "high" : "info",
    findings: findings.length > 0 ? findings : [`All claims meet trust threshold ${threshold}`],
    affected_claims: affected,
    recommendation: triggered
      ? "Review low-trust claims and add evidence or human verification."
      : "",
  };
}

// ---------------------------------------------------------------------------
// Detection Class 3: Hallucination Risk
// ---------------------------------------------------------------------------

function detectHallucinationRisk(meta: AKFMetadata): DetectionResult {
  const findings: string[] = [];
  const affected: string[] = [];

  for (const claim of meta.claims) {
    const risks: string[] = [];
    const cid = claim.id || "unknown";

    if (claim.ai_generated && claim.confidence < 0.5) {
      risks.push(`low confidence (${claim.confidence.toFixed(2)})`);
    }
    if (claim.ai_generated && (!claim.evidence || claim.evidence.length === 0)) {
      risks.push("no evidence grounding");
    }
    if (claim.ai_generated && (!claim.source || claim.source === "unspecified")) {
      risks.push("no source attribution");
    }
    if (claim.ai_generated && claim.authority_tier !== undefined && claim.authority_tier >= 5) {
      risks.push(`lowest authority tier (${claim.authority_tier})`);
    }

    if (risks.length > 0) {
      affected.push(cid);
      const preview = claim.content.length > 50
        ? claim.content.slice(0, 50) + "..."
        : claim.content;
      findings.push(`Claim [${cid}] "${preview}": ${risks.join(", ")}`);
    }
  }

  const triggered = affected.length > 0;
  return {
    detection_class: "hallucination_risk",
    triggered,
    severity: triggered ? "critical" : "info",
    findings: findings.length > 0 ? findings : ["No hallucination risk indicators found"],
    affected_claims: affected,
    recommendation: triggered
      ? "Add evidence grounding, source attribution, and human review to flagged claims."
      : "",
  };
}

// ---------------------------------------------------------------------------
// Detection Class 4: Knowledge Laundering
// ---------------------------------------------------------------------------

function detectKnowledgeLaundering(meta: AKFMetadata): DetectionResult {
  const findings: string[] = [];
  const affected: string[] = [];

  if (!meta.classification || meta.classification === "public") {
    for (const claim of meta.claims) {
      if (claim.ai_generated && !claim.risk) {
        const cid = claim.id || "unknown";
        affected.push(cid);
        findings.push(`AI claim [${cid}] in public unit without risk disclosure`);
      }
    }
  }

  for (const claim of meta.claims) {
    if (
      claim.ai_generated &&
      claim.authority_tier !== undefined &&
      claim.authority_tier <= 2 &&
      !claim.origin
    ) {
      const cid = claim.id || "unknown";
      if (!affected.includes(cid)) {
        affected.push(cid);
        findings.push(
          `AI claim [${cid}] has high authority (tier ${claim.authority_tier}) but no origin tracking`
        );
      }
    }
  }

  if (meta.provenance) {
    for (const hop of meta.provenance) {
      if (["downgraded", "declassified", "reclassified"].includes(hop.action)) {
        findings.push(
          `Provenance hop by '${hop.actor}' shows suspicious action: '${hop.action}'`
        );
      }
    }
  }

  if (meta.agent) {
    const unlabeled = meta.claims.filter(
      (c) => c.ai_generated === undefined || c.ai_generated === false
    );
    for (const claim of unlabeled) {
      const cid = claim.id || "unknown";
      if (!affected.includes(cid)) {
        affected.push(cid);
        findings.push(
          `Unit has agent '${meta.agent}' but claim [${cid}] not labeled as AI-generated`
        );
      }
    }
  }

  const triggered = findings.length > 0;
  return {
    detection_class: "knowledge_laundering",
    triggered,
    severity: triggered ? "critical" : "info",
    findings: findings.length > 0 ? findings : ["No knowledge laundering indicators found"],
    affected_claims: affected,
    recommendation: triggered
      ? "Ensure all AI content is properly labeled with origin tracking and risk descriptions."
      : "",
  };
}

// ---------------------------------------------------------------------------
// Detection Class 5: Classification Downgrade
// ---------------------------------------------------------------------------

function detectClassificationDowngrade(meta: AKFMetadata): DetectionResult {
  const findings: string[] = [];

  if (meta.provenance) {
    for (let i = 0; i < meta.provenance.length; i++) {
      const hop = meta.provenance[i];
      if (["downgraded", "declassified", "reclassified"].includes(hop.action)) {
        findings.push(
          `Hop ${i} by '${hop.actor}': classification action '${hop.action}'`
        );
      }
    }
  }

  if (
    meta.inherit_classification === false &&
    meta.classification &&
    ["public", "internal"].includes(meta.classification)
  ) {
    findings.push(
      `Classification inheritance disabled on '${meta.classification}' unit — derived documents can downgrade freely`
    );
  }

  if (
    meta.allow_external &&
    meta.classification &&
    (CLASSIFICATION_RANK[meta.classification] ?? 0) >= CLASSIFICATION_RANK["confidential"]
  ) {
    findings.push(`External sharing enabled on '${meta.classification}' unit`);
  }

  const triggered = findings.length > 0;
  return {
    detection_class: "classification_downgrade",
    triggered,
    severity: triggered ? "critical" : "info",
    findings: findings.length > 0 ? findings : ["Classification integrity maintained"],
    affected_claims: [],
    recommendation: triggered
      ? "Enable inherit_classification and review provenance for unauthorized changes."
      : "",
  };
}

// ---------------------------------------------------------------------------
// Detection Class 6: Stale Claims (using freshness_status like Python)
// ---------------------------------------------------------------------------

function detectStaleClaims(meta: AKFMetadata): DetectionResult {
  const findings: string[] = [];
  const affected: string[] = [];
  const now = Date.now();

  for (const claim of meta.claims) {
    const cid = claim.id || "unknown";
    const status = freshnessStatus(claim);

    if (status === "expired") {
      affected.push(cid);
      findings.push(`Claim [${cid}] has expired freshness`);
    } else if (status === "stale") {
      affected.push(cid);
      findings.push(`Claim [${cid}] is stale (past recommended refresh)`);
    }

    // Also check stale_after_hours from freshness object
    if (claim.freshness?.stale_after_hours && claim.freshness?.retrieved_at) {
      try {
        const retrievedMs = new Date(claim.freshness.retrieved_at).getTime();
        const hoursSince = (now - retrievedMs) / (1000 * 60 * 60);
        if (hoursSince > claim.freshness.stale_after_hours) {
          if (!affected.includes(cid)) affected.push(cid);
          findings.push(
            `Claim [${cid}] stale: ${Math.round(hoursSince)}h since retrieval (threshold: ${claim.freshness.stale_after_hours}h)`
          );
        }
      } catch { /* ignore parse errors */ }
    }

    // Check last_verified staleness (> 90 days)
    if (claim.last_verified) {
      try {
        const verifiedMs = new Date(claim.last_verified).getTime();
        const daysSince = (now - verifiedMs) / (1000 * 60 * 60 * 24);
        if (daysSince > 90) {
          if (!affected.includes(cid)) affected.push(cid);
          findings.push(`Claim [${cid}] last verified ${Math.round(daysSince)} days ago`);
        }
      } catch { /* ignore parse errors */ }
    }
  }

  // Check unit-level TTL
  if (meta.ttl !== undefined && meta.created) {
    try {
      const createdMs = new Date(meta.created).getTime();
      const ageHours = (now - createdMs) / (1000 * 60 * 60);
      if (ageHours > meta.ttl) {
        findings.push(`Unit TTL (${meta.ttl}h) exceeded — age is ${ageHours.toFixed(1)}h`);
      }
    } catch { /* ignore parse errors */ }
  }

  const triggered = findings.length > 0;
  return {
    detection_class: "stale_claims",
    triggered,
    severity: triggered ? "medium" : "info",
    findings: findings.length > 0 ? findings : ["All claims are fresh"],
    affected_claims: affected,
    recommendation: triggered
      ? "Refresh expired claims or remove stale content before distribution."
      : "",
  };
}

// ---------------------------------------------------------------------------
// Detection Class 7: Ungrounded AI Claims
// ---------------------------------------------------------------------------

function detectUngroundedClaims(meta: AKFMetadata): DetectionResult {
  const findings: string[] = [];
  const affected: string[] = [];

  for (const claim of meta.claims) {
    if (!claim.ai_generated) continue;

    const cid = claim.id || "unknown";
    const issues: string[] = [];

    if (!claim.evidence || claim.evidence.length === 0) {
      issues.push("no evidence");
    }
    if (!claim.source || claim.source === "unspecified") {
      issues.push("no source");
    }
    if (!claim.reasoning) {
      issues.push("no reasoning chain");
    }

    if (issues.length > 0) {
      affected.push(cid);
      const preview = claim.content.length > 50
        ? claim.content.slice(0, 50) + "..."
        : claim.content;
      findings.push(`Claim [${cid}] "${preview}": ${issues.join(", ")}`);
    }
  }

  const triggered = affected.length > 0;
  return {
    detection_class: "ungrounded_ai_claims",
    triggered,
    severity: triggered ? "high" : "info",
    findings: findings.length > 0 ? findings : ["All AI claims have grounding"],
    affected_claims: affected,
    recommendation: triggered
      ? "Add evidence, source references, or reasoning chains to ungrounded claims."
      : "",
  };
}

// ---------------------------------------------------------------------------
// Detection Class 8: Trust Degradation Chain
// ---------------------------------------------------------------------------

function detectTrustDegradationChain(meta: AKFMetadata): DetectionResult {
  const findings: string[] = [];

  if (!meta.provenance || meta.provenance.length < 2) {
    return {
      detection_class: "trust_degradation_chain",
      triggered: false,
      severity: "info",
      findings: ["No multi-hop provenance chain to evaluate"],
      affected_claims: [],
      recommendation: "",
    };
  }

  let totalPenalty = 0;
  for (const hop of meta.provenance) {
    if (hop.penalty !== undefined) {
      totalPenalty += hop.penalty;
    }
  }

  if (totalPenalty < -0.1) {
    findings.push(
      `Cumulative provenance penalty: ${totalPenalty.toFixed(2)} across ${meta.provenance.length} hops`
    );
  }

  for (let i = 0; i < meta.provenance.length; i++) {
    const hop = meta.provenance[i];
    if (hop.penalty !== undefined && hop.penalty < -0.1) {
      findings.push(
        `Hop ${i} by '${hop.actor}' has significant penalty: ${hop.penalty.toFixed(2)}`
      );
    }
  }

  for (const claim of meta.claims) {
    const trust = effectiveTrust(claim);
    if (trust.score < 0.4 && claim.confidence >= 0.7) {
      const cid = claim.id || "unknown";
      findings.push(
        `Claim [${cid}] original confidence ${claim.confidence.toFixed(2)} degraded to effective trust ${trust.score.toFixed(2)}`
      );
    }
  }

  const triggered = findings.length > 0;
  return {
    detection_class: "trust_degradation_chain",
    triggered,
    severity: triggered ? "high" : "info",
    findings: findings.length > 0 ? findings : ["Trust chain is healthy"],
    affected_claims: [],
    recommendation: triggered
      ? "Review provenance chain for unnecessary transformations that degrade trust."
      : "",
  };
}

// ---------------------------------------------------------------------------
// Detection Class 9: Excessive AI Concentration
// ---------------------------------------------------------------------------

function detectExcessiveAiConcentration(meta: AKFMetadata, maxAiRatio = 0.8): DetectionResult {
  const total = meta.claims.length;
  const aiCount = meta.claims.filter((c) => c.ai_generated).length;
  const aiRatio = total > 0 ? aiCount / total : 0;
  const findings: string[] = [];

  if (aiRatio > maxAiRatio) {
    findings.push(
      `AI content ratio ${Math.round(aiRatio * 100)}% exceeds threshold ${Math.round(maxAiRatio * 100)}% (${aiCount}/${total} claims are AI-generated)`
    );
  }

  if (aiCount > 1 && meta.model && aiRatio > maxAiRatio) {
    findings.push(`All AI claims attributed to single model: ${meta.model}`);
  }

  const humanCount = meta.claims.filter((c) => !c.ai_generated).length;
  if (humanCount === 0 && total > 0) {
    findings.push("No human-authored claims — document is entirely AI-generated");
  }

  const triggered = findings.length > 0;
  return {
    detection_class: "excessive_ai_concentration",
    triggered,
    severity: triggered ? "medium" : "info",
    findings: findings.length > 0
      ? findings
      : [`AI concentration ${Math.round(aiRatio * 100)}% is within acceptable range`],
    affected_claims: [],
    recommendation: triggered
      ? "Add human-authored or human-reviewed claims to balance AI concentration."
      : "",
  };
}

// ---------------------------------------------------------------------------
// Detection Class 10: Provenance Gap (1-based hop numbering)
// ---------------------------------------------------------------------------

function detectProvenanceGap(meta: AKFMetadata): DetectionResult {
  const findings: string[] = [];

  if (!meta.provenance || meta.provenance.length === 0) {
    findings.push("No provenance chain — content origin is untraceable");
  } else {
    // Check for gaps in hop numbering (1-based: hop 1, 2, 3, ...)
    for (let i = 0; i < meta.provenance.length; i++) {
      const expectedHop = i + 1;
      if (meta.provenance[i].hop !== expectedHop) {
        findings.push(
          `Provenance gap: expected hop ${expectedHop}, found hop ${meta.provenance[i].hop}`
        );
      }
    }

    const firstActor = meta.provenance[0].actor;
    if (!firstActor || ["unknown", "unspecified"].includes(firstActor)) {
      findings.push("Provenance origin actor is unknown or unspecified");
    }

    for (let i = 0; i < meta.provenance.length; i++) {
      if (!meta.provenance[i].actor) {
        findings.push(`Provenance hop ${i} has no actor`);
      }
    }
  }

  const aiWithoutOrigin = meta.claims.filter(
    (c) => c.ai_generated && !c.origin
  );
  if (aiWithoutOrigin.length > 0) {
    findings.push(`${aiWithoutOrigin.length} AI claims lack origin tracking`);
  }

  const triggered = findings.length > 0;
  return {
    detection_class: "provenance_gap",
    triggered,
    severity: triggered ? "high" : "info",
    findings: findings.length > 0 ? findings : ["Complete provenance chain with origin tracking"],
    affected_claims: [],
    recommendation: triggered
      ? "Add provenance chain and origin tracking to establish content lineage."
      : "",
  };
}

// ---------------------------------------------------------------------------
// Aggregate: Run all 10 detection classes
// ---------------------------------------------------------------------------

export function runAllDetections(meta: AKFMetadata): DetectionReport {
  const results: DetectionResult[] = [
    detectAiWithoutReview(meta),
    detectTrustBelowThreshold(meta),
    detectHallucinationRisk(meta),
    detectKnowledgeLaundering(meta),
    detectClassificationDowngrade(meta),
    detectStaleClaims(meta),
    detectUngroundedClaims(meta),
    detectTrustDegradationChain(meta),
    detectExcessiveAiConcentration(meta),
    detectProvenanceGap(meta),
  ];

  const triggered = results.filter((r) => r.triggered);
  const critical = triggered.filter((r) => r.severity === "critical");
  const high = triggered.filter((r) => r.severity === "high");

  return {
    results,
    triggered_count: triggered.length,
    critical_count: critical.length,
    high_count: high.length,
    clean: triggered.length === 0,
  };
}
