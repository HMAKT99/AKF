import { describe, it, expect } from "vitest";
import { AKFBuilder, validate, toJSON } from "../src/index.js";

describe("AKFBuilder", () => {
  it("should build a basic unit", () => {
    const unit = new AKFBuilder()
      .by("sarah@woodgrove.com")
      .claim("Revenue $4.2B", 0.98, { src: "SEC 10-Q", tier: 1 })
      .build();

    expect(unit.v).toBe("1.0");
    expect(unit.claims).toHaveLength(1);
    expect(unit.by).toBe("sarah@woodgrove.com");
    expect(unit.id!.startsWith("akf-")).toBe(true);
  });

  it("should build a multi-claim unit", () => {
    const unit = new AKFBuilder()
      .by("sarah@woodgrove.com")
      .label("confidential")
      .claim("Revenue $4.2B", 0.98, { src: "SEC 10-Q", tier: 1, ver: true })
      .claim("Cloud growth 15-18%", 0.85, { src: "Gartner", tier: 2 })
      .claim("Pipeline strong", 0.72, { src: "my estimate", tier: 4 })
      .build();

    expect(unit.claims).toHaveLength(3);
    expect(unit.label).toBe("confidential");
  });

  it("should auto-create provenance hop 0", () => {
    const unit = new AKFBuilder()
      .by("sarah@woodgrove.com")
      .claim("test", 0.5)
      .build();

    expect(unit.prov).toBeDefined();
    expect(unit.prov!).toHaveLength(1);
    expect(unit.prov![0].hop).toBe(0);
    expect(unit.prov![0].by).toBe("sarah@woodgrove.com");
    expect(unit.prov![0].do).toBe("created");
  });

  it("should auto-compute integrity hash", () => {
    const unit = new AKFBuilder()
      .by("user@test.com")
      .claim("test", 0.5)
      .build();

    expect(unit.hash).toBeDefined();
    expect(unit.hash!.startsWith("sha256:")).toBe(true);
  });

  it("should add tags to the last claim", () => {
    const unit = new AKFBuilder()
      .claim("test", 0.5)
      .tag("revenue", "Q3")
      .build();

    expect(unit.claims[0].tags).toEqual(["revenue", "Q3"]);
  });

  it("should throw when tagging without a claim", () => {
    expect(() => {
      new AKFBuilder().tag("test");
    }).toThrow("No claims to tag");
  });

  it("should throw when building without claims", () => {
    expect(() => {
      new AKFBuilder().build();
    }).toThrow("At least one claim is required");
  });

  it("should produce a unit that validates", () => {
    const unit = new AKFBuilder()
      .by("user@test.com")
      .label("internal")
      .claim("test claim", 0.8, { src: "source" })
      .build();

    const result = validate(unit);
    expect(result.valid).toBe(true);
  });

  it("should set agent", () => {
    const unit = new AKFBuilder()
      .agent("copilot-m365")
      .claim("AI insight", 0.7, { ai: true })
      .build();

    expect(unit.agent).toBe("copilot-m365");
  });

  it("should serialize without nulls", () => {
    const unit = new AKFBuilder()
      .by("user@test.com")
      .claim("test", 0.5)
      .build();

    const cleanJson = toJSON(unit);
    const cleanParsed = JSON.parse(cleanJson);

    const checkNoNulls = (obj: unknown): void => {
      if (typeof obj === "object" && obj !== null) {
        if (Array.isArray(obj)) {
          for (const item of obj) checkNoNulls(item);
        } else {
          for (const [key, value] of Object.entries(obj)) {
            expect(value).not.toBeNull();
            expect(value).not.toBeUndefined();
            checkNoNulls(value);
          }
        }
      }
    };
    checkNoNulls(cleanParsed);
  });
});
