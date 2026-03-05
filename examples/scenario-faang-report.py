"""
AKF Demo: AI-Generated Financial Report at a FAANG Company
Complete lifecycle: create -> review -> trust -> compact -> derive -> security -> freshness
"""
import os
import sys
import tempfile

# Run from tempdir to avoid polluting the project
workdir = tempfile.mkdtemp(prefix="akf_demo_")
os.chdir(workdir)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
import akf

# --- Step 1: AI agent creates the report ---
unit = akf.create_multi(
    [
        {
            "content": "Q3 revenue projected at $42.1B, up 12% YoY",
            "confidence": 0.82,
            "source": "internal-erp",
            "uri": "https://erp.internal/reports/q3-2026",
            "ai_generated": True,
            "risk": "Projection based on 2 months actuals + 1 month forecast",
            "tags": ["revenue", "forecast", "q3-2026"],
            "expires_at": "2026-09-30T23:59:59Z",
        },
        {
            "content": "APAC region underperforming target by 8%",
            "confidence": 0.91,
            "source": "internal-erp",
            "ai_generated": True,
            "authority_tier": 1,
            "tags": ["apac", "underperformance"],
        },
    ],
    author="finance-agent@corp.ai",
    classification="confidential",
)

# Add origin with generation params to claims
unit.claims[0].origin = akf.Origin(
    type="ai", model="gpt-4o", provider="openai",
    generation=akf.GenerationParams(
        temperature=0.3,
        tokens_input=12400,
        tokens_output=847,
        cost_usd=0.004,
        tools_used=["erp_query", "time_series_forecast"],
        prompt_hash="sha256:e8f2a1b3...",
    ),
)
unit.claims[0].reasoning = akf.ReasoningChain(
    steps=[
        "Pulled monthly revenue from ERP for Jan-Aug 2026",
        "Applied seasonal adjustment from prior 3 years",
        "Weighted recent growth trajectory at 60%, historical at 40%",
        "Cross-referenced with sales pipeline data",
    ],
    conclusion="12% YoY growth supported by pipeline strength and seasonal patterns",
)
unit.claims[0].evidence = [
    akf.Evidence(type="test_pass", detail="Back-tested against Q1/Q2 actuals within 3% margin")
]
unit.claims[1].origin = akf.Origin(type="ai", model="gpt-4o")

unit.save("report-q3.akf", compact=False)
print("Step 1: Created report-q3.akf")

# --- Step 2: Human analyst reviews ---
unit = akf.load("report-q3.akf")
unit.claims[0].verified = True
unit.claims[0].verified_by = "jane.doe@corp.com"
unit.claims[0].reviews = [
    akf.Review(reviewer="jane.doe@corp.com", verdict="approved",
               comment="Verified against ERP actuals")
]
unit.claims[1].reviews = [
    akf.Review(reviewer="jane.doe@corp.com", verdict="needs_changes",
               comment="Missing context on currency headwinds")
]
akf.save(unit, "report-q3.akf", compact=False)
print("Step 2: Reviews added")

# --- Step 3: Save compact version ---
unit.save("report-q3-compact.akf", compact=True)
full_size = os.path.getsize("report-q3.akf")
compact_size = os.path.getsize("report-q3-compact.akf")
print(f"Step 3: Compact: {compact_size}B vs {full_size}B ({100*(full_size-compact_size)/full_size:.0f}% smaller)")

# --- Step 4: Trust computation ---
results = akf.compute_all(unit)
for claim, result in zip(unit.claims, results):
    preview = claim.content[:50]
    print(f"Step 4: Trust [{result.decision}] {result.score:.4f}  \"{preview}\"")

# --- Step 5: Downstream agent derives board deck ---
source = akf.load("report-q3.akf")
deck = akf.derive(
    parent=source,
    agent_id="deck-agent@corp.ai",
    claims=[
        {"content": "Revenue on track at $42.1B with 12% growth",
         "confidence": 0.78},
    ],
)
deck.save("board-deck.akf", compact=False)
print("Step 5: Derived board-deck.akf from report-q3.akf")

# --- Step 6: Security report ---
report = akf.full_report(unit)
print(f"Step 6: Security Score: {report.score:.1f}/10 ({report.grade})")
print(f"         Classification: {report.classification}")
print(f"         Reviews: {report.reviewed_claims}/{report.total_claims}")
print(f"         External sharing: {'ALLOWED' if report.can_share_external else 'BLOCKED'}")

# --- Step 7: Freshness check ---
for claim in unit.claims:
    status = akf.freshness_status(claim)
    preview = claim.content[:50]
    print(f"Step 7: Freshness [{status:10s}] \"{preview}\"")

# --- Step 8: Explain trust ---
explanation = akf.explain_trust(unit.claims[0])
print(f"\nStep 8: Trust explanation for claim 1:\n{explanation}")

print(f"\nDemo complete. Files in: {workdir}")
print("  report-q3.akf")
print("  report-q3-compact.akf")
print("  board-deck.akf")
