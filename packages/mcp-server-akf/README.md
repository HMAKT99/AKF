# mcp-server-akf

MCP (Model Context Protocol) server that exposes 9 AKF tools to AI agents.
Any MCP-compatible client (Claude Desktop, Cursor, Windsurf, etc.) can stamp,
validate, audit, and scan files using the Agent Knowledge Format.

## Installation

```bash
pip install ./packages/mcp-server-akf
```

## Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "akf": {
      "command": "python",
      "args": ["-m", "mcp_server_akf"]
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "akf": {
      "command": "python",
      "args": ["-m", "mcp_server_akf"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `create_claim` | Create an AKF claim with trust metadata |
| `validate_file` | Validate an `.akf` file against the spec |
| `scan_file` | Security scan any file for AKF metadata |
| `trust_score` | Compute effective trust score for a claim |
| `stamp_file` | Stamp trust metadata onto any file (20+ formats) |
| `audit_file` | Compliance audit (EU AI Act, SOX, HIPAA, GDPR, NIST, ISO 42001) |
| `embed_file` | Embed AKF metadata into DOCX, PDF, HTML, images, etc. |
| `extract_file` | Extract AKF metadata from any supported format |
| `detect_threats` | Run 10 AI-specific security detections |

## Quick usage

Once configured, ask your AI agent:

> "Stamp `report.docx` with AKF trust metadata, confidence 0.9, evidence 'quarterly review complete'"

The agent will call `stamp_file` through MCP and attach provenance automatically.

You can also run the server directly for testing:

```bash
python -m mcp_server_akf
```

## Multi-Agent Support

The MCP server works seamlessly with multi-agent orchestration platforms:

- **Agent Identity**: Create and verify agent cards via `akf agent create` / `akf agent verify`
- **A2A Protocol**: Export/import agent cards for cross-platform discovery via `akf agent export-a2a`
- **Team Certification**: Use `akf certify --team` for per-agent trust breakdowns in CI
- **Delegation**: Trust ceilings cap delegate output when agents hand off work
- **Team Streaming**: Multi-agent sessions with per-agent claim attribution

Supports: Claude Agent Teams, Copilot Cowork, Codex multi-agent, and any A2A-compatible platform.

## Requirements

- Python >= 3.10
- `akf >= 1.0.0`
- `mcp >= 1.0.0`
