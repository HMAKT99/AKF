import { describe, it, expect } from "vitest";
import {
  effectiveTrust,
  AUTHORITY_WEIGHTS,
} from "../src/index.js";
import type { Claim } from "../src/index.js";

function makeClaim(overrides: Partial<Claim>): Claim {
  return { c: "test", t: 0.5, ...overrides };
}

describe("effectiveTrust", () => {
  it("should compute tier 1 high trust", () => {
    const claim = makeClaim({ c: "Revenue $4.2B", t: 0.98, tier: 1 });
    const result = effectiveTrust(claim);
    expect(result.score).toBeCloseTo(0.98, 1);
    expect(result.decision).toBe("ACCEPT");
  });

  it("should compute tier 2", () => {
    const claim = makeClaim({ c: "Growth 15%", t: 0.85, tier: 2 });
    const result = effectiveTrust(claim);
    const expected = 0.85 * 0.85; // 0.7225
    expect(result.score).toBeCloseTo(expected, 1);
    expect(result.decision).toBe("ACCEPT");
  });

  it("should default to tier 3", () => {
    const claim = makeClaim({ c: "test", t: 0.7 });
    const result = effectiveTrust(claim);
    const expected = 0.7 * 0.7; // 0.49
    expect(result.score).toBeCloseTo(expected, 1);
    expect(result.decision).toBe("LOW");
  });

  it("should compute tier 4", () => {
    const claim = makeClaim({
      c: "Pipeline strong",
      t: 0.72,
      tier: 4,
    });
    const result = effectiveTrust(claim);
    const expected = 0.72 * 0.5; // 0.36
    expect(result.score).toBeCloseTo(expected, 1);
    expect(result.decision).toBe("REJECT");
  });

  it("should compute tier 5 low trust", () => {
    const claim = makeClaim({
      c: "AI inference",
      t: 0.63,
      tier: 5,
    });
    const result = effectiveTrust(claim);
    const expected = 0.63 * 0.3; // 0.189
    expect(result.score).toBeCloseTo(expected, 1);
    expect(result.decision).toBe("REJECT");
  });

  it("should apply temporal decay at half-life", () => {
    const claim = makeClaim({ t: 1.0, tier: 1, decay: 30 });
    const result = effectiveTrust(claim, 30);
    expect(result.score).toBeCloseTo(0.5, 1);
  });

  it("should apply temporal decay at double half-life", () => {
    const claim = makeClaim({ t: 1.0, tier: 1, decay: 30 });
    const result = effectiveTrust(claim, 60);
    expect(result.score).toBeCloseTo(0.25, 1);
  });

  it("should not decay without decay field", () => {
    const claim = makeClaim({ t: 0.9, tier: 1 });
    const result = effectiveTrust(claim, 365);
    expect(result.score).toBeCloseTo(0.9, 1);
  });

  it("should apply penalty", () => {
    const claim = makeClaim({ t: 0.98, tier: 1 });
    const result = effectiveTrust(claim, 0, -0.1);
    const expected = 0.98 * 1.0 * 1.0 * 0.9; // 0.882
    expect(result.score).toBeCloseTo(expected, 1);
  });

  it("should handle trust = 0", () => {
    const claim = makeClaim({ t: 0.0, tier: 1 });
    const result = effectiveTrust(claim);
    expect(result.score).toBe(0.0);
    expect(result.decision).toBe("REJECT");
  });

  it("should handle trust = 1", () => {
    const claim = makeClaim({ c: "certain", t: 1.0, tier: 1 });
    const result = effectiveTrust(claim);
    expect(result.score).toBe(1.0);
    expect(result.decision).toBe("ACCEPT");
  });

  it("should have correct decision thresholds", () => {
    // >= 0.7 -> ACCEPT
    expect(effectiveTrust(makeClaim({ t: 0.7, tier: 1 })).decision).toBe(
      "ACCEPT"
    );

    // >= 0.4 -> LOW
    // 0.6 * 0.7 = 0.42
    expect(
      effectiveTrust(makeClaim({ t: 0.6, tier: 3 })).decision
    ).toBe("LOW");

    // < 0.4 -> REJECT
    // 0.5 * 0.3 = 0.15
    expect(
      effectiveTrust(makeClaim({ t: 0.5, tier: 5 })).decision
    ).toBe("REJECT");
  });

  it("should return correct breakdown", () => {
    const claim = makeClaim({ t: 0.85, tier: 2 });
    const result = effectiveTrust(claim);
    expect(result.breakdown.confidence).toBe(0.85);
    expect(result.breakdown.authority).toBe(0.85);
    expect(result.breakdown.tier).toBe(2);
  });

  it("should work for all authority weight tiers", () => {
    for (const [tier, weight] of Object.entries(AUTHORITY_WEIGHTS)) {
      const claim = makeClaim({ t: 1.0, tier: Number(tier) });
      const result = effectiveTrust(claim);
      expect(result.score).toBeCloseTo(weight, 1);
    }
  });
});
