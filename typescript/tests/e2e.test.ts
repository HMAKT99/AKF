/**
 * End-to-End Test: Woodgrove Bank Q3 Earnings Analysis
 * =====================================================
 *
 * This test walks through the complete hackathon demo scenario:
 *   Sarah (analyst) -> Copilot (AI enrichment) -> Review -> Agent consumption
 *
 * It validates the full AKF lifecycle: create, enrich, review, classify,
 * share control, transform, and provenance auditing.
 */

import { describe, it, expect } from "vitest";
import {
  AKFBuilder,
  AKFTransformer,
  validate,
  addHop,
  computeIntegrityHash,
  validateChain,
  formatTree,
  validateInheritance,
  canShareExternal,
  toJSON,
  fromJSON,
} from "../src/index.js";
import type { AKFUnit, Claim } from "../src/index.js";

describe("Woodgrove E2E", () => {
  it("should run the full scenario", () => {
    // ============================================================
    // STEP 1: Sarah creates Q3-Analysis.akf with 3 initial claims
    // ============================================================
    const q3Analysis = new AKFBuilder()
      .by("sarah@woodgrove.com")
      .label("confidential")
      .inherit(true)
      .claim("Woodgrove Q3 revenue was $4.2B, up 12% YoY", 0.98, {
        src: "SEC 10-Q Filing",
        tier: 1,
        ver: true,
        ver_by: "sarah@woodgrove.com",
      })
      .tag("revenue", "Q3")
      .claim("Cloud segment grew 15-18% driven by AI workloads", 0.85, {
        src: "Gartner Cloud Report 2025",
        tier: 2,
      })
      .tag("cloud", "growth")
      .claim(
        "Enterprise pipeline is strong with 3 deals over $50M",
        0.72,
        {
          src: "Internal CRM estimate",
          tier: 4,
        }
      )
      .tag("pipeline")
      .build();

    // Verify initial state
    expect(q3Analysis.v).toBe("1.0");
    expect(q3Analysis.by).toBe("sarah@woodgrove.com");
    expect(q3Analysis.label).toBe("confidential");
    expect(q3Analysis.inherit).toBe(true);
    expect(q3Analysis.claims).toHaveLength(3);
    expect(q3Analysis.claims[0].t).toBe(0.98);
    expect(q3Analysis.claims[0].ver).toBe(true);

    // Verify initial provenance (hop 0: created)
    expect(q3Analysis.prov).toBeDefined();
    expect(q3Analysis.prov!).toHaveLength(1);
    expect(q3Analysis.prov![0].by).toBe("sarah@woodgrove.com");
    expect(q3Analysis.prov![0].do).toBe("created");

    // Verify initial validation
    const step1Result = validate(q3Analysis);
    expect(step1Result.valid).toBe(true);

    // ============================================================
    // STEP 2: Copilot enriches with 2 AI claims
    // ============================================================
    const copilotClaim1: Claim = {
      c: "AI copilot adoption rate is 34% across Fortune 500",
      t: 0.78,
      id: "cop1",
      src: "McKinsey AI Survey 2025",
      tier: 2,
      ai: true,
      tags: ["AI", "adoption"],
    };

    const copilotClaim2: Claim = {
      c: "H2 revenue will accelerate to 25% growth based on pipeline momentum",
      t: 0.63,
      id: "cop2",
      src: "Copilot inference from Q1-Q3 trend",
      tier: 5,
      ai: true,
      risk: "AI inference — extrapolated from limited data points. Not supported by analyst consensus.",
      tags: ["forecast", "AI-generated"],
    };

    // Add Copilot's claims to the unit
    const enrichedClaims = [...q3Analysis.claims, copilotClaim1, copilotClaim2];
    let enriched: AKFUnit = { ...q3Analysis, claims: enrichedClaims };

    // Add provenance hop for Copilot's enrichment
    enriched = addHop(enriched, "copilot-m365", "enriched", {
      adds: [copilotClaim1.id!, copilotClaim2.id!],
    });

    // Verify enrichment
    expect(enriched.claims).toHaveLength(5);
    expect(enriched.prov!).toHaveLength(2);
    expect(enriched.prov![1].by).toBe("copilot-m365");
    expect(enriched.prov![1].do).toBe("enriched");

    const aiClaims = enriched.claims.filter((c) => c.ai);
    expect(aiClaims).toHaveLength(2);

    // The flagged claim should have a risk description
    const flagged = enriched.claims.filter((c) => c.risk);
    expect(flagged).toHaveLength(1);
    expect(flagged[0].risk!.toLowerCase()).toContain("inference");

    // ============================================================
    // STEP 3: Sarah reviews — confirms 1, rejects 1, adds 1
    // ============================================================
    const rejectedId = copilotClaim2.id;

    // Remove the rejected claim
    let reviewedClaims = enriched.claims.filter(
      (c) => c.id !== rejectedId
    );

    // Sarah adds her own claim
    const sarahNewClaim: Claim = {
      c: "Key competitor Contoso lost 2 enterprise accounts to Woodgrove in Q3",
      t: 0.8,
      id: "sarah-new",
      src: "Sales team debrief",
      tier: 3,
      ver: true,
      ver_by: "sarah@woodgrove.com",
      tags: ["competitive"],
    };
    reviewedClaims = [...reviewedClaims, sarahNewClaim];

    // Update the unit
    let reviewed: AKFUnit = { ...enriched, claims: reviewedClaims };

    // Add review provenance hop
    reviewed = addHop(reviewed, "sarah@woodgrove.com", "reviewed", {
      adds: [sarahNewClaim.id!],
      drops: [rejectedId!],
    });

    // Verify review
    expect(reviewed.claims).toHaveLength(5); // 3 original + 1 AI confirmed + 1 new
    expect(reviewed.prov!).toHaveLength(3); // created, enriched, reviewed

    // The rejected claim should be gone
    const remainingIds = new Set(reviewed.claims.map((c) => c.id));
    expect(remainingIds.has(rejectedId)).toBe(false);

    // The new claim should be present
    expect(remainingIds.has(sarahNewClaim.id)).toBe(true);

    // Review provenance should track adds and drops
    const reviewHop = reviewed.prov![2];
    expect(reviewHop.by).toBe("sarah@woodgrove.com");
    expect(reviewHop.do).toBe("reviewed");
    expect(reviewHop.adds).toContain(sarahNewClaim.id);
    expect(reviewHop.drops).toContain(rejectedId);

    // ============================================================
    // STEP 4: Validate classification inheritance
    // ============================================================
    expect(reviewed.label).toBe("confidential");
    expect(reviewed.inherit).toBe(true);

    // A public child should be REJECTED
    const publicChild: AKFUnit = {
      v: "1.0",
      claims: [{ c: "public leak", t: 0.5 }],
      label: "public",
    };
    expect(validateInheritance(reviewed, publicChild)).toBe(false);

    // A confidential child should be ACCEPTED
    const confidentialChild: AKFUnit = {
      v: "1.0",
      claims: [{ c: "ok", t: 0.5 }],
      label: "confidential",
    };
    expect(validateInheritance(reviewed, confidentialChild)).toBe(true);

    // A restricted child should be ACCEPTED (higher is fine)
    const restrictedChild: AKFUnit = {
      v: "1.0",
      claims: [{ c: "ok", t: 0.5 }],
      label: "restricted",
    };
    expect(validateInheritance(reviewed, restrictedChild)).toBe(true);

    // ============================================================
    // STEP 5: Simulate external share -> Purview blocks
    // ============================================================
    expect(canShareExternal(reviewed)).toBe(false);

    // AI claims are present
    const aiClaimsPresent = reviewed.claims.some((c) => c.ai);
    expect(aiClaimsPresent).toBe(true);

    // ============================================================
    // STEP 6: Research agent consumes -> Weekly-Brief.akf
    // ============================================================
    const weeklyBrief = new AKFTransformer(reviewed)
      .filter(0.5) // Filter by effective trust
      .penalty(-0.03) // Apply transform penalty
      .by("research-agent")
      .build();

    // The weekly brief should only contain high-trust claims
    expect(weeklyBrief.claims.length).toBeGreaterThan(0);
    expect(weeklyBrief.claims.length).toBeLessThan(reviewed.claims.length);

    // Classification should be inherited
    expect(weeklyBrief.label).toBe("confidential");
    expect(validateInheritance(reviewed, weeklyBrief)).toBe(true);

    // Provenance should extend the chain
    expect(weeklyBrief.prov!).toHaveLength(reviewed.prov!.length + 1);
    const agentHop = weeklyBrief.prov![weeklyBrief.prov!.length - 1];
    expect(agentHop.by).toBe("research-agent");
    expect(agentHop.do).toBe("consumed");

    // Parent reference should exist
    expect((weeklyBrief.meta as Record<string, unknown>)["parent_id"]).toBe(
      reviewed.id
    );

    // Trust scores should be reduced by penalty
    for (const claim of weeklyBrief.claims) {
      const original = reviewed.claims.find((c) => c.id === claim.id)!;
      expect(claim.t).toBeCloseTo(original.t - 0.03, 3);
    }

    // Brief should validate
    const briefResult = validate(weeklyBrief);
    expect(briefResult.valid).toBe(true);

    // ============================================================
    // STEP 7: Validate provenance chain across all hops
    // ============================================================
    expect(validateChain(weeklyBrief.prov!)).toBe(true);

    // Verify the complete chain narrative
    const chain = weeklyBrief.prov!;
    expect(chain[0].do).toBe("created");
    expect(chain[1].do).toBe("enriched");
    expect(chain[2].do).toBe("reviewed");
    expect(chain[3].do).toBe("consumed");

    expect(chain[0].by).toBe("sarah@woodgrove.com");
    expect(chain[1].by).toBe("copilot-m365");
    expect(chain[2].by).toBe("sarah@woodgrove.com");
    expect(chain[3].by).toBe("research-agent");

    // Pretty-print the provenance tree
    const tree = formatTree(weeklyBrief);
    expect(tree).toContain("sarah@woodgrove.com");
    expect(tree).toContain("copilot-m365");
    expect(tree).toContain("research-agent");

    // ============================================================
    // STEP 8: Validate integrity hashes
    // ============================================================
    expect(reviewed.hash).toBeDefined();
    expect(reviewed.hash!.startsWith("sha256:")).toBe(true);

    expect(weeklyBrief.hash).toBeDefined();
    expect(weeklyBrief.hash!.startsWith("sha256:")).toBe(true);

    // Hashes should be different (different content)
    expect(reviewed.hash).not.toBe(weeklyBrief.hash);

    // Recomputing should match
    const recomputed = computeIntegrityHash(weeklyBrief);
    expect(recomputed).toBe(weeklyBrief.hash);

    // Tampering should invalidate
    const tampered: AKFUnit = {
      ...weeklyBrief,
      claims: [{ c: "tampered!", t: 0.01 }],
    };
    const tamperedHash = computeIntegrityHash(tampered);
    expect(tamperedHash).not.toBe(weeklyBrief.hash);

    // ============================================================
    // STEP 9: Round-trip JSON serialization
    // ============================================================
    const json = toJSON(weeklyBrief);
    const reloaded = fromJSON(json);

    expect(reloaded.id).toBe(weeklyBrief.id);
    expect(reloaded.label).toBe(weeklyBrief.label);
    expect(reloaded.claims).toHaveLength(weeklyBrief.claims.length);
    expect(reloaded.prov!).toHaveLength(weeklyBrief.prov!.length);

    for (let i = 0; i < weeklyBrief.claims.length; i++) {
      expect(reloaded.claims[i].c).toBe(weeklyBrief.claims[i].c);
      expect(reloaded.claims[i].t).toBe(weeklyBrief.claims[i].t);
    }

    // Verify no null fields in serialized JSON
    const parsed = JSON.parse(json);
    const assertNoNulls = (obj: unknown, path: string = ""): void => {
      if (typeof obj === "object" && obj !== null) {
        if (Array.isArray(obj)) {
          for (let i = 0; i < obj.length; i++) {
            assertNoNulls(obj[i], `${path}[${i}]`);
          }
        } else {
          for (const [k, v] of Object.entries(obj)) {
            expect(v).not.toBeNull();
            expect(v).not.toBeUndefined();
            assertNoNulls(v, `${path}.${k}`);
          }
        }
      }
    };
    assertNoNulls(parsed);
  });
});
