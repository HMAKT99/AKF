import { TFile, debounce } from "obsidian";
import type AKFPlugin from "./main";
import { readAKFFromFile, averageTrust } from "./akf-reader";
import { trustBucket, trustColor, type TrustBucket } from "./utils";

export class GraphColorizer {
  private plugin: AKFPlugin;
  private styleEl: HTMLStyleElement;
  private trustMap: Map<string, TrustBucket> = new Map();
  private debouncedRebuild: () => void;

  constructor(plugin: AKFPlugin) {
    this.plugin = plugin;

    this.styleEl = document.createElement("style");
    this.styleEl.id = "akf-graph-colors";
    document.head.appendChild(this.styleEl);

    this.debouncedRebuild = debounce(
      () => this.rebuildTrustMap(),
      2000,
      true
    );
  }

  async rebuildTrustMap(): Promise<void> {
    if (this.plugin.settings.graphColoring === "off") {
      this.styleEl.textContent = "";
      return;
    }

    const files = this.plugin.app.vault.getMarkdownFiles();
    this.trustMap.clear();

    for (const file of files) {
      try {
        const { unit } = await readAKFFromFile(
          this.plugin.app,
          file,
          this.plugin.settings
        );
        if (unit?.claims?.length) {
          const avg = averageTrust(unit);
          const bucket = trustBucket(avg, this.plugin.settings.trustThresholds);
          this.trustMap.set(file.path, bucket);
        }
      } catch {
        // Skip files that fail to read
      }
    }

    this.generateCSS();
  }

  private generateCSS(): void {
    if (this.trustMap.size === 0) {
      this.styleEl.textContent = "";
      return;
    }

    const rules: string[] = [];

    // Generate per-file CSS rules targeting graph nodes
    // Obsidian's graph view uses data-id attributes on node containers
    for (const [filePath, bucket] of this.trustMap) {
      const color = trustColor(bucket);
      // Remove .md extension for the data-id selector
      const nodeId = filePath.replace(/\.md$/, "");
      // Escape special characters in CSS selector
      const escapedId = CSS.escape(nodeId);

      // Target both the circle fill and the node text
      rules.push(
        `.graph-view .links ~ .nodes .node[data-id="${escapedId}"] circle { fill: ${color} !important; }`,
        `.graph-view .links ~ .nodes .node[data-id="${escapedId}"] .node-text { color: ${color} !important; }`
      );
    }

    this.styleEl.textContent = rules.join("\n");
  }

  onMetadataChanged(file: TFile): void {
    if (file.extension === "md") {
      this.debouncedRebuild();
    }
  }

  destroy(): void {
    this.styleEl.remove();
    this.trustMap.clear();
  }
}
