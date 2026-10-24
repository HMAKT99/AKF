# mcp-server-akf

mcp-name: io.github.HMAKT99/akf

MCP (Model Context Protocol) server that exposes 10 AKF tools to AI agents.
Any MCP-compatible client (Claude Desktop, Claude Code, Cursor, Windsurf, etc.)
can check, stamp, validate, audit, and scan files using the Agent Knowledge Format.

**A stamp costs ~15 tokens. Re-verifying costs 15,000.** Agents stamp what they
verify; the next agent calls `check_file` and builds on it instead of redoing
the work.

## Installation

```bash
pip install mcp-server-akf
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
| `check_file` | One-line trust check — can an agent build on this file without re-verifying? (OK / LOW / STALE / UNSTAMPED) |
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

## Verification state in tool results (experimental)

On mcp 2.x, a tool result for a file (any tool called with `path`) carries that file's verification state in `_meta` under the vendor key `dev.akf/trust`:

```json
"_meta": {
  "dev.akf/trust": {
    "v": "1",
    "status": "OK",
    "trust": 0.7447,
    "evidence": ["human_review"],
    "agent": "claude-code",
    "age_days": 4
  }
}
```

`status` is computed live (`OK` / `LOW` / `STALE` / `UNSTAMPED`), so a client sees whether the file changed since it was verified. The key is absent when the result isn't about a file. Clients that don't know the key ignore it.

To annotate your own server's results:

```python
from mcp_server_akf.meta import TRUST_META_KEY, trust_meta

meta = trust_meta(path)
return CallToolResult(content=[...], _meta={TRUST_META_KEY: meta} if meta else None)
```

To read it in a client:

```python
result = await client.call_tool("extract_file", {"path": "report.md"})
state = (result.meta or {}).get("dev.akf/trust")
if state and state["status"] == "OK":
    ...  # verified and unchanged: build on it without re-verifying
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
