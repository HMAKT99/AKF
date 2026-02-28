/**
 * AKF v1.0 — Provenance chain management and integrity hashing.
 */

import { createHash } from "node:crypto";
import type { AKFUnit, ProvHop } from "./models.js";
import { stripNulls } from "./core.js";

/**
 * Compute SHA-256 hash for a provenance hop, chained to previous.
 */
export function computeHopHash(
  previousHash: string | null,
  hop: Record<string, unknown>
): string {
  let payload = JSON.stringify(hop, Object.keys(hop).sort());
  if (previousHash) {
    payload = previousHash + "|" + payload;
  }
  const digest = createHash("sha256").update(payload, "utf-8").digest("hex");
  return `sha256:${digest}`;
}

/**
 * Compute SHA-256 of entire unit contents (excluding the hash field).
 */
export function computeIntegrityHash(unit: AKFUnit): string {
  const d = stripNulls({ ...unit });
  delete (d as Record<string, unknown>)["hash"];
  const payload = JSON.stringify(d, Object.keys(d).sort());
  const digest = createHash("sha256").update(payload, "utf-8").digest("hex");
  return `sha256:${digest}`;
}

/**
 * Verify hop numbers are sequential starting at 0.
 */
export function validateChain(prov: ProvHop[]): boolean {
  for (let i = 0; i < prov.length; i++) {
    if (prov[i].hop !== i) {
      return false;
    }
  }
  return true;
}

/**
 * Add a new provenance hop to an existing unit. Auto-hashes.
 */
export function addHop(
  unit: AKFUnit,
  by: string,
  action: string,
  opts?: {
    adds?: string[];
    drops?: string[];
    penalty?: number;
  }
): AKFUnit {
  const existing = unit.prov ? [...unit.prov] : [];
  const hopNum = existing.length;
  const prevHash =
    existing.length > 0 ? existing[existing.length - 1].h || null : null;

  const hopData: Record<string, unknown> = {
    hop: hopNum,
    by,
    do: action,
    at: new Date().toISOString(),
  };
  if (opts?.adds) {
    hopData["adds"] = opts.adds;
  }
  if (opts?.drops) {
    hopData["drops"] = opts.drops;
  }
  if (opts?.penalty !== undefined) {
    hopData["pen"] = opts.penalty;
  }

  const hopHash = computeHopHash(prevHash, hopData);
  hopData["h"] = hopHash;

  const newHop = hopData as unknown as ProvHop;
  const newProv = [...existing, newHop];

  const updated: AKFUnit = { ...unit, prov: newProv };

  // Recompute integrity hash
  const integrity = computeIntegrityHash(updated);
  updated.hash = integrity;

  return updated;
}

/**
 * Return a pretty-printed provenance tree string.
 */
export function formatTree(unit: AKFUnit): string {
  if (!unit.prov || unit.prov.length === 0) {
    return "(no provenance)";
  }

  const lines: string[] = [];
  for (let i = 0; i < unit.prov.length; i++) {
    const hop = unit.prov[i];
    const hShort = hop.h ? hop.h.slice(0, 18) + "..." : "";

    let addsStr = "";
    if (hop.adds) {
      addsStr = ` (+${hop.adds.length} claims)`;
    }
    let dropsStr = "";
    if (hop.drops) {
      dropsStr = ` (-${hop.drops.length} rejected)`;
    }

    const prefix = i === 0 ? "" : "  ".repeat(i) + "\u2514\u2192 ";

    lines.push(`${prefix}${hop.by} ${hop.do}${addsStr}${dropsStr} \u2014 ${hShort}`);
  }

  return lines.join("\n");
}
