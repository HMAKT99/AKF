# Contributing to AKF

Thank you for your interest in contributing to the Agent Knowledge Format project!

## Development Setup

### Python SDK

```bash
cd python
pip install -e ".[dev]"
pytest
```

### TypeScript SDK

```bash
cd typescript
npm install
npm test
```

## How to Contribute

### Reporting Bugs

Open a GitHub issue with:
- AKF version (`akf --version`)
- Python/Node.js version
- Minimal reproduction case
- Expected vs actual behavior

### Feature Requests

Open a GitHub issue with the "feature request" label. Include:
- Use case description
- Proposed API surface
- Example code showing how you'd use it

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/my-feature`)
3. Make your changes
4. Ensure all tests pass:
   ```bash
   cd python && pytest
   cd typescript && npm test
   ```
5. Add tests for new functionality
6. Submit a PR against `main`

### Code Standards

- **Python**: Follow existing patterns. Use type hints. Run `pytest` before submitting.
- **TypeScript**: Follow existing patterns. Use strict TypeScript. Run `npm test` before submitting.
- **Spec changes**: Any changes to `spec/` must maintain backward compatibility with existing .akf files.

### Areas for Contribution

- Framework integrations (LangChain, LlamaIndex, CrewAI, etc.)
- New file format handlers in `universal.py`
- Additional compliance regulation checks
- Documentation and examples
- IDE extensions

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
