# Purview Integration

How Microsoft Purview can scan and protect .akf files.

## Field Mapping

| AKF Field | Purview Capability | Action |
|-----------|-------------------|--------|
| `label` | Sensitivity labels | Auto-apply or validate classification |
| `inherit` | Label inheritance | Enforce on derived documents |
| `ext` | DLP policies | Block external sharing when false |
| `ai` (on claims) | AI content detection | Flag AI-generated content |
| `risk` | Risk assessment | Surface risk descriptions |
| `t` (trust scores) | Confidence monitoring | Alert on low-confidence claims |
| `prov` | Audit trail | eDiscovery chain of custody |
| `hash` | Integrity verification | Detect tampering |

## Sample DLP Policies

### Block External Sharing of Confidential AI Content

```
Rule: Block AKF External Share
Condition:
  - File type: .akf (application/vnd.akf+json)
  - label IN ("confidential", "highly-confidential", "restricted")
  - ext = false OR ext not present
Action:
  - Block sharing to external recipients
  - Notify sender with policy tip
  - Log to compliance dashboard
```

### Flag High-Risk AI Claims

```
Rule: Flag AI Inference Claims
Condition:
  - File type: .akf
  - Any claim where ai = true AND tier >= 4
Action:
  - Add warning banner: "Contains AI-generated inferences"
  - Require human review before distribution
  - Log AI claim count and risk descriptions
```

### Alert on Low Trust Content

```
Rule: Low Trust Alert
Condition:
  - File type: .akf
  - Average trust score < 0.6 across all claims
Action:
  - Add "Low Confidence" indicator
  - Require additional verification before use in decisions
```

## eDiscovery Queries

### Find All AI-Generated Claims

```kql
ContentType:akf AND claims.ai:true
```

### Find Confidential Documents with Provenance

```kql
ContentType:akf AND label:confidential AND prov.hop:*
```

### Find Claims Above Trust Threshold

```kql
ContentType:akf AND claims.t:>0.8 AND claims.tier:<=2
```

### Trace Provenance Chain

```kql
ContentType:akf AND prov.by:"copilot-m365" AND prov.do:"enriched"
```

## Integration Architecture

```
.akf file created
    ↓
Purview Scanner
    ├── Read label → Apply sensitivity label
    ├── Check ext → Enforce DLP policy
    ├── Scan claims.ai → Flag AI content
    ├── Read prov → Index audit trail
    └── Verify hash → Integrity check
    ↓
Compliance Dashboard
    ├── Classification distribution
    ├── AI content prevalence
    ├── Trust score trends
    └── Provenance depth metrics
```
