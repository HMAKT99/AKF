/**
 * AKF v1.0 — Security classification and inheritance.
 */

import type { AKFUnit } from "./models.js";

/** Classification hierarchy: lower number = less restrictive. */
export const HIERARCHY: Record<string, number> = {
  public: 0,
  internal: 1,
  confidential: 2,
  "highly-confidential": 3,
  restricted: 4,
};

/** Return numeric rank for a classification label. Defaults to 0 (public). */
export function labelRank(label: string | undefined): number {
  if (label === undefined) {
    return 0;
  }
  return HIERARCHY[label] ?? 0;
}

/**
 * Check child label >= parent label when parent.inherit is true.
 *
 * Returns true if inheritance is valid, false if child is less restrictive.
 */
export function validateInheritance(parent: AKFUnit, child: AKFUnit): boolean {
  if (parent.inherit === false) {
    return true; // No inheritance constraint
  }
  return labelRank(child.label) >= labelRank(parent.label);
}

/** Check if the unit can be shared externally. */
export function canShareExternal(unit: AKFUnit): boolean {
  if (unit.ext === true) {
    return true;
  }
  if (
    unit.label === "confidential" ||
    unit.label === "highly-confidential" ||
    unit.label === "restricted"
  ) {
    return false;
  }
  return unit.ext !== false && labelRank(unit.label) <= HIERARCHY["internal"];
}

/** Return security fields to copy to a derived .akf. */
export function inheritLabel(
  parent: AKFUnit
): Partial<Pick<AKFUnit, "label" | "inherit" | "ext">> {
  const fields: Partial<Pick<AKFUnit, "label" | "inherit" | "ext">> = {};
  if (parent.inherit !== false && parent.label) {
    fields.label = parent.label;
    fields.inherit = parent.inherit;
  }
  if (parent.ext !== undefined) {
    fields.ext = parent.ext;
  }
  return fields;
}
