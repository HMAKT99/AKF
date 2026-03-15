/**
 * DOM rendering helpers for the AKF taskpane.
 */

import {
  AKFMetadata,
  AKFClaim,
  AuditResult,
  DetectionReport,
  trustColor,
  trustLabel,
  overallTrust,
} from "./akf-core";

function esc(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

export function renderHeader(
  container: HTMLElement,
  meta: AKFMetadata
): void {
  const trust = overallTrust(meta.claims);
  const color = trustColor(trust);

  container.innerHTML = `
    <div style="margin-bottom:16px">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px">
        <span style="font-size:14px;font-weight:600">AKF Trust Metadata</span>
        ${
          meta.classification
            ? `<span style="background:#334155;color:#94a3b8;padding:2px 8px;border-radius:4px;font-size:11px;text-transform:uppercase">${meta.classification}</span>`
            : ""
        }
      </div>
      <div style="display:flex;align-items:center;gap:8px">
        <span style="width:10px;height:10px;border-radius:50%;background:${color};display:inline-block"></span>
        <span style="font-size:13px;color:#cbd5e1">Trust: ${trust.toFixed(2)} (${trustLabel(trust)})</span>
      </div>
      <div style="font-size:12px;color:#64748b;margin-top:4px">${meta.claims.length} claim(s)</div>
    </div>
  `;
}

export function renderClaims(
  container: HTMLElement,
  claims: AKFClaim[],
  onAddClaim?: (claim: AKFClaim) => void
): void {
  const items = claims.length === 0
    ? `<div style="color:#64748b;font-size:13px;padding:12px 0">No claims found.</div>`
    : claims
        .map((c) => {
          const color = trustColor(c.confidence);
          const badges: string[] = [];
          if (c.source) badges.push(`<span style="color:#94a3b8;font-size:11px">${esc(c.source)}</span>`);
          if (c.verified) badges.push(`<span style="color:#22c55e;font-size:11px">verified</span>`);
          if (c.ai_generated) badges.push(`<span style="color:#eab308;font-size:11px">AI</span>`);

          return `
            <div style="padding:8px 0;border-bottom:1px solid #1e293b">
              <div style="display:flex;align-items:flex-start;gap:8px">
                <span style="width:8px;height:8px;border-radius:50%;background:${color};display:inline-block;margin-top:5px;flex-shrink:0"></span>
                <div>
                  <div style="font-size:13px;color:#e2e8f0">${esc(c.content)}</div>
                  <div style="display:flex;gap:8px;margin-top:4px;align-items:center">
                    <span style="color:${color};font-size:11px;font-weight:600">${c.confidence.toFixed(2)}</span>
                    ${badges.join("")}
                  </div>
                  ${c.risk ? `<div style="color:#ef4444;font-size:11px;margin-top:2px">Risk: ${esc(c.risk)}</div>` : ""}
                </div>
              </div>
            </div>
          `;
        })
        .join("");

  const addClaimForm = onAddClaim
    ? `
    <div style="margin-top:16px;border-top:1px solid #1e293b;padding-top:12px">
      <button id="add-claim-toggle" style="
        background:none;border:1px solid #334155;color:#94a3b8;padding:6px 14px;
        border-radius:4px;font-size:12px;cursor:pointer;width:100%
      ">+ Add Claim</button>
      <div id="add-claim-form" style="display:none;margin-top:12px">
        <div style="margin-bottom:8px">
          <label style="font-size:11px;color:#94a3b8;display:block;margin-bottom:4px">Content</label>
          <textarea id="claim-content" rows="3" style="
            width:100%;background:#1e293b;border:1px solid #334155;color:#e2e8f0;
            padding:6px 8px;border-radius:4px;font-size:12px;resize:vertical;font-family:inherit
          " placeholder="Enter claim content..."></textarea>
        </div>
        <div style="margin-bottom:8px">
          <label style="font-size:11px;color:#94a3b8;display:block;margin-bottom:4px">
            Confidence: <span id="conf-display">0.80</span>
          </label>
          <input id="claim-confidence" type="range" min="0" max="1" step="0.01" value="0.8" style="width:100%" />
        </div>
        <div style="margin-bottom:8px">
          <label style="font-size:11px;color:#94a3b8;display:block;margin-bottom:4px">Source</label>
          <input id="claim-source" type="text" style="
            width:100%;background:#1e293b;border:1px solid #334155;color:#e2e8f0;
            padding:6px 8px;border-radius:4px;font-size:12px
          " placeholder="Source attribution" />
        </div>
        <div style="margin-bottom:8px;display:flex;align-items:center;gap:8px">
          <input id="claim-ai" type="checkbox" />
          <label for="claim-ai" style="font-size:12px;color:#94a3b8">AI-generated</label>
        </div>
        <div id="claim-risk-row" style="display:none;margin-bottom:8px">
          <label style="font-size:11px;color:#94a3b8;display:block;margin-bottom:4px">Risk description</label>
          <input id="claim-risk" type="text" style="
            width:100%;background:#1e293b;border:1px solid #334155;color:#e2e8f0;
            padding:6px 8px;border-radius:4px;font-size:12px
          " placeholder="Describe risk..." />
        </div>
        <button id="claim-submit" style="
          background:#3b82f6;color:white;border:none;padding:8px 16px;
          border-radius:4px;font-size:12px;cursor:pointer;font-weight:500;width:100%
        ">Add Claim</button>
      </div>
    </div>
  `
    : "";

  container.innerHTML = `<div>${items}${addClaimForm}</div>`;

  // Wire up form interactions
  if (onAddClaim) {
    const toggle = document.getElementById("add-claim-toggle");
    const form = document.getElementById("add-claim-form");
    if (toggle && form) {
      toggle.addEventListener("click", () => {
        form.style.display = form.style.display === "none" ? "block" : "none";
        toggle.textContent = form.style.display === "none" ? "+ Add Claim" : "Cancel";
      });
    }

    const confSlider = document.getElementById("claim-confidence") as HTMLInputElement | null;
    const confDisplay = document.getElementById("conf-display");
    if (confSlider && confDisplay) {
      confSlider.addEventListener("input", () => {
        confDisplay.textContent = parseFloat(confSlider.value).toFixed(2);
      });
    }

    const aiCheck = document.getElementById("claim-ai") as HTMLInputElement | null;
    const riskRow = document.getElementById("claim-risk-row");
    if (aiCheck && riskRow) {
      aiCheck.addEventListener("change", () => {
        riskRow.style.display = aiCheck.checked ? "block" : "none";
      });
    }

    const submitBtn = document.getElementById("claim-submit");
    if (submitBtn) {
      submitBtn.addEventListener("click", () => {
        const content = (document.getElementById("claim-content") as HTMLTextAreaElement)?.value?.trim();
        if (!content) return;

        const confidence = parseFloat(
          (document.getElementById("claim-confidence") as HTMLInputElement)?.value ?? "0.8"
        );
        const source = (document.getElementById("claim-source") as HTMLInputElement)?.value?.trim() || undefined;
        const aiGenerated = (document.getElementById("claim-ai") as HTMLInputElement)?.checked ?? false;
        const risk = aiGenerated
          ? (document.getElementById("claim-risk") as HTMLInputElement)?.value?.trim() || undefined
          : undefined;

        const claim: AKFClaim = {
          id: crypto.randomUUID(),
          content,
          confidence,
          source,
          ai_generated: aiGenerated,
          risk,
        };

        // Reset form
        (document.getElementById("claim-content") as HTMLTextAreaElement).value = "";
        (document.getElementById("claim-source") as HTMLInputElement).value = "";
        (document.getElementById("claim-risk") as HTMLInputElement).value = "";
        if (confSlider) confSlider.value = "0.8";
        if (confDisplay) confDisplay.textContent = "0.80";
        if (aiCheck) aiCheck.checked = false;
        if (riskRow) riskRow.style.display = "none";

        onAddClaim(claim);
      });
    }
  }
}

export function renderProvenance(
  container: HTMLElement,
  meta: AKFMetadata
): void {
  const prov = meta.provenance;
  if (!prov || prov.length === 0) {
    container.innerHTML = `<div style="color:#64748b;font-size:13px;padding:12px 0">No provenance recorded.</div>`;
    return;
  }

  const items = prov
    .map(
      (hop) => `
      <div style="display:flex;gap:8px;padding:6px 0;border-left:2px solid #334155;padding-left:12px;margin-left:4px">
        <div>
          <div style="font-size:13px;color:#e2e8f0"><strong>${esc(hop.actor)}</strong> &mdash; ${esc(hop.action)}</div>
          <div style="font-size:11px;color:#64748b">${hop.timestamp}</div>
        </div>
      </div>
    `
    )
    .join("");

  container.innerHTML = `
    <div style="margin-top:8px">
      <div style="font-size:13px;font-weight:600;color:#94a3b8;margin-bottom:8px">Provenance</div>
      ${items}
    </div>
  `;
}

export function renderAudit(
  container: HTMLElement,
  result: AuditResult
): void {
  const statusColor = result.compliant ? "#22c55e" : "#ef4444";
  const statusText = result.compliant ? "COMPLIANT" : "NON-COMPLIANT";

  const checkItems = result.checks
    .map(
      (c) =>
        `<div style="padding:4px 0;font-size:13px">
          ${c.passed ? "\u2705" : "\u274c"} ${c.check.replace(/_/g, " ")}
        </div>`
    )
    .join("");

  const recs = result.recommendations.length > 0
    ? `<div style="margin-top:12px">
        <div style="font-size:12px;font-weight:600;color:#94a3b8;margin-bottom:4px">Recommendations</div>
        ${result.recommendations.map((r) => `<div style="font-size:12px;color:#cbd5e1;padding:2px 0">\u2022 ${r}</div>`).join("")}
      </div>`
    : "";

  container.innerHTML = `
    <div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
        <span style="color:${statusColor};font-weight:600;font-size:14px">${statusText}</span>
        <span style="color:#64748b;font-size:13px">(score: ${result.score.toFixed(2)})</span>
      </div>
      ${checkItems}
      ${recs}
    </div>
  `;
}

export function renderDetection(
  container: HTMLElement,
  report: DetectionReport
): void {
  const severityColors: Record<string, string> = {
    critical: "#ef4444",
    high: "#f97316",
    medium: "#eab308",
    low: "#3b82f6",
    info: "#6b7280",
  };

  const triggeredCount = report.triggered_count;
  const summaryParts: string[] = [`${triggeredCount} / 10 triggered`];
  if (report.critical_count > 0) summaryParts.push(`${report.critical_count} critical`);
  if (report.high_count > 0) summaryParts.push(`${report.high_count} high`);

  const summaryColor = report.critical_count > 0
    ? "#ef4444"
    : report.high_count > 0
      ? "#f97316"
      : triggeredCount > 0
        ? "#eab308"
        : "#22c55e";

  const resultItems = report.results
    .map((r) => {
      const name = r.detection_class.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase());
      const badgeColor = severityColors[r.severity] || "#6b7280";

      if (!r.triggered) {
        return `
          <div style="padding:8px 0;border-bottom:1px solid #1e293b;opacity:0.6">
            <div style="display:flex;align-items:center;gap:8px">
              <span style="color:#22c55e;font-size:11px">\u2713</span>
              <span style="font-size:13px;color:#94a3b8">${name}</span>
              <span style="background:${badgeColor}22;color:${badgeColor};padding:1px 6px;border-radius:3px;font-size:10px;text-transform:uppercase">${r.severity}</span>
            </div>
          </div>
        `;
      }

      const findingsHtml = r.findings
        .map((f) => `<div style="font-size:12px;color:#cbd5e1;padding:2px 0">\u2022 ${esc(f)}</div>`)
        .join("");

      return `
        <div style="padding:8px 0;border-bottom:1px solid #1e293b">
          <details>
            <summary style="cursor:pointer;display:flex;align-items:center;gap:8px;list-style:none">
              <span style="color:${badgeColor};font-size:11px">\u26a0</span>
              <span style="font-size:13px;color:#e2e8f0;font-weight:500">${name}</span>
              <span style="background:${badgeColor}22;color:${badgeColor};padding:1px 6px;border-radius:3px;font-size:10px;text-transform:uppercase">${r.severity}</span>
            </summary>
            <div style="margin-top:8px;padding-left:20px">
              ${findingsHtml}
              ${r.recommendation ? `<div style="font-size:11px;color:#3b82f6;margin-top:6px">${r.recommendation}</div>` : ""}
            </div>
          </details>
        </div>
      `;
    })
    .join("");

  container.innerHTML = `
    <div>
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
        <span style="color:${summaryColor};font-weight:600;font-size:14px">${summaryParts[0]}</span>
        ${summaryParts.slice(1).map((p) => `<span style="color:#64748b;font-size:12px">(${p})</span>`).join("")}
      </div>
      ${resultItems}
    </div>
  `;
}

export function renderEmpty(container: HTMLElement): void {
  container.innerHTML = `
    <div style="text-align:center;padding:40px 20px">
      <div style="font-size:14px;color:#94a3b8;margin-bottom:12px">No AKF metadata found</div>
      <div style="font-size:13px;color:#64748b;margin-bottom:20px">
        This document doesn't have trust metadata yet.
      </div>
      <button id="embed-cta" style="
        background:#3b82f6;color:white;border:none;padding:10px 24px;
        border-radius:6px;font-size:13px;cursor:pointer;font-weight:500
      ">Embed Metadata</button>
    </div>
  `;
}
