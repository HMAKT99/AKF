import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdtempSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  stampFile,
  read,
  extract,
  embed,
  scan,
  create,
  createMulti,
  toJSON,
} from "../src/index.js";

let tmpDir: string;

beforeEach(() => {
  tmpDir = mkdtempSync(join(tmpdir(), "akf-test-"));
});

afterEach(() => {
  rmSync(tmpDir, { recursive: true, force: true });
});

// ---------------------------------------------------------------------------
// stampFile
// ---------------------------------------------------------------------------

describe("stampFile", () => {
  it("should stamp a .akf file and read it back", () => {
    const filepath = join(tmpDir, "test.akf");
    const unit = stampFile(filepath, { claims: ["AI generated content"], trustScore: 0.85 });
    expect(unit.v).toBe("1.0");
    expect(unit.claims.length).toBeGreaterThanOrEqual(1);
    expect(unit.claims[0].t).toBe(0.85);

    // Read it back
    const loaded = read(filepath);
    expect(loaded.v).toBe("1.0");
    expect(loaded.claims.length).toBe(unit.claims.length);
  });

  it("should set origin when model is provided", () => {
    const filepath = join(tmpDir, "test.akf");
    const unit = stampFile(filepath, {
      model: "gpt-4o",
      claims: ["Model output"],
    });
    // Claims should have origin set
    expect((unit.claims[0] as Record<string, unknown>).origin).toBeDefined();
    const origin = (unit.claims[0] as Record<string, unknown>).origin as Record<string, unknown>;
    expect(origin.model).toBe("gpt-4o");
  });

  it("should create default claim with origin when model is provided", () => {
    const filepath = join(tmpDir, "test.akf");
    const unit = stampFile(filepath, { model: "claude-3" });
    expect(unit.claims.length).toBe(1);
    expect(unit.claims[0].c).toContain("claude-3");
    const origin = (unit.claims[0] as Record<string, unknown>).origin as Record<string, unknown>;
    expect(origin.model).toBe("claude-3");
  });

  it("should add evidence to claims", () => {
    const filepath = join(tmpDir, "test.akf");
    const unit = stampFile(filepath, {
      claims: ["Tested claim"],
      evidence: ["10/10 tests pass", "mypy clean"],
    });
    expect(unit.claims[0].evidence).toBeDefined();
    expect(unit.claims[0].evidence!.length).toBe(2);
    expect(unit.claims[0].evidence![0].type).toBe("test_pass");
    expect(unit.claims[0].evidence![1].type).toBe("type_check");
  });

  it("should stamp a .json file with _akf key", () => {
    const filepath = join(tmpDir, "data.json");
    writeFileSync(filepath, JSON.stringify({ data: "hello" }), "utf-8");
    stampFile(filepath, { claims: ["Processed data"], trustScore: 0.8 });

    const content = JSON.parse(readFileSync(filepath, "utf-8"));
    expect(content.data).toBe("hello");
    expect(content._akf).toBeDefined();
    expect(content._akf.claims.length).toBe(1);
  });

  it("should stamp a .md file with frontmatter", () => {
    const filepath = join(tmpDir, "doc.md");
    writeFileSync(filepath, "# Hello\n\nWorld\n", "utf-8");
    stampFile(filepath, { claims: ["Summary accurate"], trustScore: 0.9 });

    const content = readFileSync(filepath, "utf-8");
    expect(content).toMatch(/^---\n/);
    expect(content).toContain("akf:");
    expect(content).toContain("# Hello");
  });

  it("should stamp a .txt file with sidecar", () => {
    const filepath = join(tmpDir, "plain.txt");
    writeFileSync(filepath, "plain text content", "utf-8");
    stampFile(filepath, { claims: ["Content reviewed"], trustScore: 0.85 });

    const sidecar = join(tmpDir, "plain.txt.akf.json");
    const sidecarContent = JSON.parse(readFileSync(sidecar, "utf-8"));
    expect(sidecarContent.claims.length).toBe(1);
  });

  it("should accept a single evidence string (issue #101)", () => {
    const filepath = join(tmpDir, "ev.md");
    writeFileSync(filepath, "# Hello\n", "utf-8");
    const unit = stampFile(filepath, { agent: "test", evidence: "tests pass" });
    const ev = unit.claims[0].evidence;
    expect(Array.isArray(ev)).toBe(true);
    expect(ev!.length).toBe(1);
    expect(ev![0].detail).toBe("tests pass");
  });

  it("should reject non-string non-array evidence with a clear error", () => {
    const filepath = join(tmpDir, "ev.md");
    writeFileSync(filepath, "# Hello\n", "utf-8");
    expect(() =>
      // @ts-expect-error — runtime check for JS callers
      stampFile(filepath, { evidence: 42 })
    ).toThrowError(/'evidence' must be a string or string\[\]/);
  });
});

// ---------------------------------------------------------------------------
// read / extract
// ---------------------------------------------------------------------------

describe("read / extract", () => {
  it("should read a .akf file", () => {
    const filepath = join(tmpDir, "test.akf");
    const unit = create("Test claim", 0.9, { src: "test" });
    writeFileSync(filepath, toJSON(unit), "utf-8");

    const loaded = read(filepath);
    expect(loaded.claims[0].c).toBe("Test claim");
    expect(loaded.claims[0].t).toBe(0.9);
  });

  it("should read a .json file with _akf key", () => {
    const filepath = join(tmpDir, "data.json");
    const unit = create("JSON claim", 0.8);
    const data = { name: "test", _akf: JSON.parse(toJSON(unit)) };
    writeFileSync(filepath, JSON.stringify(data), "utf-8");

    const loaded = read(filepath);
    expect(loaded.claims[0].c).toBe("JSON claim");
  });

  it("should read a .json file that is a full AKF unit", () => {
    const filepath = join(tmpDir, "unit.json");
    const unit = create("Full unit", 0.75);
    writeFileSync(filepath, toJSON(unit), "utf-8");

    const loaded = read(filepath);
    expect(loaded.claims[0].c).toBe("Full unit");
  });

  it("should read a .md file with YAML frontmatter", () => {
    const filepath = join(tmpDir, "doc.md");
    const unit = create("MD claim", 0.85);
    const compactJson = toJSON(unit);
    const content = `---\ntitle: Test\nakf: ${compactJson}\n---\n# Hello\n`;
    writeFileSync(filepath, content, "utf-8");

    const loaded = read(filepath);
    expect(loaded.claims[0].c).toBe("MD claim");
  });

  it("extract should be an alias for read", () => {
    expect(extract).toBe(read);
  });

  it("should throw for file without AKF metadata", () => {
    const filepath = join(tmpDir, "plain.json");
    writeFileSync(filepath, JSON.stringify({ name: "no akf" }), "utf-8");
    expect(() => read(filepath)).toThrow("No AKF metadata found");
  });

  it("should read from sidecar file", () => {
    const filepath = join(tmpDir, "image.png");
    const sidecar = join(tmpDir, "image.png.akf.json");
    writeFileSync(filepath, "fake-image", "utf-8");
    const unit = create("Sidecar claim", 0.7);
    writeFileSync(sidecar, toJSON(unit), "utf-8");

    const loaded = read(filepath);
    expect(loaded.claims[0].c).toBe("Sidecar claim");
  });

  it("should read HTML with AKF script tag", () => {
    const filepath = join(tmpDir, "page.html");
    const unit = create("HTML claim", 0.85);
    const jsonStr = toJSON(unit, 2);
    writeFileSync(
      filepath,
      `<html><head><script type="application/akf+json">\n${jsonStr}\n</script></head><body></body></html>`,
      "utf-8"
    );
    const loaded = read(filepath);
    expect(loaded.claims[0].c).toBe("HTML claim");
  });
});

// ---------------------------------------------------------------------------
// embed
// ---------------------------------------------------------------------------

describe("embed", () => {
  it("should embed into .json file", () => {
    const filepath = join(tmpDir, "data.json");
    writeFileSync(filepath, JSON.stringify({ name: "test" }), "utf-8");

    const unit = create("Embedded claim", 0.8);
    embed(filepath, unit);

    const raw = JSON.parse(readFileSync(filepath, "utf-8"));
    expect(raw._akf).toBeDefined();
    expect(raw._akf.claims[0].c).toBe("Embedded claim");
    expect(raw.name).toBe("test");
  });

  it("should embed into .md file", () => {
    const filepath = join(tmpDir, "doc.md");
    writeFileSync(filepath, "# Hello\nWorld\n", "utf-8");

    const unit = create("MD embed", 0.9);
    embed(filepath, unit);

    const content = readFileSync(filepath, "utf-8");
    expect(content).toContain("---");
    expect(content).toContain("akf:");
    expect(content).toContain("# Hello");
  });

  it("should embed into .html file", () => {
    const filepath = join(tmpDir, "page.html");
    writeFileSync(filepath, "<html><head></head><body>Hi</body></html>", "utf-8");

    const unit = create("HTML embed", 0.85);
    embed(filepath, unit);

    const content = readFileSync(filepath, "utf-8");
    expect(content).toContain("application/akf+json");
    expect(content).toContain("HTML embed");

    // Should be readable back
    const loaded = read(filepath);
    expect(loaded.claims[0].c).toBe("HTML embed");
  });

  it("should use sidecar for unsupported formats", () => {
    const filepath = join(tmpDir, "data.csv");
    writeFileSync(filepath, "a,b,c\n1,2,3", "utf-8");

    const unit = create("Sidecar embed", 0.7);
    embed(filepath, unit);

    const sidecar = join(tmpDir, "data.csv.akf.json");
    const loaded = JSON.parse(readFileSync(sidecar, "utf-8"));
    expect(loaded.claims[0].c).toBe("Sidecar embed");
  });

  it("should accept EmbedOptions instead of unit", () => {
    const filepath = join(tmpDir, "opts.akf");
    embed(filepath, {
      claims: [{ c: "Option claim", t: 0.9 }],
      classification: "internal",
    });
    const loaded = read(filepath);
    expect(loaded.claims[0].c).toBe("Option claim");
    expect(loaded.label).toBe("internal");
  });

  it("should embed into new .akf file", () => {
    const filepath = join(tmpDir, "new.akf");
    const unit = create("New file", 0.8);
    embed(filepath, unit);
    const loaded = read(filepath);
    expect(loaded.claims[0].c).toBe("New file");
  });
});

// ---------------------------------------------------------------------------
// scan
// ---------------------------------------------------------------------------

describe("scan", () => {
  it("should scan an enriched file", () => {
    const filepath = join(tmpDir, "test.akf");
    stampFile(filepath, { claims: ["Scan claim"], classification: "internal" });

    const result = scan(filepath);
    expect(result.enriched).toBe(true);
    expect(result.format).toBe("akf");
    expect(result.claimCount).toBeGreaterThanOrEqual(1);
    expect(result.classification).toBe("internal");
    expect(result.overallTrust).toBeGreaterThan(0);
    expect(result.validation).toBeDefined();
    expect(result.validation!.valid).toBe(true);
  });

  it("should scan a non-enriched file", () => {
    const filepath = join(tmpDir, "plain.txt");
    writeFileSync(filepath, "Just a plain file", "utf-8");

    const result = scan(filepath);
    expect(result.enriched).toBe(false);
    expect(result.claimCount).toBe(0);
    expect(result.overallTrust).toBe(0);
    expect(result.validation).toBeNull();
  });

  it("should count AI claims", () => {
    const filepath = join(tmpDir, "ai.akf");
    const unit = createMulti([
      { c: "AI claim", t: 0.8, ai: true },
      { c: "Human claim", t: 0.9 },
    ]);
    writeFileSync(filepath, toJSON(unit), "utf-8");

    const result = scan(filepath);
    expect(result.aiClaimCount).toBe(1);
    expect(result.claimCount).toBe(2);
  });

  it("should scan multiple claims and average trust", () => {
    const filepath = join(tmpDir, "multi.akf");
    stampFile(filepath, { claims: ["Claim A", "Claim B"], trustScore: 0.8 });
    const result = scan(filepath);
    expect(result.claimCount).toBe(2);
    expect(result.overallTrust).toBe(0.8);
  });
});
