# AKF Quickstart

Get up and running with AKF in 5 minutes.

## Install

```bash
pip install akf
```

## 1. Create Your First .akf File

```python
import akf

unit = akf.create("Revenue was $4.2B, up 12% YoY", t=0.98, src="SEC 10-Q", tier=1)
unit.save("report.akf")
```

## 2. Validate It

```python
result = akf.validate("report.akf")
print(result.valid)   # True
print(result.level)   # 2 (Practical)
```

## 3. Compute Trust Scores

```python
unit = akf.load("report.akf")
for claim in unit.claims:
    result = akf.effective_trust(claim)
    print(f"{result.decision}: {result.score:.2f} — {claim.c}")
```

## 4. Build Multi-Claim Units

```python
unit = (akf.AKFBuilder()
    .by("sarah@company.com")
    .label("confidential")
    .claim("Revenue $4.2B", 0.98, src="SEC 10-Q", tier=1, ver=True)
    .claim("Cloud growth 15-18%", 0.85, src="Gartner", tier=2)
    .claim("Pipeline strong", 0.72, src="estimate", tier=4)
    .build())
```

## 5. Transform (Agent Consumption)

```python
brief = (akf.AKFTransformer(unit)
    .filter(trust_min=0.5)
    .penalty(-0.03)
    .by("research-agent")
    .build())
brief.save("weekly-brief.akf")
```

## CLI

```bash
akf create report.akf --claim "Revenue $4.2B" --trust 0.98 --src "SEC 10-Q"
akf validate report.akf
akf inspect report.akf
akf trust report.akf
akf consume report.akf --output brief.akf --threshold 0.6 --agent my-agent
akf provenance report.akf
```
