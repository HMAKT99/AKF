import { App, Modal, Setting, Notice } from "obsidian";
import type { Claim } from "akf-format";
import { createMulti } from "akf-format";
import type AKFPlugin from "./main";
import { writeAKFToFile } from "./akf-writer";
import { trustBucket, trustColor } from "./utils";

export class StampModal extends Modal {
  plugin: AKFPlugin;
  agent: string;
  trustScore: number;
  classification: string;
  aiGenerated: boolean;
  evidenceText: string;

  private onStamped: () => void;

  constructor(plugin: AKFPlugin, onStamped: () => void) {
    super(plugin.app);
    this.plugin = plugin;
    this.onStamped = onStamped;

    // Initialize from settings
    this.agent = plugin.settings.defaultAgent;
    this.trustScore = plugin.settings.defaultTrust;
    this.classification = plugin.settings.defaultClassification;
    this.aiGenerated = plugin.settings.defaultAiGenerated;
    this.evidenceText = "";
  }

  onOpen(): void {
    const { contentEl } = this;
    contentEl.empty();
    contentEl.addClass("akf-stamp-modal");

    contentEl.createEl("h2", { text: "Stamp Note with AKF Metadata" });

    new Setting(contentEl)
      .setName("Agent")
      .setDesc("Who or what is stamping this note")
      .addText((text) =>
        text
          .setPlaceholder("obsidian")
          .setValue(this.agent)
          .onChange((value) => {
            this.agent = value;
          })
      );

    const trustSetting = new Setting(contentEl)
      .setName("Trust score")
      .setDesc(`${this.trustScore.toFixed(2)}`);

    trustSetting.addSlider((slider) =>
      slider
        .setLimits(0, 1, 0.05)
        .setValue(this.trustScore)
        .setDynamicTooltip()
        .onChange((value) => {
          this.trustScore = value;
          trustSetting.setDesc(`${value.toFixed(2)}`);
          // Update preview color
          const bucket = trustBucket(value, this.plugin.settings.trustThresholds);
          const preview = contentEl.querySelector(".akf-stamp-preview");
          if (preview instanceof HTMLElement) {
            preview.style.borderLeftColor = trustColor(bucket);
          }
        })
    );

    new Setting(contentEl)
      .setName("Classification")
      .addDropdown((dropdown) =>
        dropdown
          .addOption("public", "Public")
          .addOption("internal", "Internal")
          .addOption("confidential", "Confidential")
          .addOption("restricted", "Restricted")
          .setValue(this.classification)
          .onChange((value) => {
            this.classification = value;
          })
      );

    new Setting(contentEl)
      .setName("AI-generated")
      .setDesc("Was this note created or assisted by AI?")
      .addToggle((toggle) =>
        toggle.setValue(this.aiGenerated).onChange((value) => {
          this.aiGenerated = value;
        })
      );

    new Setting(contentEl)
      .setName("Evidence")
      .setDesc("Optional evidence supporting trust (e.g., 'tests pass', 'reviewed by team')")
      .addTextArea((text) =>
        text
          .setPlaceholder("e.g., reviewed by team, facts verified")
          .setValue(this.evidenceText)
          .onChange((value) => {
            this.evidenceText = value;
          })
      );

    // Preview
    const bucket = trustBucket(this.trustScore, this.plugin.settings.trustThresholds);
    const preview = contentEl.createDiv({ cls: "akf-stamp-preview" });
    preview.style.borderLeftColor = trustColor(bucket);
    preview.createEl("span", { text: "Preview: metadata will be added to frontmatter" });

    // Submit button
    new Setting(contentEl).addButton((btn) =>
      btn
        .setButtonText("Stamp")
        .setCta()
        .onClick(async () => {
          await this.doStamp();
          this.close();
        })
    );
  }

  onClose(): void {
    this.contentEl.empty();
  }

  private async doStamp(): Promise<void> {
    const file = this.app.workspace.getActiveFile();
    if (!file || file.extension !== "md") {
      new Notice("No active markdown file to stamp");
      return;
    }

    const claim: Partial<Claim> = {
      c: `Stamped: ${file.basename}`,
      t: this.trustScore,
      ai: this.aiGenerated,
    };

    if (this.evidenceText.trim()) {
      claim.evidence = [
        {
          type: detectEvidenceType(this.evidenceText),
          detail: this.evidenceText.trim(),
          at: new Date().toISOString(),
        },
      ];
    }

    const unit = createMulti([claim as Claim], {
      by: this.agent,
      agent: this.agent,
      label: this.classification,
      at: new Date().toISOString(),
    });

    await writeAKFToFile(
      this.app,
      file,
      unit,
      this.plugin.settings.frontmatterKey
    );

    new Notice(`AKF stamped: trust ${this.trustScore.toFixed(2)}, ${this.classification}`);
    this.onStamped();
  }
}

function detectEvidenceType(evidence: string): string {
  const lower = evidence.toLowerCase();
  if (/\d+\/\d+\s*tests?\s*pass/i.test(lower)) return "test_pass";
  if (/type.?check/i.test(lower)) return "type_check";
  if (/lint/i.test(lower)) return "lint_clean";
  if (/ci|pipeline|build.*pass/i.test(lower)) return "ci_pass";
  if (/review|approved/i.test(lower)) return "human_review";
  return "other";
}
