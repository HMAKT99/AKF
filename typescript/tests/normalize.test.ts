import { describe, it, expect } from "vitest";
import {
  normalizeClaim,
  normalizeUnit,
  toDescriptive,
  toDescriptiveClaim,
  fromJSON,
  toJSON,
  create,
} from "../src/index.js";

describe("normalizeClaim", () => {
  it("should pass through compact names", () => {
    const claim = normalizeClaim({ c: "test", t: 0.5, src: "SEC" });
    expect(claim.c).toBe("test");
    expect(claim.t).toBe(0.5);
    expect(claim.src).toBe("SEC");
  });

  it("should convert descriptive names to compact", () => {
    const claim = normalizeClaim({
      content: "Revenue $4.2B",
      confidence: 0.98,
      source: "SEC",
      authority_tier: 1,
      verified: true,
      ai_generated: false,
      decay_half_life: 30,
    });
    expect(claim.c).toBe("Revenue $4.2B");
    expect(claim.t).toBe(0.98);
    expect(claim.src).toBe("SEC");
    expect(claim.tier).toBe(1);
    expect(claim.ver).toBe(true);
    expect(claim.ai).toBe(false);
    expect(claim.decay).toBe(30);
  });

  it("should preserve unknown fields", () => {
    const claim = normalizeClaim({ c: "test", t: 0.5, custom: "value" });
    expect((claim as Record<string, unknown>).custom).toBe("value");
  });
});

describe("normalizeUnit", () => {
  it("should normalize descriptive unit fields", () => {
    const unit = normalizeUnit({
      version: "1.0",
      author: "user@test.com",
      classification: "confidential",
      inherit_classification: true,
      allow_external: false,
      claims: [{ content: "test", confidence: 0.5, source: "SEC" }],
    });
    expect(unit.v).toBe("1.0");
    expect(unit.by).toBe("user@test.com");
    expect(unit.label).toBe("confidential");
    expect(unit.inherit).toBe(true);
    expect(unit.ext).toBe(false);
    expect(unit.claims[0].c).toBe("test");
    expect(unit.claims[0].t).toBe(0.5);
    expect(unit.claims[0].src).toBe("SEC");
  });

  it("should normalize provenance hops", () => {
    const unit = normalizeUnit({
      v: "1.0",
      claims: [{ c: "test", t: 0.5 }],
      provenance: [
        { hop: 0, actor: "user@test.com", action: "created", timestamp: "2025-01-01T00:00:00Z" },
      ],
    });
    expect(unit.prov).toBeDefined();
    expect(unit.prov![0].by).toBe("user@test.com");
    expect(unit.prov![0].do).toBe("created");
    expect(unit.prov![0].at).toBe("2025-01-01T00:00:00Z");
  });
});

describe("toDescriptive", () => {
  it("should convert compact to descriptive", () => {
    const unit = create("Revenue $4.2B", 0.98, { src: "SEC", tier: 1 });
    const desc = toDescriptive(unit);
    expect(desc.version).toBe("1.0");
    expect(desc.author).toBeUndefined(); // Not set
    const claims = desc.claims as Record<string, unknown>[];
    expect(claims[0].content).toBe("Revenue $4.2B");
    expect(claims[0].confidence).toBe(0.98);
    expect(claims[0].source).toBe("SEC");
    expect(claims[0].authority_tier).toBe(1);
  });
});

describe("toDescriptiveClaim", () => {
  it("should convert compact claim to descriptive", () => {
    const desc = toDescriptiveClaim({ c: "test", t: 0.5, src: "SEC", ai: true });
    expect(desc.content).toBe("test");
    expect(desc.confidence).toBe(0.5);
    expect(desc.source).toBe("SEC");
    expect(desc.ai_generated).toBe(true);
  });
});

describe("fromJSON with descriptive names", () => {
  it("should parse descriptive JSON and normalize to compact", () => {
    const json = JSON.stringify({
      version: "1.0",
      classification: "internal",
      claims: [
        { content: "Test claim", confidence: 0.8, source: "test" },
      ],
    });
    const unit = fromJSON(json);
    expect(unit.v).toBe("1.0");
    expect(unit.label).toBe("internal");
    expect(unit.claims[0].c).toBe("Test claim");
    expect(unit.claims[0].t).toBe(0.8);
    expect(unit.claims[0].src).toBe("test");
  });

  it("should still parse compact JSON", () => {
    const json = JSON.stringify({
      v: "1.0",
      label: "internal",
      claims: [{ c: "test", t: 0.5, src: "SEC" }],
    });
    const unit = fromJSON(json);
    expect(unit.v).toBe("1.0");
    expect(unit.claims[0].c).toBe("test");
  });

  it("should round-trip descriptive -> compact -> descriptive", () => {
    const descriptiveJson = JSON.stringify({
      version: "1.0",
      classification: "confidential",
      claims: [
        { content: "Revenue $4.2B", confidence: 0.98, source: "SEC", authority_tier: 1 },
      ],
    });
    const unit = fromJSON(descriptiveJson);
    const compactJson = toJSON(unit);
    const reloaded = fromJSON(compactJson);
    const desc = toDescriptive(reloaded);
    expect(desc.version).toBe("1.0");
    expect(desc.classification).toBe("confidential");
    expect((desc.claims as Record<string, unknown>[])[0].content).toBe("Revenue $4.2B");
  });
});
