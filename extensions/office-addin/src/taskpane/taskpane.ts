import { AKFMetadata, AKFClaim, audit, createDefaultMetadata, runAllDetections } from "../shared/akf-core";
import { extractAKF, embedAKF } from "../shared/office-xml";
import {
  renderHeader,
  renderClaims,
  renderProvenance,
  renderAudit,
  renderDetection,
  renderEmpty,
} from "../shared/ui";

let currentMetadata: AKFMetadata | null = null;
let currentView = "overview";

Office.onReady(async () => {
  await loadMetadata();
  setupTabs();
});

async function loadMetadata(): Promise<void> {
  try {
    currentMetadata = await extractAKF();
  } catch (err) {
    console.error("Failed to load AKF metadata:", err);
    currentMetadata = null;
  }
  renderCurrentView();
}

function setupTabs(): void {
  document.querySelectorAll<HTMLButtonElement>(".tab").forEach((btn) => {
    btn.addEventListener("click", () => {
      document
        .querySelectorAll(".tab")
        .forEach((t) => t.classList.remove("active"));
      btn.classList.add("active");
      currentView = btn.dataset.view ?? "overview";
      renderCurrentView();
    });
  });
}

function showError(container: HTMLElement, msg: string): void {
  container.innerHTML = `
    <div style="padding:16px;background:#451a1a;border:1px solid #7f1d1d;border-radius:6px;margin:8px 0">
      <div style="color:#fca5a5;font-size:13px">${msg}</div>
    </div>
  `;
}

function renderCurrentView(): void {
  const content = document.getElementById("content");
  if (!content) return;

  if (!currentMetadata) {
    renderEmpty(content);
    const embedBtn = document.getElementById("embed-cta");
    if (embedBtn) {
      embedBtn.addEventListener("click", async () => {
        try {
          const meta = createDefaultMetadata();
          await embedAKF(meta);
          currentMetadata = meta;
          renderCurrentView();
        } catch (err) {
          showError(content, `Failed to embed metadata: ${err}`);
        }
      });
    }
    return;
  }

  switch (currentView) {
    case "overview":
      renderHeader(content, currentMetadata);
      break;
    case "claims":
      renderClaims(content, currentMetadata.claims, async (claim: AKFClaim) => {
        if (!currentMetadata) return;
        currentMetadata.claims.push(claim);
        if (!currentMetadata.provenance) currentMetadata.provenance = [];
        currentMetadata.provenance.push({
          hop: currentMetadata.provenance.length + 1,
          actor: "office-addin",
          action: "claim_added",
          timestamp: new Date().toISOString(),
          claims_added: [claim.id || "unknown"],
        });
        try {
          await embedAKF(currentMetadata);
          renderCurrentView();
        } catch (err) {
          showError(content, `Failed to save claim: ${err}`);
        }
      });
      break;
    case "provenance":
      renderProvenance(content, currentMetadata);
      break;
    case "audit": {
      const result = audit(currentMetadata);
      renderAudit(content, result);
      break;
    }
    case "detection": {
      const report = runAllDetections(currentMetadata);
      renderDetection(content, report);
      break;
    }
  }
}
