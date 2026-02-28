import { describe, it, expect } from "vitest";
import {
  create,
  createMulti,
  validate,
  toJSON,
  fromJSON,
  stripNulls,
} from "../src/index.js";

describe("create", () => {
  it("should create a single-claim unit", () => {
    const unit = create("Revenue $4.2B", 0.98);
    expect(unit.v).toBe("1.0");
    expect(unit.claims).toHaveLength(1);
    expect(unit.claims[0].c).toBe("Revenue $4.2B");
    expect(unit.claims[0].t).toBe(0.98);
    expect(unit.id).toBeDefined();
    expect(unit.id!.startsWith("akf-")).toBe(true);
    expect(unit.at).toBeDefined();
  });

  it("should create a single-claim unit with opts", () => {
    const unit = create("Revenue $4.2B", 0.98, {
      src: "SEC 10-Q",
      tier: 1,
      ver: true,
    });
    expect(unit.claims[0].src).toBe("SEC 10-Q");
    expect(unit.claims[0].tier).toBe(1);
    expect(unit.claims[0].ver).toBe(true);
  });

  it("should auto-generate claim ID", () => {
    const unit = create("test", 0.5);
    expect(unit.claims[0].id).toBeDefined();
    expect(typeof unit.claims[0].id).toBe("string");
  });
});

describe("createMulti", () => {
  it("should create a multi-claim unit", () => {
    const unit = createMulti(
      [
        { c: "Claim 1", t: 0.9 },
        { c: "Claim 2", t: 0.8, src: "source" },
      ],
      { by: "user@test.com", label: "internal" }
    );
    expect(unit.claims).toHaveLength(2);
    expect(unit.by).toBe("user@test.com");
    expect(unit.label).toBe("internal");
  });
});

describe("validate", () => {
  it("should validate a minimal unit", () => {
    const unit = create("test", 0.5);
    const result = validate(unit);
    expect(result.valid).toBe(true);
    expect(result.level).toBe(1);
  });

  it("should validate a practical unit (with source)", () => {
    const unit = create("test", 0.5, { src: "source" });
    const result = validate(unit);
    expect(result.valid).toBe(true);
    expect(result.level).toBe(2);
  });

  it("should reject invalid label", () => {
    const unit = create("test", 0.5);
    unit.label = "top-secret";
    const result = validate(unit);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("RULE 5"))).toBe(true);
  });

  it("should reject invalid hash prefix", () => {
    const unit = create("test", 0.5);
    unit.hash = "md5:abc123";
    const result = validate(unit);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("RULE 10"))).toBe(true);
  });

  it("should reject non-sequential provenance hops", () => {
    const unit = create("test", 0.5);
    unit.prov = [
      { hop: 0, by: "a", do: "created", at: "2025-01-01T00:00:00Z" },
      { hop: 5, by: "b", do: "enriched", at: "2025-01-01T00:00:00Z" },
    ];
    const result = validate(unit);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("RULE 7"))).toBe(true);
  });

  it("should warn on AI tier 5 without risk", () => {
    const unit = create("AI claim", 0.6, { ai: true, tier: 5 });
    const result = validate(unit);
    expect(result.valid).toBe(true);
    expect(result.warnings.length).toBeGreaterThan(0);
    expect(result.warnings.some((w) => w.includes("RULE 9"))).toBe(true);
  });

  it("should reject positive penalty", () => {
    const unit = create("test", 0.5);
    unit.prov = [
      {
        hop: 0,
        by: "a",
        do: "created",
        at: "2025-01-01T00:00:00Z",
        pen: 0.5,
      },
    ];
    const result = validate(unit);
    expect(result.valid).toBe(false);
    expect(result.errors.some((e) => e.includes("RULE 8"))).toBe(true);
  });
});

describe("round-trip serialization", () => {
  it("should round-trip via JSON", () => {
    const unit = create("Test claim", 0.85, { src: "test" });
    const json = toJSON(unit);
    const loaded = fromJSON(json);
    expect(loaded.claims[0].c).toBe(unit.claims[0].c);
    expect(loaded.claims[0].t).toBe(unit.claims[0].t);
    expect(loaded.claims[0].src).toBe(unit.claims[0].src);
    expect(loaded.id).toBe(unit.id);
  });

  it("should exclude null/undefined from JSON", () => {
    const unit = create("test", 0.5);
    const json = toJSON(unit);
    const parsed = JSON.parse(json);

    const checkNoNulls = (obj: unknown): void => {
      if (typeof obj === "object" && obj !== null) {
        if (Array.isArray(obj)) {
          for (const item of obj) {
            checkNoNulls(item);
          }
        } else {
          for (const [key, value] of Object.entries(obj)) {
            expect(value).not.toBeNull();
            expect(value).not.toBeUndefined();
            checkNoNulls(value);
          }
        }
      }
    };
    checkNoNulls(parsed);
  });

  it("should preserve unknown fields in round-trip", () => {
    const json =
      '{"v":"1.0","claims":[{"c":"test","t":0.5,"future":"2050"}],"new_field":"value"}';
    const unit = fromJSON(json);
    const output = toJSON(unit);
    const parsed = JSON.parse(output);
    expect(parsed.new_field).toBe("value");
    expect(parsed.claims[0].future).toBe("2050");
  });
});

describe("stripNulls", () => {
  it("should remove null values from objects", () => {
    const result = stripNulls({ a: 1, b: null, c: "test" });
    expect(result).toEqual({ a: 1, c: "test" });
  });

  it("should remove undefined values from objects", () => {
    const result = stripNulls({ a: 1, b: undefined, c: "test" });
    expect(result).toEqual({ a: 1, c: "test" });
  });

  it("should handle nested objects", () => {
    const result = stripNulls({
      a: { b: null, c: 1 },
      d: [{ e: null, f: 2 }],
    });
    expect(result).toEqual({ a: { c: 1 }, d: [{ f: 2 }] });
  });
});
