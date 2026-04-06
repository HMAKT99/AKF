import { ItemView, TFile, WorkspaceLeaf } from "obsidian";
import type { AKFUnit, Claim, ProvHop } from "akf-format";
import { effectiveTrust } from "akf-format";
import type AKFPlugin from "./main";
import { readAKFFromFile, averageTrust, hasAiClaims } from "./akf-reader";
import {
  trustBucket,
  trustColor,
  trustEmoji,
  trustLabel,
  formatDate,
  classificationColor,
} from "./utils";

export const AKF_VIEW_TYPE = "akf-sidebar";

export class AKFSidebarView extends ItemView {
  plugin: AKFPlugin;

  constructor(leaf: WorkspaceLeaf, plugin: AKFPlugin) {
    super(leaf);
    this.plugin = plugin;
  }

  getViewType(): string {
    return AKF_VIEW_TYPE;
  }

  getDisplayText(): string {
    return "AKF Metadata";
  }

  getIcon(): string {
    return "shield";
  }

  async onOpen(): Promise<void> {
    this.renderEmpty();
  }

  async onClose(): Promise<void> {
    this.contentEl.empty();
  }

  async refresh(file: TFile | null): Promise<void> {
    if (!file || file.extension !== "md") {
      this.renderEmpty();
      return;
    }

    const { unit, source } = await readAKFFromFile(
      this.plugin.app,
      file,
      this.plugin.settings
    );

    if (!unit) {
      this.renderEmpty(file.basename);
      return;
    }

    this.renderUnit(unit, file.basename, source || "frontmatter");
  }

  private renderEmpty(filename?: string): void {
    const el = this.contentEl;
    el.empty();
    const container = el.createDiv({ cls: "akf-sidebar" });
    container.createEl("p", {
      text: filename
        ? `No AKF metadata in "${filename}"`
        : "Open a note to see AKF metadata",
      cls: "akf-empty-message",
    });

    const hint = container.createEl("p", { cls: "akf-empty-hint" });
    hint.setText('Use "AKF: Stamp this note" from the command palette to add metadata.');
  }

  private renderUnit(unit: AKFUnit, filename: string, source: string): void {
    const el = this.contentEl;
    el.empty();
    const container = el.createDiv({ cls: "akf-sidebar" });

    // Header
    const header = container.createDiv({ cls: "akf-sidebar-header" });
    header.createEl("h3", { text: filename });
    header.createEl("span", {
      text: `Source: ${source}`,
      cls: "akf-source-badge",
    });

    // Trust Score (overall)
    const avg = averageTrust(unit);
    const bucket = trustBucket(avg, this.plugin.settings.trustThresholds);
    this.renderTrustScore(container, avg, bucket);

    // Classification
    if (unit.label) {
      this.renderClassification(container, unit.label);
    }

    // Agent / Author info
    this.renderInfo(container, unit);

    // Claims
    if (unit.claims?.length) {
      this.renderClaims(container, unit.claims);
    }

    // Provenance
    if (unit.prov?.length) {
      this.renderProvenance(container, unit.prov);
    }
  }

  private renderTrustScore(
    parent: HTMLElement,
    score: number,
    bucket: "high" | "medium" | "low"
  ): void {
    const section = parent.createDiv({ cls: "akf-sidebar-section" });
    const badge = section.createDiv({
      cls: `akf-trust-badge akf-trust-${bucket}`,
    });
    badge.createEl("span", {
      text: trustEmoji(bucket),
      cls: "akf-trust-emoji",
    });
    badge.createEl("span", {
      text: `${score.toFixed(2)}`,
      cls: "akf-trust-score",
    });
    badge.createEl("span", {
      text: trustLabel(bucket),
      cls: "akf-trust-label",
    });
  }

  private renderClassification(parent: HTMLElement, label: string): void {
    const section = parent.createDiv({ cls: "akf-sidebar-section" });
    const pill = section.createEl("span", {
      text: label.toUpperCase(),
      cls: "akf-classification-pill",
    });
    pill.style.backgroundColor = classificationColor(label);
  }

  private renderInfo(parent: HTMLElement, unit: AKFUnit): void {
    const section = parent.createDiv({ cls: "akf-sidebar-section akf-info-section" });
    const items: [string, string | undefined][] = [
      ["Author", unit.by],
      ["Agent", unit.agent],
      ["Model", unit.model],
      ["Created", unit.at ? formatDate(unit.at) : undefined],
      ["Session", unit.session],
      ["Version", unit.v],
    ];

    for (const [label, value] of items) {
      if (!value) continue;
      const row = section.createDiv({ cls: "akf-info-row" });
      row.createEl("span", { text: label, cls: "akf-info-label" });
      row.createEl("span", { text: value, cls: "akf-info-value" });
    }
  }

  private renderClaims(parent: HTMLElement, claims: Claim[]): void {
    const section = parent.createDiv({ cls: "akf-sidebar-section" });
    section.createEl("h4", { text: `Claims (${claims.length})` });

    for (const claim of claims) {
      const card = section.createDiv({ cls: "akf-claim-card" });

      // Claim header: trust + AI badge
      const claimHeader = card.createDiv({ cls: "akf-claim-header" });
      const trustResult = effectiveTrust(claim);
      const bucket = trustBucket(
        trustResult.score,
        this.plugin.settings.trustThresholds
      );
      claimHeader.createEl("span", {
        text: `${trustEmoji(bucket)} ${trustResult.score.toFixed(2)}`,
        cls: `akf-claim-trust akf-trust-${bucket}`,
      });

      if (claim.ai) {
        claimHeader.createEl("span", { text: "AI", cls: "akf-ai-badge" });
      }
      if (claim.ver) {
        claimHeader.createEl("span", {
          text: "Verified",
          cls: "akf-verified-badge",
        });
      }

      // Content
      card.createEl("p", { text: claim.c, cls: "akf-claim-content" });

      // Source
      if (claim.src) {
        card.createEl("p", {
          text: `Source: ${claim.src}`,
          cls: "akf-claim-source",
        });
      }

      // Evidence
      if (claim.evidence?.length) {
        const evList = card.createEl("ul", { cls: "akf-evidence-list" });
        for (const ev of claim.evidence) {
          const li = evList.createEl("li", { cls: "akf-evidence-item" });
          li.createEl("span", {
            text: ev.type.replace(/_/g, " "),
            cls: "akf-evidence-type",
          });
          li.createEl("span", { text: `: ${ev.detail}` });
        }
      }

      // Tags
      if (claim.tags?.length) {
        const tagRow = card.createDiv({ cls: "akf-tag-row" });
        for (const tag of claim.tags) {
          tagRow.createEl("span", { text: tag, cls: "akf-tag" });
        }
      }
    }
  }

  private renderProvenance(parent: HTMLElement, prov: ProvHop[]): void {
    const section = parent.createDiv({ cls: "akf-sidebar-section" });
    section.createEl("h4", { text: `Provenance (${prov.length} hops)` });

    const timeline = section.createDiv({ cls: "akf-provenance-timeline" });

    for (const hop of prov) {
      const entry = timeline.createDiv({ cls: "akf-prov-entry" });
      const dot = entry.createDiv({ cls: "akf-prov-dot" });
      const body = entry.createDiv({ cls: "akf-prov-body" });

      body.createEl("strong", {
        text: `${hop.do} by ${hop.by}`,
      });
      if (hop.at) {
        body.createEl("span", {
          text: formatDate(hop.at),
          cls: "akf-prov-time",
        });
      }
      if (hop.model) {
        body.createEl("span", {
          text: `Model: ${hop.model}`,
          cls: "akf-prov-model",
        });
      }
      if (hop.pen) {
        body.createEl("span", {
          text: `Penalty: ${hop.pen}`,
          cls: "akf-prov-penalty",
        });
      }
    }
  }
}
