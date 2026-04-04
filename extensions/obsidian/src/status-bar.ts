import { TFile } from "obsidian";
import type AKFPlugin from "./main";
import { readAKFFromFile, averageTrust, hasAiClaims } from "./akf-reader";
import { trustBucket, trustEmoji, trustLabel } from "./utils";
import { AKF_VIEW_TYPE } from "./sidebar-view";

export class AKFStatusBar {
  private el: HTMLElement;
  private plugin: AKFPlugin;

  constructor(plugin: AKFPlugin) {
    this.plugin = plugin;
    this.el = plugin.addStatusBarItem();
    this.el.addClass("akf-status-bar");
    this.el.addEventListener("click", () => {
      this.plugin.activateSidebar();
    });
    this.clear();
  }

  async update(file: TFile | null): Promise<void> {
    if (!this.plugin.settings.showStatusBar) {
      this.el.style.display = "none";
      return;
    }
    this.el.style.display = "";

    if (!file || file.extension !== "md") {
      this.clear();
      return;
    }

    const { unit } = await readAKFFromFile(
      this.plugin.app,
      file,
      this.plugin.settings
    );

    if (!unit || !unit.claims?.length) {
      this.el.setText("AKF: --");
      this.el.title = "No AKF metadata";
      return;
    }

    const avg = averageTrust(unit);
    const bucket = trustBucket(avg, this.plugin.settings.trustThresholds);
    const emoji = trustEmoji(bucket);
    const label = trustLabel(bucket);
    const aiFlag = hasAiClaims(unit) ? " | AI" : "";

    this.el.setText(`${emoji} Trust: ${avg.toFixed(2)} (${label})${aiFlag}`);
    this.el.title = `AKF: ${unit.claims.length} claim(s), classification: ${unit.label || "none"}`;
  }

  clear(): void {
    this.el.setText("AKF: --");
    this.el.title = "No AKF metadata";
  }

  hide(): void {
    this.el.style.display = "none";
  }
}
