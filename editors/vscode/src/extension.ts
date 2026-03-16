/**
 * AKF VS Code Extension
 *
 * Detects AI-generated content (Copilot, Cursor, Continue, Codeium) and
 * auto-stamps files with AKF trust metadata on save.
 *
 * Detection strategy:
 * 1. Monitor text edits — large insertions (>threshold chars in a single
 *    edit batch) are flagged as potential AI completions.
 * 2. Check if known AI extensions are active (GitHub Copilot, Cursor, etc.)
 * 3. On save: if AI edits were detected since last save, run `akf stamp`.
 */

import * as vscode from "vscode";
import { execFile } from "child_process";
import { promisify } from "util";
import * as path from "path";

const execFileAsync = promisify(execFile);

// Known AI-assist extension IDs
const AI_EXTENSION_IDS = [
  "GitHub.copilot",
  "GitHub.copilot-chat",
  "Continue.continue",
  "Codeium.codeium",
  "TabNine.tabnine-vscode",
  "AmazonWebServices.aws-toolkit-vscode", // CodeWhisperer
  "Supermaven.supermaven",
];

// Per-document tracking of AI edits since last save
const aiEditTracker = new Map<string, { insertions: number; totalChars: number }>();

let statusBarItem: vscode.StatusBarItem;
let outputChannel: vscode.OutputChannel;

// ─── Activation ──────────────────────────────────────────────────────

export function activate(context: vscode.ExtensionContext) {
  outputChannel = vscode.window.createOutputChannel("AKF");
  outputChannel.appendLine("AKF extension activated");

  // Status bar
  statusBarItem = vscode.window.createStatusBarItem(
    vscode.StatusBarAlignment.Right,
    50
  );
  statusBarItem.command = "akf.inspectFile";
  context.subscriptions.push(statusBarItem);
  updateStatusBar();

  // Track document edits for AI detection
  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument(onDocumentChange)
  );

  // Auto-stamp on save
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument(onDocumentSave)
  );

  // Update status bar when active editor changes
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor(() => updateStatusBar())
  );

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand("akf.stampFile", cmdStampFile),
    vscode.commands.registerCommand("akf.inspectFile", cmdInspectFile),
    vscode.commands.registerCommand("akf.toggleAutoStamp", cmdToggleAutoStamp)
  );

  // Check AKF CLI availability
  checkCliAvailable();
}

export function deactivate() {
  aiEditTracker.clear();
}

// ─── AI Edit Detection ──────────────────────────────────────────────

function onDocumentChange(event: vscode.TextDocumentChangeEvent) {
  if (event.document.uri.scheme !== "file") return;

  const config = vscode.workspace.getConfiguration("akf");
  const threshold = config.get<number>("aiInsertionThreshold", 80);

  for (const change of event.contentChanges) {
    const insertedLength = change.text.length;
    const deletedLength = change.rangeLength;

    // Heuristic: a large insertion with little/no deletion is likely AI
    if (insertedLength >= threshold && deletedLength < insertedLength * 0.2) {
      const key = event.document.uri.toString();
      const tracker = aiEditTracker.get(key) || { insertions: 0, totalChars: 0 };
      tracker.insertions += 1;
      tracker.totalChars += insertedLength;
      aiEditTracker.set(key, tracker);

      outputChannel.appendLine(
        `AI edit detected: +${insertedLength} chars in ${path.basename(event.document.fileName)}`
      );
    }
  }
}

// ─── Auto-Stamp on Save ─────────────────────────────────────────────

async function onDocumentSave(document: vscode.TextDocument) {
  if (document.uri.scheme !== "file") return;

  const config = vscode.workspace.getConfiguration("akf");
  if (!config.get<boolean>("autoStamp", true)) return;

  const key = document.uri.toString();
  const tracker = aiEditTracker.get(key);

  if (!tracker || tracker.insertions === 0) return;

  // Additional confidence: is a known AI extension active?
  const hasAiExtension = AI_EXTENSION_IDS.some((id) =>
    vscode.extensions.getExtension(id) !== undefined
  );

  // Only auto-stamp if we have AI edits AND an AI extension is present,
  // OR if the insertions are substantial (>3 events or >500 chars)
  const confident =
    hasAiExtension ||
    tracker.insertions >= 3 ||
    tracker.totalChars >= 500;

  if (!confident) {
    aiEditTracker.delete(key);
    return;
  }

  outputChannel.appendLine(
    `Stamping ${path.basename(document.fileName)}: ` +
    `${tracker.insertions} AI insertions, ${tracker.totalChars} chars`
  );

  // Reset tracker
  aiEditTracker.delete(key);

  // Stamp the file
  const classification = config.get<string>("classification", "internal");
  await stampFile(document.fileName, { aiGenerated: true, classification });
  updateStatusBar();
}

// ─── Commands ────────────────────────────────────────────────────────

async function cmdStampFile() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("No active file to stamp.");
    return;
  }

  const config = vscode.workspace.getConfiguration("akf");
  const classification = config.get<string>("classification", "internal");

  await stampFile(editor.document.fileName, { classification });
  updateStatusBar();
  vscode.window.showInformationMessage(
    `AKF: Stamped ${path.basename(editor.document.fileName)}`
  );
}

async function cmdInspectFile() {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showWarningMessage("No active file to inspect.");
    return;
  }

  try {
    const cli = getCliPath();
    const { stdout } = await execFileAsync(cli, [
      "extract",
      editor.document.fileName,
    ]);

    if (stdout.trim()) {
      outputChannel.appendLine(`\n── ${path.basename(editor.document.fileName)} ──`);
      outputChannel.appendLine(stdout);
      outputChannel.show();
    } else {
      vscode.window.showInformationMessage("No AKF metadata found in this file.");
    }
  } catch {
    vscode.window.showWarningMessage(
      "Could not inspect file. Is the akf CLI installed?"
    );
  }
}

async function cmdToggleAutoStamp() {
  const config = vscode.workspace.getConfiguration("akf");
  const current = config.get<boolean>("autoStamp", true);
  await config.update("autoStamp", !current, vscode.ConfigurationTarget.Global);
  vscode.window.showInformationMessage(
    `AKF auto-stamp: ${!current ? "enabled" : "disabled"}`
  );
  updateStatusBar();
}

// ─── AKF CLI Integration ────────────────────────────────────────────

function getCliPath(): string {
  return vscode.workspace.getConfiguration("akf").get<string>("cliPath", "akf");
}

interface StampOptions {
  aiGenerated?: boolean;
  classification?: string;
}

async function stampFile(
  filePath: string,
  options: StampOptions = {}
): Promise<boolean> {
  try {
    const cli = getCliPath();
    const args = ["stamp", filePath];

    if (options.classification) {
      args.push("--label", options.classification);
    }
    if (options.aiGenerated) {
      args.push("--ai");
    }

    await execFileAsync(cli, args, { timeout: 10_000 });
    outputChannel.appendLine(`Stamped: ${filePath}`);
    return true;
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    outputChannel.appendLine(`Stamp failed: ${filePath} — ${message}`);
    return false;
  }
}

async function checkCliAvailable() {
  try {
    const cli = getCliPath();
    await execFileAsync(cli, ["--version"]);
    outputChannel.appendLine("AKF CLI found");
  } catch {
    vscode.window.showWarningMessage(
      "AKF CLI not found. Install with: pip install akf"
    );
  }
}

// ─── Status Bar ──────────────────────────────────────────────────────

function updateStatusBar() {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.uri.scheme !== "file") {
    statusBarItem.hide();
    return;
  }

  const config = vscode.workspace.getConfiguration("akf");
  const autoStamp = config.get<boolean>("autoStamp", true);

  const key = editor.document.uri.toString();
  const tracker = aiEditTracker.get(key);

  if (tracker && tracker.insertions > 0) {
    statusBarItem.text = `$(shield) AKF: ${tracker.insertions} AI edits`;
    statusBarItem.tooltip = `${tracker.totalChars} chars from AI — will stamp on save`;
    statusBarItem.backgroundColor = new vscode.ThemeColor(
      "statusBarItem.warningBackground"
    );
  } else if (autoStamp) {
    statusBarItem.text = "$(shield) AKF";
    statusBarItem.tooltip = "AKF auto-stamp active";
    statusBarItem.backgroundColor = undefined;
  } else {
    statusBarItem.text = "$(shield) AKF (off)";
    statusBarItem.tooltip = "AKF auto-stamp disabled";
    statusBarItem.backgroundColor = undefined;
  }

  statusBarItem.show();
}
