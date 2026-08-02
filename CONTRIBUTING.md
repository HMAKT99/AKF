# Contributing to AKF

Thank you for your interest in contributing to the Agent Knowledge Format project!

## Prerequisites

- Python 3.9+
- Node.js 18+
- git

## Development Setup

```bash
git clone https://github.com/HMAKT99/AKF.git
cd AKF

# Python SDK
cd python && pip install -e ".[dev]" && cd ..

# TypeScript SDK
cd typescript && npm install && cd ..

# Website
cd site && npm install && cd ..
```

## Project Structure

| Directory | Description |
|-----------|-------------|
| `python/akf/` | Python SDK |
| `typescript/src/` | TypeScript SDK |
| `site/` | Website (Vite + React + Tailwind) |
| `spec/` | Format specification and JSON schema |
| `packages/` | Framework integrations (MCP, LangChain, LlamaIndex, CrewAI) |
| `extensions/` | VS Code, GitHub Action, Office, Google Workspace |
| `skills/` | Agent skill files |

## Running Tests

```bash
# Python
cd python && python -m pytest tests/ -v

# TypeScript
cd typescript && npm test

# Website (build check)
cd site && npm run build
```

## PR Process

1. Create a feature branch (`git checkout -b feature/my-feature`)
2. Make your changes
3. Run all relevant tests (see above)
4. Add tests for new functionality
5. Open a PR against `main`

**Adding or changing a format field?** The models are not the source of truth for the *standard* — the schema is. Any new field on `Claim`, `Evidence`, the envelope, or a new sub-model must also be added to `spec/akf-v1.1.schema.json` and documented in `spec/akf-v1.0-spec.md`. `tests/test_schema_conformance.py` enforces this: it stamps a maximal unit and validates it against the schema, so a field that exists in code but not in the schema fails CI.

## Reporting Bugs

Open a GitHub issue with:
- AKF version (`akf --version`)
- Python/Node.js version
- Minimal reproduction case
- Expected vs actual behavior

## Feature Requests

Open a GitHub issue with the "feature request" label. Include:
- Use case description
- Proposed API surface
- Example code showing how you'd use it

## Code Style

- Follow existing patterns in the codebase. No unnecessary abstractions.
- **Python**: Use type hints. Run `pytest` before submitting.
- **TypeScript**: Use strict TypeScript. Run `npm test` before submitting.
- **Spec changes**: Must maintain backward compatibility with existing `.akf` files.

## Areas for Contribution

- Framework integrations (LangChain, LlamaIndex, CrewAI, etc.)
- New file format handlers in `universal.py` (video, audio, and beyond)
- Additional compliance regulation checks
- Documentation and examples
- IDE extensions
- Multi-agent features: delegation policies, team streaming, A2A protocol bridge
- Agent identity: AgentCard registry, cross-platform discovery

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
