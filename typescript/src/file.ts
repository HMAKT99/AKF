/**
 * AKF v1.1 — File I/O: read, write, stamp, embed, extract AKF metadata.
 *
 * Supports:
 * - .akf (native JSON)
 * - .json (_akf key)
 * - .md (YAML frontmatter)
 * - .html (JSON-LD script tag)
 * - Everything else via sidecar .akf.json
 */

import { readFileSync, writeFileSync, existsSync } from "node:fs";
import { extname, basename, dirname, join } from "node:path";
import type { AKFUnit, Claim } from "./models.js";
import { normalizeUnit } from "./models.js";
import { create, createMulti, toJSON, fromJSON, stripNulls, validate } from "./core.js";
import type { ValidationResult } from "./core.js";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function sidecarPath(filepath: string): string {
  const dir = dirname(filepath);
  const base = basename(filepath);
  return join(dir, `${base}.akf.json`);
}

function nowISO(): string {
  return new Date().toISOString();
}

// ---------------------------------------------------------------------------
// YAML frontmatter parser (reads native YAML and legacy JSON-string)
// ---------------------------------------------------------------------------

/**
 * Parse AKF metadata from a frontmatter block.
 * Supports native YAML (`akf:` with indented children) and legacy `_akf: '{...}'`.
 */
function parseAKFFromFrontmatter(block: string): Record<string, unknown> | null {
  const lines = block.split("\n");

  // Try native YAML: "akf:" line with indented children
  for (let i = 0; i < lines.length; i++) {
    const stripped = lines[i].trim();
    if (stripped === "akf:" || stripped.startsWith("akf: ")) {
      const inline = stripped.slice(4).trim();
      if (inline && inline.startsWith("{")) {
        // Inline JSON: akf: {"v":"1.0",...}
        try { return JSON.parse(inline); } catch { /* continue */ }
      }
      if (stripped === "akf:") {
        // Collect indented block
        const childLines: string[] = [];
        for (let j = i + 1; j < lines.length; j++) {
          if (lines[j].length > 0 && (lines[j][0] === " " || lines[j][0] === "\t")) {
            childLines.push(lines[j]);
          } else if (lines[j].trim() === "") {
            childLines.push(lines[j]);
          } else {
            break;
          }
        }
        if (childLines.length > 0) {
          return parseYamlBlock(childLines);
        }
      }
    }
  }

  // Try legacy: _akf: '{...}' or _akf: "{...}"
  for (const line of lines) {
    const stripped = line.trim();
    if (stripped.startsWith("_akf:")) {
      let val = stripped.slice(5).trim();
      if (val.length >= 2 && val[0] === val[val.length - 1] && (val[0] === "'" || val[0] === '"')) {
        val = val.slice(1, -1);
      }
      try { return JSON.parse(val); } catch { /* continue */ }
    }
  }

  return null;
}

function indentLevel(line: string): number {
  let count = 0;
  for (const ch of line) {
    if (ch === " ") count++;
    else if (ch === "\t") count += 2;
    else break;
  }
  return count;
}

function parseYamlValue(val: string): unknown {
  if (!val) return "";
  // Quoted string
  if (val.length >= 2 && val[0] === val[val.length - 1] && (val[0] === "'" || val[0] === '"')) {
    return val.slice(1, -1);
  }
  // Boolean
  if (val.toLowerCase() === "true") return true;
  if (val.toLowerCase() === "false") return false;
  // Null
  if (val.toLowerCase() === "null" || val === "~") return null;
  // Number
  if (/^-?\d+\.\d+$/.test(val)) return parseFloat(val);
  if (/^-?\d+$/.test(val)) return parseInt(val, 10);
  // Inline array
  if (val.startsWith("[") && val.endsWith("]")) {
    const inner = val.slice(1, -1).trim();
    if (!inner) return [];
    return inner.split(",").map((s) => parseYamlValue(s.trim()));
  }
  return val;
}

function parseYamlBlock(lines: string[]): Record<string, unknown> {
  const result: Record<string, unknown> = {};
  const baseIndent = lines.length > 0 ? indentLevel(lines[0]) : 0;
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    const stripped = line.trim();
    const indent = indentLevel(line);

    if (!stripped || stripped.startsWith("#") || indent < baseIndent) {
      i++;
      continue;
    }

    const colonIdx = stripped.indexOf(":");
    if (colonIdx < 0) { i++; continue; }

    const key = stripped.slice(0, colonIdx).trim();
    const valStr = stripped.slice(colonIdx + 1).trim();

    if (valStr === "" || valStr === null) {
      // Nested object or list
      const childLines: string[] = [];
      for (let j = i + 1; j < lines.length; j++) {
        const jStripped = lines[j].trim();
        if (indentLevel(lines[j]) > indent || !jStripped) {
          childLines.push(lines[j]);
        } else {
          break;
        }
      }
      if (childLines.length > 0 && childLines.find((l) => l.trim().startsWith("- "))) {
        result[key] = parseYamlList(childLines);
      } else if (childLines.length > 0) {
        result[key] = parseYamlBlock(childLines);
      }
      i += 1 + childLines.length;
    } else {
      result[key] = parseYamlValue(valStr);
      i++;
    }
  }
  return result;
}

function parseYamlList(lines: string[]): unknown[] {
  const items: unknown[] = [];
  let i = 0;

  while (i < lines.length) {
    const stripped = lines[i].trim();
    if (!stripped) { i++; continue; }
    if (!stripped.startsWith("- ")) { i++; continue; }

    const itemIndent = indentLevel(lines[i]);
    const first = stripped.slice(2).trim();

    if (first.includes(":")) {
      // Dict item
      const obj: Record<string, unknown> = {};
      const colonIdx = first.indexOf(":");
      obj[first.slice(0, colonIdx).trim()] = parseYamlValue(first.slice(colonIdx + 1).trim());
      let j = i + 1;
      while (j < lines.length) {
        const nextLine = lines[j];
        const ns = nextLine.trim();
        if (!ns) { j++; continue; }
        if (indentLevel(nextLine) > itemIndent && !ns.startsWith("- ")) {
          if (ns.includes(":")) {
            const ci = ns.indexOf(":");
            obj[ns.slice(0, ci).trim()] = parseYamlValue(ns.slice(ci + 1).trim());
          }
          j++;
        } else {
          break;
        }
      }
      items.push(obj);
      i = j;
    } else {
      items.push(parseYamlValue(first));
      i++;
    }
  }
  return items;
}

// ---------------------------------------------------------------------------
// YAML serializer (writes native YAML for markdown frontmatter)
// ---------------------------------------------------------------------------

/**
 * Serialize an AKFUnit as native YAML for markdown frontmatter.
 * Produces human-readable, Obsidian/Dataview-friendly output.
 */
function akfToYaml(unit: AKFUnit): string {
  const obj = JSON.parse(toJSON(unit));
  const lines = ["akf:"];
  dictToYaml(obj, lines, 2, 2);
  return lines.join("\n");
}

function dictToYaml(d: Record<string, unknown>, lines: string[], base: number, step: number): void {
  const prefix = " ".repeat(base);
  for (const [key, val] of Object.entries(d)) {
    if (val === undefined || val === null) continue;
    if (typeof val === "object" && !Array.isArray(val)) {
      lines.push(`${prefix}${key}:`);
      dictToYaml(val as Record<string, unknown>, lines, base + step, step);
    } else if (Array.isArray(val)) {
      if (val.length === 0) {
        lines.push(`${prefix}${key}: []`);
      } else if (typeof val[0] === "object" && val[0] !== null) {
        lines.push(`${prefix}${key}:`);
        listOfDictsToYaml(val as Record<string, unknown>[], lines, base + step, step);
      } else {
        const items = val.map((v) => yamlScalar(v)).join(", ");
        lines.push(`${prefix}${key}: [${items}]`);
      }
    } else {
      lines.push(`${prefix}${key}: ${yamlScalar(val)}`);
    }
  }
}

function listOfDictsToYaml(items: Record<string, unknown>[], lines: string[], base: number, step: number): void {
  const prefix = " ".repeat(base);
  for (const item of items) {
    let first = true;
    for (const [key, val] of Object.entries(item)) {
      if (val === undefined || val === null) continue;
      if (first) {
        if (typeof val === "object" && !Array.isArray(val)) {
          lines.push(`${prefix}- ${key}:`);
          dictToYaml(val as Record<string, unknown>, lines, base + step + 2, step);
        } else {
          lines.push(`${prefix}- ${key}: ${yamlScalar(val)}`);
        }
        first = false;
      } else {
        const innerPrefix = " ".repeat(base + 2);
        if (typeof val === "object" && !Array.isArray(val)) {
          lines.push(`${innerPrefix}${key}:`);
          dictToYaml(val as Record<string, unknown>, lines, base + step + 2, step);
        } else if (Array.isArray(val)) {
          if (val.length > 0 && typeof val[0] === "object") {
            lines.push(`${innerPrefix}${key}:`);
            listOfDictsToYaml(val as Record<string, unknown>[], lines, base + step + 2, step);
          } else {
            const s = val.map((v) => yamlScalar(v)).join(", ");
            lines.push(`${innerPrefix}${key}: [${s}]`);
          }
        } else {
          lines.push(`${innerPrefix}${key}: ${yamlScalar(val)}`);
        }
      }
    }
  }
}

function yamlScalar(val: unknown): string {
  if (typeof val === "boolean") return val ? "true" : "false";
  if (typeof val === "number") return String(val);
  if (val === null || val === undefined) return "null";
  const s = String(val);
  // Quote strings that look like numbers to prevent YAML type coercion
  if (/^-?\d+(\.\d+)?$/.test(s)) return `"${s}"`;
  if (/[:{}\[\],&*?|<>=!%@`#\-]/.test(s) || /^(true|false|null|~|yes|no|on|off)$/i.test(s)) {
    return `"${s.replace(/"/g, '\\"')}"`;
  }
  if (!s) return '""';
  return s;
}

/**
 * Strip akf: and _akf: lines (and their indented children) from frontmatter.
 */
function stripAKFLines(lines: string[]): string[] {
  const result: string[] = [];
  let skipping = false;
  let skipIndent = 0;

  for (const line of lines) {
    const stripped = line.trim();
    if (stripped.startsWith("akf:") || stripped.startsWith("_akf:")) {
      skipping = true;
      skipIndent = indentLevel(line);
      continue;
    }
    if (skipping) {
      if (stripped === "" || indentLevel(line) > skipIndent) {
        continue; // Skip indented children of akf block
      }
      skipping = false;
    }
    result.push(line);
  }
  return result;
}

// ---------------------------------------------------------------------------
// Read / Extract
// ---------------------------------------------------------------------------

/**
 * Read AKF metadata from any file.
 * Checks native format first, then sidecar.
 */
export function read(filepath: string): AKFUnit {
  const ext = extname(filepath).toLowerCase();

  if (ext === ".akf") {
    const content = readFileSync(filepath, "utf-8");
    return fromJSON(content);
  }

  if (ext === ".json") {
    const content = readFileSync(filepath, "utf-8");
    const data = JSON.parse(content);
    if (data._akf) {
      return normalizeUnit(data._akf);
    }
    // Maybe the whole file is an AKF unit
    if (data.v && data.claims) {
      return normalizeUnit(data);
    }
    throw new Error(`No AKF metadata found in ${filepath}`);
  }

  if (ext === ".md") {
    const content = readFileSync(filepath, "utf-8");
    const match = content.match(/^---\n([\s\S]*?)\n---/);
    if (match) {
      const fmBlock = match[1];
      const parsed = parseAKFFromFrontmatter(fmBlock);
      if (parsed) {
        return normalizeUnit(parsed);
      }
    }
    // Fall through to sidecar
  }

  if (ext === ".html" || ext === ".htm") {
    const content = readFileSync(filepath, "utf-8");
    const match = content.match(
      /<script\s+type=["']application\/akf\+json["'][^>]*>([\s\S]*?)<\/script>/i
    );
    if (match) {
      return fromJSON(match[1].trim());
    }
    // Fall through to sidecar
  }

  // Sidecar fallback
  const sidecar = sidecarPath(filepath);
  if (existsSync(sidecar)) {
    const content = readFileSync(sidecar, "utf-8");
    return fromJSON(content);
  }

  throw new Error(`No AKF metadata found for ${filepath}`);
}

/** Alias for read — extract AKF metadata from any file. */
export const extract = read;

// ---------------------------------------------------------------------------
// Write / Embed
// ---------------------------------------------------------------------------

export interface EmbedOptions {
  claims?: Array<Partial<Claim>>;
  classification?: string;
  author?: string;
  agent?: string;
  model?: string;
}

/**
 * Embed AKF metadata into a file.
 * Uses native embedding for supported formats, sidecar for others.
 */
export function embed(filepath: string, unit: AKFUnit): void;
export function embed(filepath: string, options: EmbedOptions): void;
export function embed(filepath: string, unitOrOpts: AKFUnit | EmbedOptions): void {
  let unit: AKFUnit;

  if ("v" in unitOrOpts && "claims" in unitOrOpts && Array.isArray(unitOrOpts.claims)) {
    unit = unitOrOpts as AKFUnit;
  } else {
    const opts = unitOrOpts as EmbedOptions;
    const claims = (opts.claims || []).map((c) => ({
      c: c.c || (c as Record<string, unknown>).content as string || "",
      t: c.t ?? (c as Record<string, unknown>).confidence as number ?? 0.7,
      ...c,
    })) as Claim[];

    unit = createMulti(claims, {
      by: opts.author,
      agent: opts.agent,
      model: opts.model,
      label: opts.classification,
    });
  }

  const ext = extname(filepath).toLowerCase();
  const jsonStr = toJSON(unit, 2);

  if (ext === ".akf") {
    writeFileSync(filepath, jsonStr, "utf-8");
    return;
  }

  if (ext === ".json") {
    let data: Record<string, unknown> = {};
    if (existsSync(filepath)) {
      data = JSON.parse(readFileSync(filepath, "utf-8"));
    }
    data._akf = JSON.parse(jsonStr);
    writeFileSync(filepath, JSON.stringify(data, null, 2), "utf-8");
    return;
  }

  if (ext === ".md") {
    let content = "";
    if (existsSync(filepath)) {
      content = readFileSync(filepath, "utf-8");
    }
    const akfYaml = akfToYaml(unit);
    // Check if frontmatter exists
    if (content.startsWith("---\n")) {
      const endIdx = content.indexOf("\n---", 4);
      if (endIdx > 0) {
        const frontmatter = content.slice(4, endIdx);
        const rest = content.slice(endIdx + 4);
        // Remove existing akf/_ akf lines and their indented children
        const lines = stripAKFLines(frontmatter.split("\n"));
        lines.push(akfYaml);
        content = `---\n${lines.join("\n")}\n---${rest}`;
      }
    } else {
      content = `---\n${akfYaml}\n---\n${content}`;
    }
    writeFileSync(filepath, content, "utf-8");
    return;
  }

  if (ext === ".html" || ext === ".htm") {
    let content = "";
    if (existsSync(filepath)) {
      content = readFileSync(filepath, "utf-8");
    }
    const scriptTag = `<script type="application/akf+json">\n${jsonStr}\n</script>`;
    // Remove existing AKF script if present
    content = content.replace(
      /<script\s+type=["']application\/akf\+json["'][^>]*>[\s\S]*?<\/script>/gi,
      ""
    );
    // Insert before </head> or append
    if (content.indexOf("</head>") >= 0) {
      content = content.replace("</head>", `${scriptTag}\n</head>`);
    } else {
      content += `\n${scriptTag}`;
    }
    writeFileSync(filepath, content, "utf-8");
    return;
  }

  // Sidecar for everything else
  const sidecar = sidecarPath(filepath);
  writeFileSync(sidecar, jsonStr, "utf-8");
}

// ---------------------------------------------------------------------------
// Stamp
// ---------------------------------------------------------------------------

export interface StampOptions {
  model?: string;
  agent?: string;
  claims?: Array<string | Partial<Claim>>;
  trustScore?: number;
  classification?: string;
  evidence?: string[];
}

/**
 * Stamp a file with AKF trust metadata.
 * Creates or updates AKF metadata on the file.
 */
export function stampFile(filepath: string, options: StampOptions = {}): AKFUnit {
  const {
    model,
    agent,
    claims: rawClaims = [],
    trustScore = 0.7,
    classification,
    evidence,
  } = options;

  const claims: Partial<Claim>[] = rawClaims.map((c) => {
    const base = typeof c === "string"
      ? { c, t: trustScore, ai: true }
      : { t: trustScore, ai: true, ...c };
    if (model) {
      (base as Record<string, unknown>).origin = { type: "ai", model };
    }
    return base;
  });

  // If no claims provided, create a default stamp claim
  if (claims.length === 0) {
    const defaultClaim: Partial<Claim> = {
      c: `Stamped by ${agent || model || "akf"}`,
      t: trustScore,
      ai: true,
    };
    if (model) {
      (defaultClaim as Record<string, unknown>).origin = { type: "ai", model };
    }
    claims.push(defaultClaim);
  }

  // Add evidence to claims if provided
  if (evidence && evidence.length > 0) {
    const evidenceObjs = evidence.map((e) => ({
      type: detectEvidenceType(e),
      detail: e,
      at: nowISO(),
    }));
    for (const claim of claims) {
      claim.evidence = evidenceObjs;
    }
  }

  const unit = createMulti(claims, {
    model,
    agent,
    label: classification,
    by: agent,
    at: nowISO(),
  });

  embed(filepath, unit);
  return unit;
}

/** Auto-detect evidence type from a plain string. */
function detectEvidenceType(evidence: string): string {
  const lower = evidence.toLowerCase();
  if (/\d+\/\d+\s*tests?\s*pass/i.test(lower)) return "test_pass";
  if (/mypy|type.?check/i.test(lower)) return "type_check";
  if (/lint|eslint|pylint/i.test(lower)) return "lint_clean";
  if (/ci|pipeline|build.*pass/i.test(lower)) return "ci_pass";
  if (/review|approved/i.test(lower)) return "human_review";
  return "other";
}

// ---------------------------------------------------------------------------
// Scan
// ---------------------------------------------------------------------------

export interface ScanResult {
  enriched: boolean;
  format: string;
  claimCount: number;
  classification: string | null;
  overallTrust: number;
  aiClaimCount: number;
  validation: ValidationResult | null;
}

/**
 * Scan a file for AKF metadata and return a summary report.
 */
export function scan(filepath: string): ScanResult {
  const ext = extname(filepath).toLowerCase();
  const format = ext.replace(".", "") || "unknown";

  try {
    const unit = read(filepath);
    const validation = validate(unit);

    const claims = unit.claims || [];
    const aiClaims = claims.filter((c) => c.ai);
    const totalTrust =
      claims.length > 0
        ? claims.reduce((sum, c) => sum + (c.t || 0), 0) / claims.length
        : 0;

    return {
      enriched: true,
      format,
      claimCount: claims.length,
      classification: unit.label || null,
      overallTrust: Math.round(totalTrust * 100) / 100,
      aiClaimCount: aiClaims.length,
      validation,
    };
  } catch {
    return {
      enriched: false,
      format,
      claimCount: 0,
      classification: null,
      overallTrust: 0,
      aiClaimCount: 0,
      validation: null,
    };
  }
}
