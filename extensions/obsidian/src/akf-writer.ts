import { App, TFile } from "obsidian";
import type { AKFUnit } from "akf-format";
import { toJSON } from "akf-format";

/**
 * Write AKF metadata into a markdown file's YAML frontmatter.
 */
export async function writeAKFToFile(
  app: App,
  file: TFile,
  unit: AKFUnit,
  frontmatterKey: string
): Promise<void> {
  const compactJson = toJSON(unit);

  await app.vault.process(file, (content) => {
    // Check if frontmatter exists
    if (content.startsWith("---\n")) {
      const endIdx = content.indexOf("\n---", 4);
      if (endIdx > 0) {
        const frontmatter = content.slice(4, endIdx);
        const rest = content.slice(endIdx + 4);
        // Remove existing akf/_akf lines
        const lines = frontmatter
          .split("\n")
          .filter((l) => !l.startsWith("akf:") && !l.startsWith("_akf:"));
        lines.push(`${frontmatterKey}: '${compactJson}'`);
        return `---\n${lines.join("\n")}\n---${rest}`;
      }
    }
    // No frontmatter — prepend it
    return `---\n${frontmatterKey}: '${compactJson}'\n---\n${content}`;
  });
}

/**
 * Remove AKF metadata from a markdown file's frontmatter.
 */
export async function removeAKFFromFile(
  app: App,
  file: TFile
): Promise<boolean> {
  let removed = false;

  await app.vault.process(file, (content) => {
    if (!content.startsWith("---\n")) return content;

    const endIdx = content.indexOf("\n---", 4);
    if (endIdx <= 0) return content;

    const frontmatter = content.slice(4, endIdx);
    const rest = content.slice(endIdx + 4);
    const lines = frontmatter.split("\n");
    const filtered = lines.filter((l) => !l.startsWith("akf:") && !l.startsWith("_akf:"));

    if (filtered.length < lines.length) {
      removed = true;
      if (filtered.every((l) => l.trim() === "")) {
        // Frontmatter is now empty — remove it entirely
        return rest.startsWith("\n") ? rest.slice(1) : rest;
      }
      return `---\n${filtered.join("\n")}\n---${rest}`;
    }
    return content;
  });

  return removed;
}
