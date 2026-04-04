import { Notice, Plugin, TFile, WorkspaceLeaf } from "obsidian";
import { createMulti } from "akf-format";
import type { Claim } from "akf-format";
import { AKFSettings, AKFSettingTab, DEFAULT_SETTINGS } from "./settings";
import { AKFStatusBar } from "./status-bar";
import { AKFSidebarView, AKF_VIEW_TYPE } from "./sidebar-view";
import { StampModal } from "./stamp-modal";
import { GraphColorizer } from "./graph-colorizer";
import { writeAKFToFile, removeAKFFromFile } from "./akf-writer";

export default class AKFPlugin extends Plugin {
  settings: AKFSettings = DEFAULT_SETTINGS;
  private statusBar!: AKFStatusBar;
  private graphColorizer!: GraphColorizer;

  async onload(): Promise<void> {
    await this.loadSettings();

    // Settings tab
    this.addSettingTab(new AKFSettingTab(this.app, this));

    // Sidebar view
    this.registerView(AKF_VIEW_TYPE, (leaf) => new AKFSidebarView(leaf, this));

    // Status bar
    this.statusBar = new AKFStatusBar(this);

    // Graph colorizer
    this.graphColorizer = new GraphColorizer(this);

    // Ribbon icon to toggle sidebar
    this.addRibbonIcon("shield", "AKF Metadata", () => {
      this.activateSidebar();
    });

    // Commands
    this.addCommand({
      id: "stamp",
      name: "Stamp this note",
      checkCallback: (checking) => {
        const file = this.app.workspace.getActiveFile();
        if (!file || file.extension !== "md") return false;
        if (!checking) {
          new StampModal(this, () => this.refreshViews()).open();
        }
        return true;
      },
    });

    this.addCommand({
      id: "quick-stamp",
      name: "Quick stamp (use defaults)",
      checkCallback: (checking) => {
        const file = this.app.workspace.getActiveFile();
        if (!file || file.extension !== "md") return false;
        if (!checking) {
          this.quickStamp(file);
        }
        return true;
      },
    });

    this.addCommand({
      id: "remove",
      name: "Remove AKF metadata",
      checkCallback: (checking) => {
        const file = this.app.workspace.getActiveFile();
        if (!file || file.extension !== "md") return false;
        if (!checking) {
          this.removeMetadata(file);
        }
        return true;
      },
    });

    this.addCommand({
      id: "show-sidebar",
      name: "Show AKF sidebar",
      callback: () => this.activateSidebar(),
    });

    // Event listeners
    this.registerEvent(
      this.app.workspace.on("file-open", (file) => {
        this.statusBar.update(file);
        this.refreshSidebar(file);
      })
    );

    this.registerEvent(
      this.app.metadataCache.on("changed", (file) => {
        const activeFile = this.app.workspace.getActiveFile();
        if (activeFile && file.path === activeFile.path) {
          this.statusBar.update(file);
          this.refreshSidebar(file);
        }
        this.graphColorizer.onMetadataChanged(file);
      })
    );

    // Initial load
    this.app.workspace.onLayoutReady(() => {
      const file = this.app.workspace.getActiveFile();
      this.statusBar.update(file);
      this.graphColorizer.rebuildTrustMap();
    });
  }

  async onunload(): Promise<void> {
    this.graphColorizer.destroy();
  }

  async loadSettings(): Promise<void> {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings(): Promise<void> {
    await this.saveData(this.settings);
  }

  async activateSidebar(): Promise<void> {
    const existing = this.app.workspace.getLeavesOfType(AKF_VIEW_TYPE);
    if (existing.length > 0) {
      this.app.workspace.revealLeaf(existing[0]);
      return;
    }

    const leaf = this.app.workspace.getRightLeaf(false);
    if (leaf) {
      await leaf.setViewState({ type: AKF_VIEW_TYPE, active: true });
      this.app.workspace.revealLeaf(leaf);
      // Refresh with current file
      const file = this.app.workspace.getActiveFile();
      this.refreshSidebar(file);
    }
  }

  private async refreshSidebar(file: TFile | null): Promise<void> {
    const leaves = this.app.workspace.getLeavesOfType(AKF_VIEW_TYPE);
    for (const leaf of leaves) {
      const view = leaf.view;
      if (view instanceof AKFSidebarView) {
        await view.refresh(file);
      }
    }
  }

  private async refreshViews(): Promise<void> {
    const file = this.app.workspace.getActiveFile();
    this.statusBar.update(file);
    this.refreshSidebar(file);
  }

  private async quickStamp(file: TFile): Promise<void> {
    const claim: Partial<Claim> = {
      c: `Stamped: ${file.basename}`,
      t: this.settings.defaultTrust,
      ai: this.settings.defaultAiGenerated,
    };

    const unit = createMulti([claim as Claim], {
      by: this.settings.defaultAgent,
      agent: this.settings.defaultAgent,
      label: this.settings.defaultClassification,
      at: new Date().toISOString(),
    });

    await writeAKFToFile(this.app, file, unit, this.settings.frontmatterKey);
    new Notice(
      `AKF quick-stamped: trust ${this.settings.defaultTrust.toFixed(2)}`
    );
    this.refreshViews();
  }

  private async removeMetadata(file: TFile): Promise<void> {
    const removed = await removeAKFFromFile(this.app, file);
    if (removed) {
      new Notice("AKF metadata removed");
    } else {
      new Notice("No AKF metadata found to remove");
    }
    this.refreshViews();
  }
}
