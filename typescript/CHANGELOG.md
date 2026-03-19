# Changelog

All notable changes to `akf-format` will be documented in this file.

This project follows [semantic versioning](https://semver.org/).

## [1.2.1] — 2026-03-19

### Fixed
- Fixed `akf doctor` showing hardcoded version instead of actual version
- Aligned Markdown and PDF report titles to "AKF Trust Report"
- Fixed npm README API examples to match actual SDK exports

### Added
- README.md with full API documentation, upgrade guidance, and release notifications
- CHANGELOG.md tracking all releases
- Package metadata: repository, homepage, bugs URLs

## [1.2.0] — 2026-03-19

### Added
- Professional HTML report rendering with executive dashboard
- Structured terminal output for scan and audit commands
- `--output` flag for exporting reports (HTML, JSON, CSV, Markdown, PDF)
- `--open` flag to open exported reports in browser
- Automated npm publishing via GitHub Actions

### Changed
- Version bump from 1.1.0 to 1.2.0

## [1.1.0] — 2026-03-18

### Added
- Multi-agent orchestration support (delegation, team streaming, agent cards)
- Agent identity and A2A protocol bridge
- Team certification with per-agent trust breakdown
- 6 new multi-agent features for the AI orchestration era

## [1.0.0] — 2026-03-17

### Added
- Initial release of `akf-format` TypeScript SDK
- Core models: Claim, KnowledgeUnit, Provenance
- Compact and descriptive field name support
- Validation against AKF v1.1 schema
- Trust score computation
- Compliance checking (EU AI Act, SOX, HIPAA, GDPR, NIST AI, ISO 42001)
- Security detection classes
- File I/O: read/write `.akf` files
- Builder pattern for creating claims and knowledge units
- Stream support for real-time trust metadata
