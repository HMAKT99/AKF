<p align="center">
  <img src="https://img.shields.io/npm/v/akf-format?style=flat-square&label=npm" />
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" />
  <img src="https://img.shields.io/badge/format-.akf-blue?style=flat-square" />
</p>

# AKF — Agent Knowledge Format (TypeScript SDK)

**The trust metadata standard for AI-generated content.** AKF is to AI output what EXIF is to photos — trust scores, source provenance, and security classification in ~15 tokens of JSON.

## Install

```bash
npm install akf-format
```

## Staying Up to Date

AKF is actively developed. To get the latest features and fixes:

```bash
# Check your current version
npm list akf-format

# Update to the latest version
npm update akf-format

# Or install a specific version
npm install akf-format@latest
```

**Tip:** If your `package.json` has `"akf-format": "^1.0.0"`, running `npm update` will automatically pull the latest 1.x release. We follow [semantic versioning](https://semver.org/) — patch and minor updates are always backward-compatible.

### Release notifications

- **GitHub Releases** — Watch the [AKF repo](https://github.com/HMAKT99/AKF) and select "Releases only" to get notified of every new version
- **npm** — Run `npm outdated` in your project to check for available updates
- **Automated** — Use [Renovate](https://github.com/renovatebot/renovate) or [Dependabot](https://docs.github.com/en/code-security/dependabot) to get automatic PRs when new versions are published

## Quick Start

```typescript
import { create, createMulti, validate, effectiveTrust } from 'akf-format';

// Create a single trust-stamped claim
const unit = create('Revenue was $4.2B, up 12% YoY', 0.98, {
  src: 'SEC 10-Q filing',
  tier: 1,
  ver: true,
});

// Validate against the AKF schema
const result = validate(unit);
console.log(result.valid); // true

// Compute effective trust score
const trust = effectiveTrust(unit.claims[0]);
console.log(trust.score);    // 0.98
console.log(trust.decision); // "ACCEPT"
```

## Core API

### Single Claim

```typescript
import { create } from 'akf-format';

// create(content, confidence, options?)
const unit = create('Customer satisfaction increased 15%', 0.85, {
  src: 'Q1 Survey Results',
  tier: 2,
});
```

### Multiple Claims

```typescript
import { createMulti } from 'akf-format';

// createMulti(claims[], envelope?)
const unit = createMulti(
  [
    { c: 'Revenue was $4.2B', t: 0.98, src: 'SEC 10-Q', tier: 1, ver: true },
    { c: 'H2 will accelerate', t: 0.63, tier: 5, ai: true },
  ],
  { by: 'analyst@acme.com', label: 'confidential' }
);
```

### Builder Pattern

```typescript
import { AKFBuilder } from 'akf-format';

const unit = new AKFBuilder()
  .by('analyst@acme.com')
  .agent('claude-code')
  .model('claude-sonnet-4-20250514')
  .label('confidential')
  .claim('Revenue was $4.2B', 0.98, { src: 'SEC 10-Q', tier: 1 })
    .kind('financial_data')
    .evidence({ type: 'test_pass', detail: '42/42 passed' })
    .tag('finance', 'q1')
  .claim('H2 outlook positive', 0.63)
  .build();
// Auto-generates: provenance, integrity hash, timestamps
```

### Validation

```typescript
import { validate } from 'akf-format';

const result = validate(unit);
if (!result.valid) {
  console.error(result.errors);
}
console.log(result.level); // 0=invalid, 1=minimal, 2=practical, 3=full
```

### Trust Scoring

```typescript
import { effectiveTrust, AUTHORITY_WEIGHTS } from 'akf-format';

const trust = effectiveTrust(claim);
console.log(trust.score);     // 0.0 – 1.0
console.log(trust.decision);  // "ACCEPT" | "LOW" | "REJECT"
console.log(trust.breakdown); // { confidence, authority, tier, decay, penalty }

// Authority weights by tier:
// Tier 1: 1.00 (SEC filings)  Tier 3: 0.70 (news)  Tier 5: 0.30 (AI inference)
```

### Compliance Audit

```typescript
import { audit } from 'akf-format';

// Supports: eu_ai_act, sox, hipaa, gdpr, nist_ai, iso_42001
const result = audit(unit, 'eu_ai_act');
console.log(result.compliant); // true/false
console.log(result.findings);  // detailed findings
```

### Security Detections

```typescript
import { runAllDetections } from 'akf-format';

// 10 detection classes: AI without review, trust below threshold,
// hallucination risk, knowledge laundering, classification downgrade,
// stale claims, ungrounded claims, trust degradation, excessive AI, provenance gap
const report = runAllDetections(unit);
```

### Provenance

```typescript
import { addHop, formatTree } from 'akf-format';

const reviewed = addHop(unit, { by: 'reviewer@acme.com', do: 'reviewed' });
console.log(formatTree(reviewed)); // visual provenance tree
```

### File I/O

```typescript
import { stampFile, read, scan, embed, extract } from 'akf-format';

// Write .akf files
stampFile('report.akf', unit);

// Read .akf files
const loaded = read('report.akf');

// Scan for security issues
const scanResult = scan('report.akf');

// Embed into Markdown (frontmatter)
embed('report.md', unit);

// Extract metadata from any supported format
const meta = extract('report.md');
```

### JSON Serialization

```typescript
import { toJSON, fromJSON } from 'akf-format';

const json = toJSON(unit);       // compact JSON string
const parsed = fromJSON(json);   // back to AKFUnit
```

### Normalize (Compact / Descriptive)

```typescript
import { toDescriptive, normalizeUnit } from 'akf-format';

// Compact (c, t, src) → Descriptive (content, confidence, source)
const descriptive = toDescriptive(unit);
console.log(descriptive.claims[0].content);    // "Revenue was $4.2B"
console.log(descriptive.claims[0].confidence); // 0.98
```

### Security Labels

```typescript
import { labelRank, canShareExternal, inheritLabel } from 'akf-format';

labelRank('confidential') > labelRank('public'); // true
canShareExternal('public');     // true
canShareExternal('restricted'); // false
```

## Format

AKF metadata is ~15 tokens of JSON:

```json
{
  "v": "1.0",
  "claims": [
    { "c": "Revenue was $4.2B", "t": 0.98, "src": "SEC 10-Q", "tier": 1, "ver": true }
  ]
}
```

Both compact (`c`, `t`, `src`) and descriptive (`content`, `confidence`, `source`) field names are supported.

## Versioning

This package follows [semantic versioning](https://semver.org/):

- **Patch** (1.2.x) — Bug fixes, no API changes
- **Minor** (1.x.0) — New features, backward-compatible
- **Major** (x.0.0) — Breaking changes (we'll provide a migration guide)

See [CHANGELOG.md](https://github.com/HMAKT99/AKF/blob/main/typescript/CHANGELOG.md) for what's new in each release.

## Full Documentation

- [AKF Specification](https://github.com/HMAKT99/AKF/blob/main/spec/akf-v1.0-spec.md)
- [JSON Schema](https://github.com/HMAKT99/AKF/blob/main/spec/akf-v1.1.schema.json)
- [Python SDK](https://github.com/HMAKT99/AKF) (`pip install akf`)
- [Website](https://akf.dev)

## License

MIT
