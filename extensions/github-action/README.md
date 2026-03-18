---
_akf: '{"v":"1.0","claims":[{"c":"Trust metadata for extensions/github-action/README.md","t":0.7,"id":"3ea3cece","src":"unspecified","tier":5,"ver":false,"ai":true,"evidence":[{"type":"other","detail":"docs updated for certify","at":"2026-03-18T03:47:35.564713+00:00"}]}],"id":"akf-b1df9959a92e","agent":"claude-code","at":"2026-03-18T03:47:35.564913+00:00","label":"public","inherit":true,"ext":false,"sv":"1.1"}'
---
# AKF Certify — GitHub Action

Trust-gated merges for your repository. Runs `akf certify` on your files and posts certification results as PR comments.

## Usage

```yaml
- uses: HMAKT99/AKF/extensions/github-action@main
  with:
    paths: "."                    # file or directory (default: .)
    min-trust: "0.7"              # minimum trust score (default: 0.7)
    fail-on-untrusted: true       # fail workflow on certification failure
    format: "markdown"            # output format: summary, json, markdown
    post-comment: true            # post results as PR comment
```

## Examples

### Basic — certify all AKF-enriched files

```yaml
name: AKF Certify
on: [pull_request]

jobs:
  certify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: HMAKT99/AKF/extensions/github-action@main
```

### With test evidence

```yaml
name: AKF Certify with Evidence
on: [pull_request]

jobs:
  test-and-certify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run tests
        run: pytest --junitxml=results.xml

      - uses: HMAKT99/AKF/extensions/github-action@main
        with:
          evidence-file: "results.xml"
          min-trust: "0.8"
```

### Strict mode — block merge on failure

```yaml
name: Trust Gate
on: [pull_request]

jobs:
  trust-gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: HMAKT99/AKF/extensions/github-action@main
        with:
          fail-on-untrusted: true
          min-trust: "0.7"
```

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `paths` | `.` | File or directory to certify |
| `min-trust` | `0.7` | Minimum trust score (0.0–1.0) |
| `fail-on-untrusted` | `true` | Exit with failure if any file is not certified |
| `evidence-file` | | Path to JUnit XML or JSON evidence file |
| `format` | `markdown` | Output format: `summary`, `json`, `markdown` |
| `python-version` | `3.11` | Python version for setup |
| `post-comment` | `true` | Post results as a PR comment |

## What it checks

`akf certify` aggregates three engines into a single pass/fail verdict:

- **Trust scoring** — average trust across all claims must meet the threshold
- **Detection** — zero critical detections (hallucination risk, knowledge laundering, etc.)
- **Compliance** — EU AI Act, SOX, NIST compliance checks

Files without AKF metadata are skipped (not failed).

## PR comments

When `post-comment: true` (default), the action posts a Markdown table to the PR showing per-file certification status. The comment is updated on subsequent pushes rather than creating duplicates.
