import { App, TFile } from "obsidian";
import type { AKFUnit } from "akf-format";
import { normalizeUnit, fromJSON } from "akf-format";
import type { AKFSettings } from "./settings";

export interface AKFReadResult {
  unit: AKFUnit | null;
  source: "frontmatter" | "sidecar" | null;
}

export async function readAKFFromFile(
  app: App,
  file: TFile,
  settings: AKFSettings
): Promise<AKFReadResult> {
  // 1. Check frontmatter via metadataCache
  const cache = app.metadataCache.getFileCache(file);
  const fm = cache?.frontmatter;

  if (fm) {
    // Try configured key, then fallback to the other
    const keys = [settings.frontmatterKey, settings.frontmatterKey === "akf" ? "_akf" : "akf"];
    for (const key of keys) {
      const raw = fm[key];
      if (raw != null) {
        try {
          const parsed = typeof raw === "string" ? JSON.parse(raw) : raw;
          // If parsed is already a full unit (has v + claims), normalize it
          if (parsed.v && parsed.claims) {
            return { unit: normalizeUnit(parsed), source: "frontmatter" };
          }
          // If it's a partial (e.g., just classification), wrap it
          if (typeof parsed === "object") {
            return { unit: normalizeUnit(parsed), source: "frontmatter" };
          }
        } catch {
          // Invalid JSON in frontmatter, skip
        }
      }
    }
  }

  // 2. Check sidecar file
  if (settings.checkSidecar) {
    const sidecarPath = file.path + ".akf.json";
    if (await app.vault.adapter.exists(sidecarPath)) {
      try {
        const content = await app.vault.adapter.read(sidecarPath);
        const unit = fromJSON(content);
        return { unit, source: "sidecar" };
      } catch {
        // Invalid sidecar, skip
      }
    }
  }

  return { unit: null, source: null };
}

/**
 * Compute average trust across all claims in a unit.
 */
export function averageTrust(unit: AKFUnit): number {
  const claims = unit.claims || [];
  if (claims.length === 0) return 0;
  const sum = claims.reduce((acc, c) => acc + (c.t ?? 0), 0);
  return sum / claims.length;
}

/**
 * Check if any claim is AI-generated.
 */
export function hasAiClaims(unit: AKFUnit): boolean {
  return (unit.claims || []).some((c) => c.ai === true);
}
