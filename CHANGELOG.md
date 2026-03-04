# Changelog

## [1.0.0] - 2026-03-04

### Added

#### Core
- AKF data model with claims, provenance, and classification
- Trust computation engine with authority tiers, temporal decay, and penalties
- Provenance chain tracking with SHA-256 integrity hashing
- Security classification hierarchy (public through restricted)
- Builder pattern for fluent AKF construction
- Transformer pattern for filtering and deriving units
- Preset templates for common document types
- Descriptive field names with backward-compatible compact aliases

#### Python SDK
- `akf.create()` and `akf.loads()` with secure defaults
- `akf.agent` module: consume, derive, generation_prompt, validate_output, response_schema, from_tool_call, to_context, detect
- `akf.compliance` module: audit, check_regulation (EU AI Act, SOX, HIPAA, GDPR, NIST AI), audit_trail, verify_human_oversight
- `akf.view` module: show, to_html, to_markdown, executive_summary
- `akf.data` module: load_dataset, quality_report, merge, filter_claims
- `akf.knowledge_base` module: KnowledgeBase class for persistent claim storage
- `akf.trust`: TrustLevel enum, explain_trust() human-readable breakdowns
- `akf.security`: security_score(), purview_signals(), detect_laundering()
- `akf.presets`: 9 built-in templates, register() for custom templates
- Universal format layer: embed/extract AKF into 12+ file formats
- CLI with create, validate, inspect, trust, consume, audit, kb, and more

#### TypeScript SDK
- Full AKF model with Zod validation
- Core create/load/validate functions
- Trust computation, provenance, security, transform modules
- Builder pattern

#### Specification
- AKF v1.0 specification document
- JSON Schema for validation
- Example .akf files
- LLM integration guide

#### Infrastructure
- Comprehensive test suite (497+ Python tests, TypeScript tests)
- CI/CD workflow
- Contributing guide and Code of Conduct
