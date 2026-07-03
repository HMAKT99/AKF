# AKF — Agent Knowledge Format

Syntax highlighting, validation, and hover info for `.akf` files — the trust metadata format for AI-generated content.

AKF stamps travel with files your AI agents produce: who made them, what was verified (tests, review), and how much to trust them. This extension makes those stamps readable and checkable inside VS Code.

## Features

- **Syntax highlighting** for `.akf` files — trust scores, claims, provenance chains, classification labels
- **Hover info** on trust scores (ACCEPT / LOW / REJECT) and authority tiers (1–5)
- **AKF: Validate Current File** — checks structure, version, and claims against the spec
- **AKF: Inspect Claims** — lists all claims with trust scores in the Output panel

## Works with the AKF CLI

```bash
pip install akf
akf init          # wire stamping into git + your agents
akf check <file>  # OK / LOW / STALE / UNSTAMPED — before you build on a file
```

A stamp costs ~15 tokens; re-verifying costs 15,000. Agents stamp what they verify — the next agent (or you, in VS Code) checks the stamp instead of redoing the work.

## Links

- [AKF on GitHub](https://github.com/HMAKT99/AKF) — spec, CLI, SDKs (Python + TypeScript)
- [akf.dev](https://akf.dev)
- [MCP server](https://pypi.org/project/mcp-server-akf/) for Claude Desktop / Claude Code / Cursor

## Development

```bash
npm install && npm run compile   # build
npm run watch                    # recompile on changes
```

Press `F5` in VS Code to launch the Extension Development Host. Package with `npx @vscode/vsce package`.

MIT licensed.
