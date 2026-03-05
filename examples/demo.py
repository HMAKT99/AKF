#!/usr/bin/env python3
"""
AKF Demo — Trust metadata for every file AI touches.

Run:  python examples/demo.py
"""

import json
import sys
import time

# ── Colors ──────────────────────────────────────────────────────
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
CYAN = "\033[36m"
RED = "\033[31m"
MAGENTA = "\033[35m"


def header(text: str) -> None:
    print(f"\n{BOLD}{CYAN}{'─' * 60}{RESET}")
    print(f"{BOLD}{CYAN}  {text}{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 60}{RESET}\n")


def step(n: int, text: str) -> None:
    print(f"  {BOLD}{BLUE}[{n}]{RESET} {text}")


def ok(text: str) -> None:
    print(f"      {GREEN}✓{RESET} {text}")


def warn(text: str) -> None:
    print(f"      {YELLOW}~{RESET} {text}")


def fail(text: str) -> None:
    print(f"      {RED}✗{RESET} {text}")


def code(text: str) -> None:
    print(f"      {DIM}{text}{RESET}")


def pause(seconds: float = 0.3) -> None:
    time.sleep(seconds)


def main() -> None:
    print(f"\n{BOLD}{MAGENTA}  ╔══════════════════════════════════════════╗{RESET}")
    print(f"{BOLD}{MAGENTA}  ║     AKF — Agent Knowledge Format         ║{RESET}")
    print(f"{BOLD}{MAGENTA}  ║     Trust metadata for the AI era         ║{RESET}")
    print(f"{BOLD}{MAGENTA}  ╚══════════════════════════════════════════╝{RESET}")

    # ── 1. Create ────────────────────────────────────────────────
    header("1. CREATE — Stamp trust metadata onto AI output")

    try:
        import akf
    except ImportError:
        print(f"  {RED}akf not installed. Run: pip install akf{RESET}")
        sys.exit(1)

    step(1, "Creating AKF unit with 3 claims...")
    pause()

    unit = (
        akf.AKFBuilder()
        .by("demo@akf.dev")
        .label("internal")
        .claim("Revenue was $4.2B, up 12% YoY", 0.98, source="SEC 10-Q", authority_tier=1, verified=True)
        .claim("Cloud segment grew 15-18%", 0.85, source="Gartner Report", authority_tier=2)
        .claim("H2 pipeline looks strong", 0.63, source="internal estimate", authority_tier=4, ai_generated=True)
        .build()
    )

    ok(f"Created unit with {len(unit.claims)} claims")
    ok(f"Classification: {unit.label}")
    ok(f"Author: {unit.by}")
    pause()

    step(2, "Trust scores computed automatically:")
    pause()

    for claim in unit.claims:
        result = akf.effective_trust(claim)
        symbol = "+" if result.decision == "ACCEPT" else ("~" if result.decision == "LOW" else "-")
        color = GREEN if result.decision == "ACCEPT" else (YELLOW if result.decision == "LOW" else RED)
        print(f"      {color}{symbol} {result.decision}{RESET} {result.score:.2f} — {claim.c}")
    pause()

    # ── 2. Save & Load ──────────────────────────────────────────
    header("2. FORMAT — Compact JSON, ~15 tokens per claim")

    step(3, "Compact format (wire-optimized):")
    compact = unit.model_dump(exclude_none=True, by_alias=True)
    compact_json = json.dumps(compact, separators=(",", ":"))
    print(f"\n      {DIM}{compact_json[:120]}...{RESET}\n")
    ok(f"Total size: {len(compact_json)} bytes")
    pause()

    step(4, "Saving to demo_output.akf...")
    unit.save("demo_output.akf")
    ok("Saved demo_output.akf")
    pause()

    step(5, "Loading back and validating...")
    loaded = akf.load("demo_output.akf")
    result = akf.validate("demo_output.akf")
    ok(f"Valid: {result.valid}, Level: {result.level}")
    ok(f"Claims loaded: {len(loaded.claims)}")
    pause()

    # ── 3. Audit ─────────────────────────────────────────────────
    header("3. AUDIT — Check compliance against regulations")

    step(6, "Running general compliance audit...")
    pause()
    audit_result = akf.audit("demo_output.akf")
    ok(f"Score: {audit_result.score:.2f}")
    ok(f"Compliant: {audit_result.compliant}")
    ok(f"Checks run: {len(audit_result.checks)}")
    pause()

    for check in audit_result.checks:
        if check.get("passed") or check.get("pass"):
            ok(f"{check.get('name', check.get('check', 'check'))}")
        else:
            warn(f"{check.get('name', check.get('check', 'check'))}: {check.get('recommendation', check.get('message', ''))}")
    pause()

    # ── 4. Security Detections ───────────────────────────────────
    header("4. DETECT — 10 enterprise security detection classes")

    step(7, "Running all 10 detection classes...")
    pause()

    report = akf.run_all_detections(unit)
    triggered = [f for f in report.findings if f.triggered]
    clean = [f for f in report.findings if not f.triggered]

    for finding in clean:
        ok(f"{finding.detection}: clean")
    for finding in triggered:
        warn(f"{finding.detection}: {finding.severity} — {finding.message}")

    pause()
    ok(f"Detections run: {len(report.findings)}")
    ok(f"Clean: {len(clean)}, Triggered: {len(triggered)}")

    # ── 5. Agent Consumption ─────────────────────────────────────
    header("5. CONSUME — Agent reads and transforms trust data")

    step(8, "Agent consuming with trust threshold 0.7...")
    pause()

    brief = (
        akf.AKFTransformer(unit)
        .filter(trust_min=0.7)
        .penalty(-0.03)
        .by("research-agent")
        .build()
    )

    ok(f"Claims above threshold: {len(brief.claims)} of {len(unit.claims)}")
    for claim in brief.claims:
        result = akf.effective_trust(claim)
        print(f"      {GREEN}+{RESET} {result.score:.2f} — {claim.c}")
    pause()

    # ── Summary ──────────────────────────────────────────────────
    header("Done!")

    print(f"  {BOLD}AKF attached trust metadata to AI content in 5 steps:{RESET}")
    print(f"  {GREEN}1.{RESET} Created claims with trust scores and provenance")
    print(f"  {GREEN}2.{RESET} Saved as compact JSON (~15 tokens/claim)")
    print(f"  {GREEN}3.{RESET} Audited for regulatory compliance")
    print(f"  {GREEN}4.{RESET} Ran 10 security detection classes")
    print(f"  {GREEN}5.{RESET} Agent consumed and filtered trusted claims")
    print()
    print(f"  {DIM}Learn more: https://github.com/HMAKT99/AKF{RESET}")
    print(f"  {DIM}Install:    pip install akf{RESET}")
    print()

    # Cleanup
    import os
    if os.path.exists("demo_output.akf"):
        os.remove("demo_output.akf")


if __name__ == "__main__":
    main()
