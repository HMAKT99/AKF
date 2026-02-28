/**
 * AKF v1.0 — AKFTransformer: filter, derive, and transform AKF units.
 */

import { randomUUID } from "node:crypto";
import type { AKFUnit, Claim } from "./models.js";
import { addHop } from "./provenance.js";
import { inheritLabel } from "./security.js";
import { effectiveTrust } from "./trust.js";

/** Transform a parent .akf into a derived .akf. */
export class AKFTransformer {
  private _parent: AKFUnit;
  private _claims: Claim[];
  private _penalty: number = 0;
  private _agent: string | undefined;
  private _accepted: string[] = [];
  private _rejected: string[] = [];
  private _trustMin: number | undefined;

  constructor(parent: AKFUnit) {
    this._parent = parent;
    this._claims = [...parent.claims];
  }

  /** Keep only claims above trust threshold (based on effective trust). */
  filter(trustMin: number = 0.6): this {
    this._trustMin = trustMin;
    const kept: Claim[] = [];
    for (const claim of this._claims) {
      const result = effectiveTrust(claim);
      if (result.score >= trustMin) {
        kept.push(claim);
        if (claim.id) {
          this._accepted.push(claim.id);
        }
      } else {
        if (claim.id) {
          this._rejected.push(claim.id);
        }
      }
    }
    this._claims = kept;
    return this;
  }

  /** Apply transform penalty to all retained claims. */
  penalty(pen: number = -0.03): this {
    this._penalty = pen;
    const adjusted: Claim[] = [];
    for (const claim of this._claims) {
      const newT = Math.max(0.0, claim.t + pen);
      adjusted.push({
        ...claim,
        t: Math.round(newT * 10000) / 10000,
      });
    }
    this._claims = adjusted;
    return this;
  }

  /** Set the transforming agent. */
  by(agent: string): this {
    this._agent = agent;
    return this;
  }

  /** Build derived .akf with inherited classification and provenance. */
  build(): AKFUnit {
    if (this._claims.length === 0) {
      throw new Error(
        "No claims survived filtering — cannot build empty AKF"
      );
    }

    const now = new Date().toISOString();
    const newId = `akf-${randomUUID().replace(/-/g, "").slice(0, 12)}`;

    // Inherit security from parent
    const security = inheritLabel(this._parent);

    // Build the derived unit (without the consumed hop first)
    let derived: AKFUnit = {
      v: "1.0",
      id: newId,
      claims: this._claims,
      by: this._agent,
      at: now,
      prov: this._parent.prov ? [...this._parent.prov] : [],
      meta: { parent_id: this._parent.id },
      ...security,
    };

    // Add the consumption/transform hop
    const actor = this._agent || "unknown";
    derived = addHop(derived, actor, "consumed", {
      adds: this._accepted.length > 0 ? this._accepted : undefined,
      drops: this._rejected.length > 0 ? this._rejected : undefined,
      penalty: this._penalty !== 0 ? this._penalty : undefined,
    });

    return derived;
  }
}
