"""AKF v1.1 — Command-line interface."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click

from .core import create, create_multi, load, validate
from .models import AKF, Claim
from .provenance import add_hop, format_tree
from .trust import compute_all, effective_trust


@click.group(invoke_without_command=True)
@click.version_option(version="1.2.5", prog_name="akf")
@click.pass_context
def main(ctx) -> None:
    """AKF — Agent Knowledge Format CLI."""
    if ctx.invoked_subcommand is None:
        click.secho("AKF — Agent Knowledge Format v1.1", bold=True)
        click.echo()
        click.echo("The trust metadata standard for every file AI touches.")
        click.echo()
        click.echo("Quick start:")
        click.echo("  akf create out.akf -c 'Revenue $4.2B' -t 0.98 --src SEC")
        click.echo("  akf validate out.akf")
        click.echo("  akf inspect out.akf")
        click.echo("  akf trust out.akf")
        click.echo("  akf audit out.akf")
        click.echo()
        click.echo("Run 'akf --help' for all commands or 'akf create --demo' for a walkthrough.")


@main.command("init")
@click.option("--git-hooks", is_flag=True, help="Install post-commit hook for akf stamp-commit")
@click.option("--agent", help="Default AI agent ID")
@click.option("--label", "classification", default="internal", help="Default classification")
@click.option("--path", "target", default=".", type=click.Path(), help="Project root")
def init_cmd(git_hooks, agent, classification, target) -> None:
    """Initialize AKF in a project directory."""
    root = Path(target).resolve()
    akf_dir = root / ".akf"
    akf_dir.mkdir(exist_ok=True)

    config = {
        "version": "1.0",
        "classification": classification,
        "auto_embed": True,
    }
    if agent:
        config["agent"] = agent

    config_path = akf_dir / "config.json"
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    click.secho(f"Created {config_path}", fg="green")

    if git_hooks:
        hooks_dir = root / ".git" / "hooks"
        if not hooks_dir.parent.exists():
            click.secho("Warning: .git directory not found, skipping hooks", fg="yellow")
        else:
            hooks_dir.mkdir(exist_ok=True)
            hook = hooks_dir / "post-commit"
            hook.write_text("#!/bin/sh\nakf stamp-commit\n")
            hook.chmod(0o755)
            click.secho(f"Installed post-commit hook: {hook}", fg="green")

    click.echo()
    click.secho("AKF initialized!", bold=True)
    click.echo("  Config:  .akf/config.json")
    click.echo()
    click.echo("Quick start:")
    click.echo("  akf embed report.docx         # add trust metadata")
    click.echo("  akf read report.docx           # view trust metadata")
    click.echo("  akf audit report.docx          # compliance check")


@main.command("read")
@click.argument("file", type=click.Path(exists=True))
@click.option("--json", "as_json", is_flag=True, help="Output raw JSON")
def read_cmd(file, as_json) -> None:
    """Read and display AKF trust metadata from any file."""
    from . import universal as akf_u

    meta = akf_u.extract(file)
    if meta is None:
        click.secho(f"No AKF metadata found in {file}", fg="yellow")
        click.echo(f"  Tip: Run 'akf embed {file}' to add metadata")
        return

    if as_json:
        click.echo(json.dumps(meta, indent=2, ensure_ascii=False))
        return

    # Header
    click.secho(f"AKF Trust Metadata: {file}", bold=True)
    if meta.get("classification"):
        click.echo(f"  Classification: {meta['classification']}")

    # Claims
    claims = meta.get("claims", [])
    if claims:
        click.echo(f"  Claims: {len(claims)}")
        click.echo()
        for claim in claims:
            conf = claim.get("confidence", claim.get("t", 0))
            content = claim.get("content", claim.get("c", ""))
            source = claim.get("source", claim.get("src", ""))

            if conf >= 0.8:
                color = "green"
                icon = "\U0001f7e2"
            elif conf >= 0.5:
                color = "yellow"
                icon = "\U0001f7e1"
            else:
                color = "red"
                icon = "\U0001f534"

            parts = [f'{icon} {conf:.2f}  "{content}"']
            if source:
                parts.append(source)
            if claim.get("verified"):
                parts.append(click.style("verified", fg="green"))
            if claim.get("ai_generated") or claim.get("ai"):
                parts.append(click.style("\u26a0 AI", fg="yellow"))
            click.echo("  " + "  ".join(parts))
    else:
        click.echo("  No claims found")

    # Provenance
    prov = meta.get("provenance", [])
    if prov:
        click.echo()
        click.secho("  Provenance:", bold=True)
        for hop in prov:
            actor = hop.get("actor", hop.get("by", "unknown"))
            action = hop.get("action", "")
            ts = hop.get("timestamp", hop.get("at", ""))
            click.echo(f"    {actor} — {action} @ {ts}")


@main.command("create")
@click.argument("file", type=click.Path(), required=False)
@click.option("--claim", "-c", multiple=True, help="Claim content")
@click.option("--trust", "-t", multiple=True, type=float, help="Trust score (0-1)")
@click.option("--src", "-s", multiple=True, help="Source for each claim")
@click.option("--tier", multiple=True, type=int, help="Authority tier (1-5)")
@click.option("--ver", is_flag=True, help="Mark claims as verified")
@click.option("--ai", is_flag=True, help="Mark claims as AI-generated")
@click.option("--by", "author", help="Author email or ID")
@click.option("--label", "classification", help="Security classification")
@click.option("--agent", "agent_id", help="AI agent ID")
@click.option("--demo", is_flag=True, help="Create a demo .akf file with walkthrough")
def create_cmd(file, claim, trust, src, tier, ver, ai, author, classification, agent_id, demo) -> None:
    """Create a new .akf file with specified claims."""
    if demo:
        demo_file = file or "demo.akf"
        unit = create_multi(
            [
                {"content": "Q3 revenue was $4.2B", "confidence": 0.98, "source": "SEC Filing", "authority_tier": 1, "verified": True},
                {"content": "Market share grew 2%", "confidence": 0.75, "source": "analyst report", "authority_tier": 3},
                {"content": "AI predicts 15% growth", "confidence": 0.6, "ai_generated": True, "risk": "Model trained on limited data"},
            ],
            author="demo@example.com",
            classification="internal",
        )
        unit.save(demo_file)
        click.secho(f"Created demo file: {demo_file}", fg="green")
        click.echo()
        click.echo("This file contains 3 sample claims with different trust levels:")
        click.echo("  1. High-trust verified SEC data (0.98)")
        click.echo("  2. Medium-trust analyst report (0.75)")
        click.echo("  3. AI-generated prediction with risk note (0.60)")
        click.echo()
        click.echo("Try these commands:")
        click.echo(f"  akf inspect {demo_file}")
        click.echo(f"  akf trust {demo_file}")
        click.echo(f"  akf validate {demo_file}")
        click.echo(f"  akf audit {demo_file}")
        return

    if not file:
        click.secho("Error: FILE argument required (or use --demo)", fg="red")
        sys.exit(1)
    if not claim or not trust:
        click.secho("Error: --claim and --trust are required", fg="red")
        sys.exit(1)
    if len(claim) != len(trust):
        click.secho("Error: Number of --claim and --trust must match", fg="red")
        sys.exit(1)

    claims = []
    for i, (c, t) in enumerate(zip(claim, trust)):
        kwargs: dict = {}
        if src and i < len(src):
            kwargs["source"] = src[i]
        if tier and i < len(tier):
            kwargs["authority_tier"] = tier[i]
        if ver:
            kwargs["verified"] = True
        if ai:
            kwargs["ai_generated"] = True
        claims.append({"content": c, "confidence": t, **kwargs})

    envelope: dict = {}
    if author:
        envelope["author"] = author
    if classification:
        envelope["classification"] = classification
    if agent_id:
        envelope["agent"] = agent_id

    unit = create_multi(claims, **envelope)
    unit.save(file)
    click.secho(f"Created {file} with {len(claims)} claim(s)", fg="green")


@main.command("validate")
@click.argument("file", type=click.Path(exists=True))
def validate_cmd(file) -> None:
    """Validate an .akf file."""
    result = validate(file)
    if result.valid:
        unit = load(file)
        level_names = {0: "Invalid", 1: "Minimal", 2: "Practical", 3: "Full"}
        label_str = unit.classification or "none"
        hash_str = "\u2713 integrity" if unit.integrity_hash else "no hash"
        click.secho(
            f"\u2705 Valid AKF (Level {result.level}: {level_names[result.level]}) "
            f"| {len(unit.claims)} claims | {label_str} | {hash_str}",
            fg="green",
        )
    else:
        click.secho("\u274c Invalid AKF", fg="red")
        for err in result.errors:
            click.secho(f"  \u2022 {err}", fg="red")

    for warn in result.warnings:
        click.secho(f"  \u26a0 {warn}", fg="yellow")


@main.command()
@click.argument("file", type=click.Path(exists=True))
def inspect(file) -> None:
    """Pretty-print an .akf file with trust indicators."""
    from . import universal as akf_u
    meta = akf_u.extract(file)
    if meta is not None:
        unit = AKF(**meta)
    else:
        unit = load(file)

    click.secho(f"AKF {unit.version} | {unit.id}", bold=True)
    if unit.author:
        click.echo(f"  by: {unit.author}")
    if unit.classification:
        click.echo(f"  label: {unit.classification}")
    click.echo(f"  claims: {len(unit.claims)}")
    click.echo()

    for claim in unit.claims:
        if claim.confidence >= 0.8:
            color = "green"
            icon = "\U0001f7e2"
        elif claim.confidence >= 0.5:
            color = "yellow"
            icon = "\U0001f7e1"
        else:
            color = "red"
            icon = "\U0001f534"

        tier_str = f"Tier {claim.authority_tier}" if claim.authority_tier else ""
        src_str = claim.source or ""
        parts = [f'{icon} {claim.confidence:.2f}  "{claim.content}"']
        if src_str:
            parts.append(src_str)
        if tier_str:
            parts.append(tier_str)
        if claim.verified:
            parts.append(click.style("verified", fg="green"))
        if claim.ai_generated:
            parts.append(click.style("\u26a0 AI", fg="yellow"))
        if claim.origin:
            parts.append(click.style(f"origin:{claim.origin.type}", fg="cyan"))
        if claim.reviews:
            verdicts = ",".join(r.verdict for r in claim.reviews)
            parts.append(click.style(f"reviewed:{verdicts}", fg="blue"))
        if claim.risk:
            parts.append(click.style(f"risk: {claim.risk}", fg="red"))

        click.echo("  " + "  ".join(parts))


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--threshold", "-t", default=0.6, type=float, help="Trust threshold")
def trust(file, threshold) -> None:
    """Compute effective trust for all claims."""
    from . import universal as akf_u
    meta = akf_u.extract(file)
    if meta is not None:
        unit = AKF(**meta)
    else:
        unit = load(file)
    results = compute_all(unit)

    for claim, result in zip(unit.claims, results):
        if result.decision == "ACCEPT":
            color = "green"
        elif result.decision == "LOW":
            color = "yellow"
        else:
            color = "red"

        extras = []
        extras.append(f"t={claim.confidence}")
        extras.append(f"tier={claim.authority_tier or 3}")
        extras.append(f"auth={result.breakdown['authority']}")
        if result.breakdown.get("origin_weight", 1.0) != 1.0:
            extras.append(f"origin={result.breakdown['origin_weight']}")
        if result.breakdown.get("grounding_bonus", 0) > 0:
            extras.append(f"ground=+{result.breakdown['grounding_bonus']:.2f}")
        if result.breakdown.get("review_bonus", 0) != 0:
            extras.append(f"review={result.breakdown['review_bonus']:+.2f}")

        click.secho(
            f"  {result.decision:6s}  {result.score:.4f}  \"{claim.content}\"  "
            f"({', '.join(extras)})",
            fg=color,
        )


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--output", "-o", required=True, type=click.Path(), help="Output file")
@click.option("--threshold", "-t", default=0.6, type=float, help="Trust threshold")
@click.option("--agent", help="Consuming agent ID")
@click.option("--penalty", "-p", default=-0.03, type=float, help="Transform penalty")
def consume(file, output, threshold, agent, penalty) -> None:
    """Filter by trust and produce derived .akf."""
    from .transform import AKFTransformer

    unit = load(file)
    transformer = AKFTransformer(unit).filter(trust_min=threshold)
    if penalty:
        transformer = transformer.penalty(penalty)
    if agent:
        transformer = transformer.by(agent)
    derived = transformer.build()
    derived.save(output)

    click.secho(
        f"Consumed {file} -> {output} | "
        f"{len(derived.claims)} claims retained (threshold={threshold})",
        fg="green",
    )


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["tree", "json"]), default="tree")
def provenance(file, fmt) -> None:
    """Show provenance chain."""
    unit = load(file)
    if fmt == "tree":
        click.echo(format_tree(unit))
    else:
        if unit.prov:
            for hop in unit.prov:
                click.echo(json.dumps(hop.to_dict(compact=True), indent=2))


@main.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--agent", required=True, help="AI agent ID")
@click.option("--claim", "-c", multiple=True, required=True, help="Claim content")
@click.option("--trust", "-t", multiple=True, required=True, type=float, help="Trust score")
@click.option("--ai", is_flag=True, default=True, help="AI-generated flag")
@click.option("--risk", "-r", multiple=True, help="Risk description")
def enrich(file, agent, claim, trust, ai, risk) -> None:
    """Add AI-enriched claims to an existing .akf file."""
    if len(claim) != len(trust):
        click.secho("Error: Number of --claim and --trust must match", fg="red")
        sys.exit(1)

    unit = load(file)
    new_claims = list(unit.claims)
    new_ids = []

    for i, (c, t) in enumerate(zip(claim, trust)):
        kwargs: dict = {"ai_generated": True}
        if risk and i < len(risk):
            kwargs["risk"] = risk[i]
        new_claim = Claim(content=c, confidence=t, **kwargs)
        new_claims.append(new_claim)
        if new_claim.id:
            new_ids.append(new_claim.id)

    updated = unit.model_copy(update={"claims": new_claims})
    updated = add_hop(updated, by=agent, action="enriched", adds=new_ids)
    updated.save(file)

    click.secho(f"Enriched {file} with {len(claim)} AI claim(s) by {agent}", fg="green")


@main.command("embed")
@click.argument("file", type=click.Path(exists=True))
@click.option("--classification", "--label", help="Security classification")
@click.option("--claim", "-c", multiple=True, help="Claim content")
@click.option("--trust", "-t", multiple=True, type=float, help="Trust score per claim")
@click.option("--src", "-s", multiple=True, help="Source per claim")
@click.option("--ai", is_flag=True, help="Mark claims as AI-generated")
@click.option("--agent", help="AI agent ID for provenance")
def embed_cmd(file, classification, claim, trust, src, ai, agent) -> None:
    """Embed AKF metadata into any supported file format."""
    from . import universal as akf_u

    metadata = {}
    if classification:
        metadata["classification"] = classification

    claims = []
    if claim:
        if trust and len(claim) != len(trust):
            click.secho("Error: Number of --claim and --trust must match", fg="red")
            sys.exit(1)
        for i, c in enumerate(claim):
            cl = {"c": c, "t": trust[i] if trust else 0.7}
            if src and i < len(src):
                cl["src"] = src[i]
            if ai:
                cl["ai"] = True
            claims.append(cl)

    if agent:
        from datetime import datetime, timezone
        metadata.setdefault("provenance", []).append({
            "actor": agent, "action": "embedded",
            "at": datetime.now(timezone.utc).isoformat(),
        })

    # If no new claims or metadata provided, re-embed existing metadata
    if not claims and not metadata:
        existing = akf_u.extract(file)
        if existing:
            akf_u.embed(file, metadata=existing)
            click.secho("Re-embedded existing AKF metadata into {}".format(file), fg="green")
        else:
            click.secho("No AKF metadata found to embed. Use --claim to add claims.", fg="yellow")
        return

    akf_u.embed(file, claims=claims if claims else None, metadata=metadata if metadata else None,
                classification=classification)
    click.secho("Embedded AKF metadata into {}".format(file), fg="green")
    if claims:
        click.echo("  {} claim(s)".format(len(claims)))
    if classification:
        click.echo("  classification: {}".format(classification))


@main.command("extract")
@click.argument("file", type=click.Path(exists=True))
@click.option("--format", "fmt", type=click.Choice(["json", "summary"]), default="json")
def extract_cmd(file, fmt) -> None:
    """Extract AKF metadata from any supported file format."""
    from . import universal as akf_u

    meta = akf_u.extract(file)
    if meta is None:
        click.secho("No AKF metadata found in {}".format(file), fg="yellow")
        click.echo("  Tip: Run 'akf embed {}' to add metadata".format(file))
        sys.exit(1)

    if fmt == "json":
        click.echo(json.dumps(meta, indent=2, ensure_ascii=False))
    else:
        click.echo(akf_u.info(file))


_EXT_TO_FORMAT = {".html": "html", ".json": "json", ".md": "markdown", ".csv": "csv", ".pdf": "pdf"}


def _export_report(file_or_dir, output, open_report, command_name):
    """Shared helper: generate enterprise report and write to file."""
    from .report import enterprise_report
    import os

    ext = Path(output).suffix.lower()
    fmt = _EXT_TO_FORMAT.get(ext)
    if not fmt:
        click.secho("Unknown output format '{}'. Use: .html .json .md .csv .pdf".format(ext), fg="red")
        sys.exit(1)

    report = enterprise_report(file_or_dir)
    rendered = report.render(format=fmt)

    mode = "wb" if isinstance(rendered, (bytes, bytearray)) else "w"
    with open(output, mode) as f:
        f.write(rendered)

    click.secho("Report saved to {} ({} files, {} claims)".format(
        output, report.total_files, report.total_claims), fg="green")

    if open_report:
        import webbrowser
        webbrowser.open("file://" + os.path.abspath(output))


def _trust_bar(count, total, width=20):
    """Render an ASCII trust bar."""
    if total <= 0:
        return "\u2591" * width
    filled = min(int(round(count / total * width)), width)
    return "\u2588" * filled + "\u2591" * (width - filled)


@main.command("scan")
@click.argument("file_or_dir", type=click.Path(exists=True))
@click.option("--recursive", "-r", is_flag=True, default=True, help="Scan directories recursively (default: on)")
@click.option("--no-recursive", is_flag=True, help="Scan only top-level files in directory")
@click.option("--max-files", "-n", default=10000, type=int, help="Maximum files to scan (default: 10000)")
@click.option("--output", "-o", type=click.Path(), help="Export report (.html, .json, .csv, .md, .pdf)")
@click.option("--open", "open_report", is_flag=True, help="Open report in browser after export")
def scan_cmd(file_or_dir, recursive, no_recursive, max_files, output, open_report) -> None:
    """Security scan any file or directory for AKF metadata."""
    from . import universal as akf_u
    from pathlib import Path
    from collections import Counter

    if output:
        _export_report(file_or_dir, output, open_report, "scan")
        return

    if no_recursive:
        recursive = False

    target = Path(file_or_dir)
    if target.is_dir():
        def progress(scanned, enriched):
            click.echo("\r  Scanning... {} files checked, {} enriched".format(scanned, enriched), nl=False)

        reports = akf_u.scan_directory(str(target), recursive=recursive, max_files=max_files, on_progress=progress)
        enriched = [r for r in reports if r.enriched]

        # Clear progress line
        if len(reports) >= 100:
            click.echo("\r" + " " * 60 + "\r", nl=False)

        # Structured summary header
        title = " AKF Scan "
        path_str = str(target)
        summary = "{}   {} scanned \u00b7 {} enriched".format(path_str, len(reports), len(enriched))
        box_w = max(len(title) + 2, len(summary) + 4, 54)
        click.secho("\u250c\u2500{}\u2500\u2510".format(title.center(box_w - 2, "\u2500")), bold=True)
        click.secho("\u2502  {}{}  \u2502".format(summary, " " * (box_w - len(summary) - 4)), bold=True)
        click.secho("\u2514{}\u2518".format("\u2500" * (box_w)), bold=True)
        click.echo()

        if len(reports) >= max_files:
            click.secho("  (stopped at --max-files limit of {})".format(max_files), fg="yellow")

        # Trust distribution
        if enriched:
            high = sum(1 for r in enriched if r.overall_trust is not None and r.overall_trust >= 0.7)
            mod = sum(1 for r in enriched if r.overall_trust is not None and 0.4 <= r.overall_trust < 0.7)
            low = sum(1 for r in enriched if r.overall_trust is not None and r.overall_trust < 0.4)
            total_e = len(enriched)

            click.echo("Trust    ", nl=False)
            click.secho("High ", fg="green", nl=False)
            click.echo("{} {:>3}    ".format(_trust_bar(high, total_e), high), nl=False)
            click.secho("Mod ", fg="yellow", nl=False)
            click.echo("{} {:>3}    ".format(_trust_bar(mod, total_e), mod), nl=False)
            click.secho("Low ", fg="red", nl=False)
            click.echo("{} {:>3}".format(_trust_bar(low, total_e), low))
            click.echo()

            # Format breakdown
            fmt_counts = Counter()
            for r in enriched:
                fmt_name = r.format.upper() if r.format else "Unknown"
                fmt_counts[fmt_name] += 1
            # Also count sidecars
            sidecar_count = sum(1 for r in reports if not r.enriched and (
                str(getattr(r, 'format', '')).lower() in ('sidecar',)))
            fmt_parts = ["{} {}".format(fmt, cnt) for fmt, cnt in fmt_counts.most_common()]
            if fmt_parts:
                click.echo("Format   " + " \u00b7 ".join(fmt_parts))
                click.echo()

        click.echo("Tip: akf scan {} --output report.html --open".format(file_or_dir))
    else:
        report = akf_u.scan(str(target))
        if not report.enriched:
            click.secho("No AKF metadata in {}".format(file_or_dir), fg="yellow")
            return

        click.secho("AKF Scan: {}".format(file_or_dir), bold=True)
        click.echo("  Format:          {}".format(report.format))
        click.echo("  Mode:            {}".format(report.mode))
        if report.classification:
            click.echo("  Classification:  {}".format(report.classification))
        if report.overall_trust is not None:
            click.echo("  Trust score:     {:.2f}".format(report.overall_trust))
        if report.ai_contribution is not None:
            click.echo("  AI contribution: {:.0f}%".format(report.ai_contribution * 100))
        click.echo("  Claims:          {} ({} verified, {} AI-generated)".format(
            report.claim_count, report.verified_claim_count, report.ai_claim_count))
        click.echo("  Provenance:      {} hops".format(report.provenance_depth))
        if report.risk_claims:
            click.secho("  Risks:           {}".format(len(report.risk_claims)), fg="red")
            for risk in report.risk_claims:
                click.secho("    - {}".format(risk), fg="red")


@main.command("info")
@click.argument("file", type=click.Path(exists=True))
def info_cmd(file) -> None:
    """Quick info check on any file's AKF metadata."""
    from . import universal as akf_u
    click.echo(akf_u.info(file))


@main.command("sidecar")
@click.argument("file", type=click.Path(exists=True))
@click.option("--classification", "--label", help="Security classification")
@click.option("--agent", help="AI agent ID")
def sidecar_cmd(file, classification, agent) -> None:
    """Create a sidecar .akf.json file for any file."""
    from . import sidecar

    metadata = {}
    if classification:
        metadata["classification"] = classification
    if agent:
        from datetime import datetime, timezone
        metadata["provenance"] = [
            {"actor": agent, "action": "tagged", "at": datetime.now(timezone.utc).isoformat()}
        ]

    sidecar.create(file, metadata)
    sc_path = sidecar.sidecar_path(file)
    click.secho("Created sidecar: {}".format(sc_path), fg="green")


@main.command("convert")
@click.argument("file_or_dir", type=click.Path(exists=True))
@click.option("--output", "-o", required=False, default=None, type=click.Path(), help="Output .akf file or directory")
@click.option("--recursive", "-r", is_flag=True, help="Recurse into subdirectories")
@click.option("--mode", "-m", type=click.Choice(["extract", "enrich", "both"]), default="both",
              help="extract=metadata only, enrich=baseline only, both=auto")
@click.option("--overwrite", is_flag=True, help="Overwrite existing .akf outputs")
@click.option("--agent", help="Agent ID for enrich-mode provenance")
def convert_cmd(file_or_dir, output, recursive, mode, overwrite, agent) -> None:
    """Extract AKF metadata from any format into standalone .akf."""
    from . import universal as akf_u
    from pathlib import Path

    target = Path(file_or_dir)
    if target.is_dir():
        # Default output to input dir when not specified
        out_dir = output if output else str(target)
        result = akf_u.convert_directory(
            str(target), output_dir=out_dir, recursive=recursive,
            mode=mode, overwrite=overwrite, agent=agent,
        )
        click.secho(
            "Converted {}, skipped {}, failed {}".format(
                result.converted, result.skipped, result.failed),
            fg="green" if result.failed == 0 else "red",
        )
        for err in result.errors:
            click.secho("  {}".format(err), fg="red")
    else:
        # Default output to <filename>.akf in same directory
        out_path = output if output else str(target) + ".akf"
        # Single-file mode: try extract first, fall back to enrich
        if mode in ("extract", "both"):
            try:
                akf_u.to_akf(str(target), out_path)
                click.secho("Converted {} -> {}".format(file_or_dir, out_path), fg="green")
                return
            except ValueError:
                if mode == "extract":
                    click.secho("No AKF metadata found in {}".format(file_or_dir), fg="red")
                    sys.exit(1)
        # enrich or both-fallback
        akf_u._enrich_to_akf(str(target), out_path, agent)
        click.secho("Enriched {} -> {}".format(file_or_dir, out_path), fg="green")


@main.command("formats")
def formats_cmd() -> None:
    """List all supported file formats."""
    from . import universal as akf_u

    fmts = akf_u.supported_formats()
    click.secho("Supported AKF Formats:", bold=True)
    click.echo()
    for ext, info in sorted(fmts.items()):
        mode = info.get("mode", "unknown")
        mechanism = info.get("mechanism", "")
        click.echo("  {:<10s} {:<12s} {}".format(ext, mode, mechanism))


@main.command()
@click.argument("file1", type=click.Path(exists=True))
@click.argument("file2", type=click.Path(exists=True))
def diff(file1, file2) -> None:
    """Show differences between two .akf files."""
    u1 = load(file1)
    u2 = load(file2)

    # Compare claims
    c1_ids = {c.id for c in u1.claims if c.id}
    c2_ids = {c.id for c in u2.claims if c.id}

    added = c2_ids - c1_ids
    removed = c1_ids - c2_ids
    common = c1_ids & c2_ids

    click.secho(f"Comparing {file1} vs {file2}", bold=True)
    click.echo(f"  Claims: {len(u1.claims)} -> {len(u2.claims)}")

    if added:
        click.secho(f"  + Added: {len(added)} claims", fg="green")
        for cid in added:
            claim = next(c for c in u2.claims if c.id == cid)
            click.secho(f"    + [{cid}] \"{claim.content}\" (t={claim.confidence})", fg="green")

    if removed:
        click.secho(f"  - Removed: {len(removed)} claims", fg="red")
        for cid in removed:
            claim = next(c for c in u1.claims if c.id == cid)
            click.secho(f"    - [{cid}] \"{claim.content}\" (t={claim.confidence})", fg="red")

    # Trust changes in common claims
    for cid in common:
        c1 = next(c for c in u1.claims if c.id == cid)
        c2 = next(c for c in u2.claims if c.id == cid)
        if c1.confidence != c2.confidence:
            delta = c2.confidence - c1.confidence
            color = "green" if delta > 0 else "red"
            click.secho(f"  ~ [{cid}] trust {c1.confidence} -> {c2.confidence} ({delta:+.4f})", fg=color)

    # Label change
    if u1.classification != u2.classification:
        click.echo(f"  Label: {u1.classification or 'none'} -> {u2.classification or 'none'}")

    # Provenance
    p1 = len(u1.prov) if u1.prov else 0
    p2 = len(u2.prov) if u2.prov else 0
    if p1 != p2:
        click.echo(f"  Provenance hops: {p1} -> {p2}")


@main.command("audit")
@click.argument("file_or_dir", type=click.Path(exists=True))
@click.option("--regulation", "-r", help="Check specific regulation (eu_ai_act, sox, hipaa, gdpr, nist_ai, iso_42001)")
@click.option("--trail", is_flag=True, help="Show audit trail")
@click.option("--export", "export_fmt", type=click.Choice(["json", "markdown", "csv"]), help="Export audit result")
@click.option("--output", "-o", type=click.Path(), help="Export report (.html, .json, .csv, .md, .pdf)")
@click.option("--open", "open_report", is_flag=True, help="Open report in browser after export")
def audit_cmd(file_or_dir, regulation, trail, export_fmt, output, open_report) -> None:
    """Run compliance audit on a file or directory."""
    from .compliance import audit, check_regulation, audit_trail, export_audit
    from pathlib import Path

    if output:
        _export_report(file_or_dir, output, open_report, "audit")
        return

    target = Path(file_or_dir)

    # If it's a directory, find all AKF-enriched files and audit each
    if target.is_dir():
        from . import universal as akf_u
        akf_files = []
        for p in sorted(target.rglob("*")):
            if p.is_file() and not p.name.startswith("."):
                if p.suffix == ".akf" or p.name.endswith(".akf.json"):
                    continue
                # Check if file has AKF metadata (sidecar or embedded)
                sidecar = p.parent / (p.name + ".akf")
                sidecar_json = p.parent / (p.name + ".akf.json")
                if sidecar.exists() or sidecar_json.exists():
                    akf_files.append(str(p))
                else:
                    try:
                        meta = akf_u.extract(str(p))
                        if meta:
                            akf_files.append(str(p))
                    except Exception:
                        pass

        if not akf_files:
            click.secho(f"No AKF-enriched files found in {file_or_dir}", fg="yellow")
            click.echo(f"  Tip: Run 'akf stamp <file>' to add metadata first")
            sys.exit(1)

        # Audit all files first
        compliant_count = 0
        total = len(akf_files)
        audit_results = []
        for filepath in akf_files:
            try:
                if regulation:
                    result = check_regulation(filepath, regulation)
                else:
                    result = audit(filepath)
                audit_results.append((filepath, result))
                if result.compliant:
                    compliant_count += 1
            except Exception:
                audit_results.append((filepath, None))

        # Structured summary header
        title = " AKF Audit "
        pct = round(compliant_count / total * 100) if total else 0
        summary = "{}   {} files \u00b7 {}/{} compliant ({}%)".format(
            str(target), total, compliant_count, total, pct)
        box_w = max(len(title) + 2, len(summary) + 4, 54)
        click.secho("\u250c\u2500{}\u2500\u2510".format(title.center(box_w - 2, "\u2500")), bold=True)
        click.secho("\u2502  {}{}  \u2502".format(summary, " " * (box_w - len(summary) - 4)), bold=True)
        click.secho("\u2514{}\u2518".format("\u2500" * (box_w)), bold=True)
        click.echo()

        # Per-file results
        for filepath, result in audit_results:
            rel = Path(filepath).relative_to(target)
            if result is None:
                click.echo(f"  \u26a0\ufe0f  {rel} — could not audit")
            else:
                status_icon = "\u2705" if result.compliant else "\u274c"
                click.echo("  {} {:<40s} {:.2f}".format(status_icon, str(rel)[:40], result.score))

        click.echo()
        color = "green" if compliant_count == total else ("yellow" if compliant_count > 0 else "red")
        click.secho("Result: {}/{} files compliant".format(compliant_count, total), fg=color, bold=True)
        click.echo()
        click.echo("Tip: akf audit {} --output report.html --open".format(file_or_dir))
        return

    # Single file audit
    if trail:
        try:
            click.echo(audit_trail(file_or_dir, format="text"))
        except (ValueError, json.JSONDecodeError) as e:
            click.secho(f"Error: {e}", fg="red")
            sys.exit(1)
        return

    try:
        if regulation:
            result = check_regulation(file_or_dir, regulation)
        else:
            result = audit(file_or_dir)
    except (ValueError, json.JSONDecodeError) as e:
        click.secho(f"Error: Could not audit {file_or_dir}: {e}", fg="red")
        click.echo(f"  Tip: Run 'akf embed {file_or_dir}' or 'akf stamp {file_or_dir}' to add metadata first")
        sys.exit(1)

    if export_fmt:
        click.echo(export_audit(result, format=export_fmt))
        return

    status = "COMPLIANT" if result.compliant else "NON-COMPLIANT"
    color = "green" if result.compliant else "red"
    label = result.regulation if result.regulation and result.regulation != "general" else "Audit"
    click.secho(f"{label}: {status} (score: {result.score:.2f})", fg=color)

    for check in result.checks:
        icon = "\u2705" if check["passed"] else "\u274c"
        click.echo(f"  {icon} {check['check']}")

    if result.recommendations:
        click.echo()
        click.secho("Recommendations:", bold=True)
        for rec in result.recommendations:
            click.echo(f"  \u2022 {rec}")


@main.command("stream")
@click.argument("action", type=click.Choice(["collect"]))
@click.argument("file", type=click.Path(exists=True))
@click.option("--output", "-o", type=click.Path(), help="Output .akf file")
def stream_cmd(action, file, output) -> None:
    """Streaming .akfl operations."""
    from .streaming import collect_stream

    if action == "collect":
        try:
            unit = collect_stream(file)
        except (ValueError, FileNotFoundError) as e:
            click.secho(f"Error: {e}", fg="red")
            sys.exit(1)

        if output:
            unit.save(output)
            click.secho(f"Collected {len(unit.claims)} claims from {file} -> {output}", fg="green")
        else:
            click.echo(unit.to_json(indent=2, compact=True))


@main.command("security")
@click.argument("file", type=click.Path(exists=True))
def security_cmd(file) -> None:
    """Show security score with letter grade."""
    from .security import security_score

    unit = load(file)
    result = security_score(unit)

    color = "green" if result.score >= 8 else "yellow" if result.score >= 5 else "red"
    click.secho(f"Security Score: {result.score:.1f}/10 (Grade: {result.grade})", fg=color, bold=True)
    click.echo()

    for check in result.checks:
        icon = "\u2705" if check["passed"] else "\u274c"
        click.echo(f"  {icon} {check['check']}")

    if result.issues:
        click.echo()
        click.secho("Issues:", bold=True)
        for issue in result.issues:
            click.echo(f"  \u2022 {issue}")


@main.command("explain")
@click.argument("file", type=click.Path(exists=True))
@click.option("--claim-id", help="Explain a specific claim by ID")
def explain_cmd(file, claim_id) -> None:
    """Show trust explanation for claims."""
    from .trust import explain_trust

    unit = load(file)
    for claim in unit.claims:
        if claim_id and claim.id != claim_id:
            continue
        click.echo(explain_trust(claim))
        click.echo()
        if claim_id:
            return

    if claim_id:
        click.secho(f"Claim '{claim_id}' not found", fg="red")


@main.command("hash")
@click.argument("file", type=click.Path(exists=True))
def hash_cmd(file) -> None:
    """Compute and display/update integrity hash."""
    from .security import compute_security_hash

    unit = load(file)
    new_hash = compute_security_hash(unit)

    if unit.integrity_hash:
        if unit.integrity_hash == new_hash:
            click.secho(f"Hash valid: {new_hash}", fg="green")
        else:
            click.secho(f"Hash mismatch!", fg="red")
            click.echo(f"  Stored:   {unit.integrity_hash}")
            click.echo(f"  Computed: {new_hash}")
    else:
        click.echo(f"Hash: {new_hash}")
        # Update the file with the hash
        unit = unit.model_copy(update={"integrity_hash": new_hash})
        unit.save(file)
        click.secho(f"Updated {file} with integrity hash", fg="green")


@main.group("kb")
def kb_group() -> None:
    """Knowledge base commands."""
    pass


@kb_group.command("stats")
@click.argument("directory", type=click.Path(exists=True))
def kb_stats_cmd(directory) -> None:
    """Show knowledge base statistics."""
    from .knowledge_base import KnowledgeBase

    kb = KnowledgeBase(directory)
    s = kb.stats()
    click.secho("Knowledge Base Stats", bold=True)
    click.echo(f"  Topics:         {s['topics']}")
    click.echo(f"  Total claims:   {s['total_claims']}")
    if s['total_claims'] > 0:
        click.echo(f"  Average trust:  {s['average_trust']:.2f}")


@kb_group.command("query")
@click.argument("directory", type=click.Path(exists=True))
@click.option("--topic", "-t", help="Filter by topic")
@click.option("--min-trust", type=float, default=0.0, help="Minimum trust threshold")
def kb_query_cmd(directory, topic, min_trust) -> None:
    """Query claims from the knowledge base."""
    from .knowledge_base import KnowledgeBase

    kb = KnowledgeBase(directory)
    claims = kb.query(topic=topic, min_trust=min_trust)

    if not claims:
        click.echo("No claims found.")
        return

    click.secho(f"Found {len(claims)} claim(s):", bold=True)
    for claim in claims:
        src = f" [{claim.source}]" if claim.source and claim.source != "unspecified" else ""
        click.echo(f"  {claim.confidence:.2f}  \"{claim.content}\"{src}")


@kb_group.command("prune")
@click.argument("directory", type=click.Path(exists=True))
@click.option("--max-age", type=int, default=90, help="Max age in days")
@click.option("--min-trust", type=float, default=0.3, help="Min trust to keep")
def kb_prune_cmd(directory, max_age, min_trust) -> None:
    """Prune low-trust or stale claims from the knowledge base."""
    from .knowledge_base import KnowledgeBase

    kb = KnowledgeBase(directory)
    pruned = kb.prune(max_age_days=max_age, min_trust=min_trust)
    click.secho(f"Pruned {pruned} claim(s)", fg="green")


@main.command("stamp")
@click.argument("file", type=click.Path(exists=True))
@click.option("--agent", default=None, help="Agent identifier (e.g. claude-code)")
@click.option("--evidence", multiple=True, help="Evidence strings (repeatable)")
@click.option("--confidence", type=float, default=None, help="Confidence score 0.0-1.0")
@click.option("--claim", "claims", multiple=True, help="Claim text (repeatable)")
@click.option("--model", default=None, help="Model identifier (e.g. gpt-4o)")
@click.option("--label", default=None, help="Classification label")
@click.option("--format", "fmt", default="auto", help="Output format: auto, embed, sidecar")
def stamp_cmd(file, agent, evidence, confidence, claims, model, label, fmt):
    """Add AKF trust metadata to any file.

    Stamps the file with trust scores, provenance, and classification.
    The file remains openable in its native application.

    Examples:

      akf stamp report.md --agent claude-code --evidence "tests pass"

      akf stamp output.pdf --claim "Revenue $4.2B" --confidence 0.95 --model gpt-4o
    """
    from .stamp import stamp_file as _stamp_file

    classification = label or "internal"
    trust_score = confidence if confidence is not None else 0.7
    evidence_list = list(evidence) if evidence else None
    claim_list = list(claims) if claims else None

    if fmt == "sidecar":
        from . import sidecar
        sidecar.create(file, {"classification": classification})
        click.echo(f"\u2713 Stamped {file} (sidecar, label: {classification})")
        return

    unit = _stamp_file(
        file,
        agent=agent,
        model=model,
        claims=claim_list,
        trust_score=trust_score,
        classification=classification,
        evidence=evidence_list,
    )

    claims_count = len(unit.claims)
    avg_trust = sum(c.confidence for c in unit.claims) / claims_count if claims_count else 0.0

    click.echo(
        f"\u2713 Stamped {file} ({claims_count} claim(s), avg trust: {avg_trust:.2f}, label: {classification})"
    )


@main.command("freshness")
@click.argument("file", type=click.Path(exists=True))
def freshness_cmd(file):
    """Check freshness of all claims in a file."""
    from .trust import freshness_status as _freshness_status

    unit = load(file)
    for claim in unit.claims or []:
        status = _freshness_status(claim)
        icon = {"fresh": "+", "stale": "~", "expired": "!", "no_expiry": "-"}.get(status, "?")
        preview = (claim.content[:60] + "...") if len(claim.content) > 60 else claim.content
        expires = getattr(claim, "expires_at", None) or "never"
        click.echo(f"  [{icon}] {status:10s} {preview}")
        if expires != "never":
            click.echo(f"              expires: {expires}")


# ---------------------------------------------------------------------------
# Cryptographic signing commands
# ---------------------------------------------------------------------------

@main.command("keygen")
@click.option("--name", default="default", help="Key name prefix")
@click.option("--dir", "key_dir", default=None, type=click.Path(), help="Key directory (default: ~/.akf/keys/)")
def keygen_cmd(name, key_dir):
    """Generate an Ed25519 keypair for signing .akf files."""
    from .signing import keygen

    priv_path, pub_path = keygen(key_dir=key_dir, name=name)
    click.secho("Generated Ed25519 keypair:", fg="green")
    click.echo(f"  Private key: {priv_path}")
    click.echo(f"  Public key:  {pub_path}")
    click.echo()
    click.echo("Keep the private key safe. Share the public key for verification.")


@main.command("sign")
@click.argument("file", type=click.Path(exists=True))
@click.option("--key", "key_path", default=None, type=click.Path(exists=True),
              help="Private key path (default: ~/.akf/keys/default.pem)")
@click.option("--signer", default=None, help="Signer identifier (email or ID)")
def sign_cmd(file, key_path, signer):
    """Sign an .akf file with an Ed25519 private key."""
    from .signing import sign as akf_sign

    if key_path is None:
        key_path = str(Path.home() / ".akf" / "keys" / "default.pem")
        if not Path(key_path).exists():
            click.secho("No default key found. Run 'akf keygen' first.", fg="red")
            sys.exit(1)

    unit = load(file)
    signed = akf_sign(unit, key_path, signer=signer)
    signed.save(file)
    click.secho(f"Signed {file}", fg="green")
    click.echo(f"  Algorithm: {signed.signature_algorithm}")
    click.echo(f"  Key ID:    {signed.public_key_id}")
    if signed.signed_by:
        click.echo(f"  Signer:    {signed.signed_by}")


@main.command("verify")
@click.argument("file", type=click.Path(exists=True))
@click.option("--key", "key_path", default=None, type=click.Path(exists=True),
              help="Public key path (default: ~/.akf/keys/default.pub.pem)")
def verify_cmd(file, key_path):
    """Verify the signature on an .akf file."""
    from .signing import verify as akf_verify

    if key_path is None:
        key_path = str(Path.home() / ".akf" / "keys" / "default.pub.pem")
        if not Path(key_path).exists():
            click.secho("No default public key found. Specify --key.", fg="red")
            sys.exit(1)

    unit = load(file)
    try:
        akf_verify(unit, key_path)
        click.secho(f"Signature valid", fg="green")
        if unit.signed_by:
            click.echo(f"  Signed by: {unit.signed_by}")
        if unit.signed_at:
            click.echo(f"  Signed at: {unit.signed_at}")
    except ValueError as e:
        click.secho(f"Verification failed: {e}", fg="red")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Calibration command
# ---------------------------------------------------------------------------

@main.command("calibrate")
@click.argument("file", type=click.Path(exists=True))
@click.option("--method", type=click.Choice(["self_reported", "source_verified", "externally_audited"]),
              help="Calibration method")
@click.option("--verifier", default=None, help="Verifier identifier")
def calibrate_cmd(file, method, verifier):
    """Show or update trust calibration on all claims."""
    from .models import Calibration

    unit = load(file)

    if method is None:
        # Show mode
        click.secho(f"Calibration: {file}", bold=True)
        for claim in unit.claims:
            preview = (claim.content[:50] + "...") if len(claim.content) > 50 else claim.content
            if claim.calibration:
                cal = claim.calibration
                click.echo(f'  {cal.method:20s}  "{preview}"')
                if cal.verifier:
                    click.echo(f"    verifier: {cal.verifier}")
            else:
                click.echo(f'  {"(none)":20s}  "{preview}"')
        return

    # Update mode
    from datetime import datetime, timezone

    cal = Calibration(
        method=method,
        verifier=verifier,
        verified_at=datetime.now(timezone.utc).isoformat(),
    )
    updated_claims = [
        c.model_copy(update={"calibration": cal}) for c in unit.claims
    ]
    updated = unit.model_copy(update={"claims": updated_claims})
    updated.save(file)
    click.secho(f"Calibrated {len(updated.claims)} claims as '{method}'", fg="green")


# ---------------------------------------------------------------------------
# Schema commands
# ---------------------------------------------------------------------------

@main.group("schema")
def schema_group():
    """Schema validation and info commands."""
    pass


@schema_group.command("check")
@click.argument("file", type=click.Path(exists=True))
def schema_check_cmd(file):
    """Validate a file against the AKF schema."""
    result = validate(file)
    if result.valid:
        level_names = {0: "Invalid", 1: "Minimal", 2: "Practical", 3: "Full"}
        click.secho(
            f"Schema valid (Level {result.level}: {level_names[result.level]})",
            fg="green",
        )
    else:
        click.secho("Schema validation failed", fg="red")
        for err in result.errors:
            click.secho(f"  {err}", fg="red")

    for warn in result.warnings:
        click.secho(f"  {warn}", fg="yellow")


@schema_group.command("info")
def schema_info_cmd():
    """Show schema version and registry status."""
    click.secho("AKF Schema Info", bold=True)
    click.echo("  Version:    1.1")
    click.echo("  Schema URL: https://akf.dev/schema/v1.1")
    click.echo("  Spec file:  spec/akf-v1.1.schema.json")
    click.echo("  Registry:   https://akf.dev")


# ---------------------------------------------------------------------------
# Batch command
# ---------------------------------------------------------------------------

@main.command("batch")
@click.argument("manifest", type=click.Path(exists=True))
@click.option("--parallel", is_flag=True, help="Run operations in parallel")
def batch_cmd(manifest, parallel):
    """Process multiple operations from a JSON manifest file.

    Manifest format: {"operations": [{"action": "validate|sign|convert", "file": "..."}]}
    """
    with open(manifest) as f:
        data = json.load(f)

    operations = data.get("operations", [])
    if not operations:
        click.secho("No operations in manifest", fg="yellow")
        return

    def _run_op(op):
        action = op.get("action", "")
        filepath = op.get("file", "")
        result = {"action": action, "file": filepath}
        try:
            if action == "validate":
                r = validate(filepath)
                result["valid"] = r.valid
                result["status"] = "ok"
            elif action == "sign":
                from .signing import sign as akf_sign
                key = op.get("key", str(Path.home() / ".akf" / "keys" / "default.pem"))
                signer = op.get("signer")
                unit = load(filepath)
                signed = akf_sign(unit, key, signer=signer)
                signed.save(filepath)
                result["status"] = "signed"
            elif action == "convert":
                from . import universal as akf_u
                out = op.get("output", filepath + ".akf")
                akf_u.to_akf(filepath, out)
                result["status"] = "converted"
                result["output"] = out
            elif action == "embed":
                from . import universal as akf_u
                akf_u.embed(filepath, classification=op.get("classification"))
                result["status"] = "embedded"
            else:
                result["status"] = "error"
                result["error"] = f"Unknown action: {action}"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        return result

    if parallel:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(_run_op, operations))
    else:
        results = [_run_op(op) for op in operations]

    ok = sum(1 for r in results if r.get("status") not in ("error",))
    err = sum(1 for r in results if r.get("status") == "error")

    click.secho(f"Batch: {ok} succeeded, {err} failed ({len(operations)} total)", fg="green" if err == 0 else "red")
    for r in results:
        icon = "\u2705" if r.get("status") != "error" else "\u274c"
        msg = r.get("error", r.get("status", ""))
        click.echo(f"  {icon} {r['action']} {r['file']} — {msg}")


@main.command("report")
@click.argument("paths", nargs=-1, type=click.Path())
@click.option("--format", "fmt", default="markdown",
              type=click.Choice(["markdown", "json", "html", "csv", "pdf"]),
              help="Output format")
@click.option("--output", "-o", "output_file", default=None,
              type=click.Path(), help="Save report to file")
@click.option("--top", default=5, type=int, help="Number of top risks to show")
def report_cmd(paths, fmt, output_file, top) -> None:
    """Generate an enterprise trust posture report across AKF files.

    Accepts file paths or a directory. Defaults to current directory.

    Examples:

        akf report                          # scan current dir

        akf report /tmp/r1.akf /tmp/r2.akf  # specific files

        akf report /tmp/ --format json      # directory, JSON output

        akf report /tmp/ -o report.md       # save to file
    """
    from .report import enterprise_report

    # PDF requires --output (can't echo bytes to stdout)
    if fmt == "pdf" and not output_file:
        click.secho("PDF format requires --output/-o flag (e.g. akf report . --format pdf -o report.pdf)", fg="red")
        raise SystemExit(1)

    targets = list(paths) if paths else ["."]

    # Single path or list
    if len(targets) == 1:
        target = targets[0]
    else:
        target = targets

    report = enterprise_report(target, format=fmt, top=top)

    if report.total_files == 0:
        click.secho("No .akf files found.", fg="yellow")
        click.echo()
        click.echo("Get started in 3 steps:")
        click.echo()
        click.secho("  1. Initialize AKF in your project:", bold=True)
        click.echo("     akf init")
        click.echo()
        click.secho("  2. Create trust metadata for your files:", bold=True)
        click.echo("     akf create out.akf -c 'Your claim' -t 0.95 --src 'source'")
        click.echo("     akf stamp myfile.py              # stamp an existing file")
        click.echo("     akf embed report.docx             # embed into Office/PDF")
        click.echo()
        click.secho("  3. Run the report again:", bold=True)
        click.echo("     akf report .")
        click.echo()
        click.echo("Run 'akf create --demo' for an interactive walkthrough.")
        return

    try:
        rendered = report.render(format=fmt)
    except ImportError as e:
        click.secho(str(e), fg="red")
        raise SystemExit(1)

    if output_file:
        if isinstance(rendered, (bytes, bytearray)):
            Path(output_file).write_bytes(rendered)
        else:
            Path(output_file).write_text(rendered)
        click.secho(f"Report saved to {output_file} ({report.total_files} files, {report.total_claims} claims)", fg="green")
    else:
        click.echo(rendered)


@main.command("doctor")
def doctor_cmd():
    """Check your AKF installation and PATH setup."""
    import platform
    import shutil

    click.secho("AKF Doctor", bold=True)
    click.echo()

    # Version
    from . import __version__
    click.echo(f"  AKF version:    {__version__}")
    click.echo(f"  Python version: {sys.version.split()[0]}")
    click.echo(f"  Platform:       {platform.system()} {platform.machine()}")
    click.echo()

    # Check if `akf` is on PATH
    akf_bin = shutil.which("akf")
    if akf_bin:
        click.secho(f"  \u2705 akf is on PATH: {akf_bin}", fg="green")
    else:
        click.secho("  \u274c akf is NOT on PATH", fg="red")
        click.echo()
        click.echo("  Workaround: python3 -m akf (always works)")
        click.echo()
        click.secho("  To fix permanently:", bold=True)
        system = platform.system()
        if system == "Darwin":
            click.echo('    Add to ~/.zshrc:')
            click.echo('      export PATH="$HOME/Library/Python/3.9/bin:$PATH"')
            click.echo()
            click.echo('    Or install with pipx (recommended):')
            click.echo('      pipx install akf')
        elif system == "Linux":
            click.echo('    Add to ~/.bashrc:')
            click.echo('      export PATH="$HOME/.local/bin:$PATH"')
            click.echo()
            click.echo('    Or install with pipx (recommended):')
            click.echo('      pipx install akf')
        else:
            click.echo('    Install with pipx (recommended):')
            click.echo('      pipx install akf')

    # Python version check
    click.echo()
    v = sys.version_info
    if v >= (3, 9):
        click.secho(f"  \u2705 Python {v.major}.{v.minor} is supported", fg="green")
    else:
        click.secho(f"  \u26a0\ufe0f  Python {v.major}.{v.minor} — AKF requires 3.9+", fg="yellow")

    click.echo()
    if akf_bin and v >= (3, 9):
        click.secho("  All good!", fg="green", bold=True)
    else:
        click.echo("  Fix the issues above and run 'akf doctor' again.")


@main.command("quickstart")
def quickstart_cmd():
    """See AKF in action in 30 seconds."""
    from .security import security_score

    # Step 1: Create
    click.secho("=== Step 1: Create ===", bold=True)
    unit = create_multi([
        {"content": "Revenue was $4.2B, up 12% YoY", "confidence": 0.98,
         "source": "SEC 10-Q Filing", "authority_tier": 1, "verified": True},
        {"content": "Cloud segment grew 15%", "confidence": 0.85,
         "source": "Gartner Report", "authority_tier": 2},
        {"content": "H2 outlook is positive", "confidence": 0.55,
         "source": "AI inference", "authority_tier": 5, "ai_generated": True,
         "risk": "Ungrounded AI projection"},
    ], author="demo@akf.dev", classification="internal")
    demo_path = Path("demo.akf")
    unit.save(str(demo_path))
    click.secho(f"Created {demo_path} with {len(unit.claims)} claims", fg="green")
    click.echo()

    # Step 2: Inspect
    click.secho("=== Step 2: Inspect ===", bold=True)
    for claim in unit.claims:
        if claim.confidence >= 0.8:
            icon = "\U0001f7e2"
        elif claim.confidence >= 0.5:
            icon = "\U0001f7e1"
        else:
            icon = "\U0001f534"

        parts = [f'{icon} {claim.confidence:.2f}  "{claim.content}"']
        if claim.source:
            parts.append(claim.source)
        if claim.authority_tier:
            parts.append(f"Tier {claim.authority_tier}")
        if claim.verified:
            parts.append(click.style("verified", fg="green"))
        if claim.ai_generated:
            parts.append(click.style("\u26a0 AI", fg="yellow"))
        click.echo("  " + "  ".join(parts))
    click.echo()

    # Step 3: Trust
    click.secho("=== Step 3: Trust ===", bold=True)
    results = compute_all(unit)
    for claim, result in zip(unit.claims, results):
        if result.decision == "ACCEPT":
            color = "green"
        elif result.decision == "LOW":
            color = "yellow"
        else:
            color = "red"
        click.secho(
            f"  {result.decision:6s}  {result.score:.4f}  \"{claim.content}\"",
            fg=color,
        )
    click.echo()

    # Step 4: Security
    click.secho("=== Step 4: Security ===", bold=True)
    sec = security_score(unit)
    color = "green" if sec.score >= 8 else "yellow" if sec.score >= 5 else "red"
    click.secho(f"  Security Score: {sec.score:.1f}/10 (Grade: {sec.grade})", fg=color, bold=True)
    for check in sec.checks:
        icon = "\u2705" if check["passed"] else "\u274c"
        click.echo(f"  {icon} {check['check']}")
    click.echo()

    # What's next
    click.secho("=== What's Next? ===", bold=True)
    click.echo("  akf embed report.docx          # Embed into Word/Excel")
    click.echo("  akf audit demo.akf             # Compliance check")
    click.echo("  akf report .                   # Governance report")
    click.echo()
    click.echo("  Learn more: https://akf.dev")


# ---------------------------------------------------------------------------
# Auto-tracking: install / uninstall / watch
# ---------------------------------------------------------------------------

@main.command("install")
@click.option("--system", is_flag=True, help="Install system-wide (requires privileges)")
@click.option("--no-daemon", is_flag=True, help="Skip background watcher daemon")
@click.option("--dirs", multiple=True, type=click.Path(), help="Directories to watch (default: ~/Downloads, ~/Desktop, ~/Documents)")
def install_cmd(system, no_daemon, dirs):
    """Activate auto-tracking and background file watcher.

    Drops a .pth file into site-packages so every Python process
    automatically patches LLM SDKs (OpenAI, Anthropic, Mistral, Google)
    to record model/provider metadata via AKF.

    Also installs a background daemon that watches common directories
    and auto-stamps new/modified files with AKF metadata.

    No code changes needed — just `akf install` once.
    """
    from ._auto import install as _install

    try:
        pth_path = _install(user=not system)
    except Exception as e:
        click.secho(f"Failed to install: {e}", fg="red")
        sys.exit(1)

    click.secho("AKF auto-tracking installed!", fg="green", bold=True)
    click.echo(f"  .pth file: {pth_path}")
    click.echo()

    if not no_daemon:
        from ._auto import install_service

        try:
            custom_dirs = list(dirs) if dirs else None
            result = install_service(dirs=custom_dirs)
            click.secho("Background watcher installed!", fg="green", bold=True)
            click.echo(f"  {result}")
        except Exception as e:
            click.secho(f"Warning: daemon install failed: {e}", fg="yellow")
            click.echo("  Auto-tracking is active, but background watcher could not start.")
            click.echo("  Use 'akf watch .' for foreground watching.")
        click.echo()

    click.echo("Every Python process will now auto-track LLM calls.")
    click.echo("Supported SDKs: OpenAI, Anthropic, Mistral, Google GenerativeAI.")
    if not no_daemon:
        click.echo()
        click.echo("Background watcher is monitoring your files.")
        click.echo("  Status:    akf watch --status")
        click.echo("  Stop:      akf watch --stop")
    click.echo()
    click.echo("To remove: akf uninstall")


@main.command("uninstall")
def uninstall_cmd():
    """Remove auto-tracking and background watcher (reverses `akf install`)."""
    from ._auto import uninstall as _uninstall, uninstall_service

    # Remove service first
    try:
        svc_result = uninstall_service()
        if svc_result:
            click.secho("Background watcher removed.", fg="green")
            click.echo(f"  {svc_result}")
    except Exception as e:
        click.secho(f"Warning: could not remove daemon: {e}", fg="yellow")

    # Remove .pth
    removed = _uninstall()
    if removed:
        click.secho("AKF auto-tracking removed.", fg="green")
        click.echo(f"  Removed: {removed}")
    else:
        click.secho("No auto-tracking installation found.", fg="yellow")

    # Clean up config/pid/log files
    akf_dir = Path.home() / ".akf"
    for name in ["watch.pid", "watch.log", "watch.log.1",
                 "watch-stdout.log", "watch-stderr.log"]:
        p = akf_dir / name
        if p.exists():
            p.unlink(missing_ok=True)


@main.command("shell-hook")
@click.option("--shell", type=click.Choice(["auto", "zsh", "bash"]),
              default="auto", help="Shell type (auto-detected by default)")
@click.option("--upload-hooks/--no-upload-hooks", default=True,
              help="Include content platform upload hooks (gws, box, m365, dbxcli, rclone)")
def shell_hook_cmd(shell, upload_hooks):
    """Output shell hook code for auto-stamping AI CLI output.

    Add to your shell profile to automatically stamp files created
    or modified by AI CLI tools (claude, chatgpt, aider, etc.).

    Also includes pre-upload stamping for content platform CLIs
    (gws, box, m365, dbxcli, obsidian-cli, rclone) so trust metadata
    travels with uploaded files. Disable with --no-upload-hooks.

    Examples:

        # Add to ~/.zshrc:
        eval "$(akf shell-hook)"

        # Or for bash, add to ~/.bashrc:
        eval "$(akf shell-hook --shell bash)"

        # Without upload hooks:
        eval "$(akf shell-hook --no-upload-hooks)"
    """
    from .shell_hook import generate_shell_hook

    click.echo(generate_shell_hook(shell, include_uploads=upload_hooks))


@main.command("uploads")
@click.option("--clear", is_flag=True, help="Clear the upload log")
@click.option("--json", "as_json", is_flag=True, help="Output as JSON")
def uploads_cmd(clear, as_json):
    """View or manage the AKF upload log.

    Shows files that were pre-stamped before upload to content
    platforms (Google Workspace, Box, M365, Dropbox, Rclone).

    Examples:

        akf uploads              # view upload log

        akf uploads --json       # machine-readable output

        akf uploads --clear      # reset the log
    """
    log_file = Path.home() / ".akf" / "upload.log"

    if clear:
        if log_file.exists():
            log_file.unlink()
            click.secho("Upload log cleared.", fg="green")
        else:
            click.secho("No upload log found.", fg="yellow")
        return

    if not log_file.exists() or log_file.stat().st_size == 0:
        click.secho("No uploads tracked yet.", fg="yellow")
        click.echo("  Upload hooks stamp files before upload to content platforms.")
        click.echo('  Enable with: eval "$(akf shell-hook)"')
        return

    lines = log_file.read_text().strip().splitlines()

    if as_json:
        entries = []
        for line in lines:
            parts = line.split(None, 4)
            if len(parts) >= 5:
                entries.append({
                    "timestamp": parts[0],
                    "tool": parts[1],
                    "action": parts[2],
                    "file": parts[3],
                    "status": parts[4],
                })
        click.echo(json.dumps(entries, indent=2))
        return

    # Pretty table output
    click.secho(f"┌─ AKF Upload Log {'─' * 43}┐", bold=True)
    click.secho(f"│  {len(lines)} upload(s) tracked{' ' * 40}│", bold=True)
    click.secho(f"└{'─' * 61}┘", bold=True)

    for line in lines:
        parts = line.split(None, 4)
        if len(parts) >= 5:
            ts, tool, _action, fname, status = parts
            # Format timestamp: remove seconds, replace T with space
            ts_short = ts[:16].replace("T", " ")
            click.echo(f"  {ts_short}  {tool:<12} {fname:<24} {status}")


@main.command("watch")
@click.argument("directories", nargs=-1, type=click.Path(exists=True))
@click.option("--agent", help="Agent ID for stamped metadata")
@click.option("--classification", default="internal", help="Classification label")
@click.option("--interval", default=5.0, type=float, help="Poll interval in seconds")
@click.option("--status", "show_status", is_flag=True, help="Show daemon status")
@click.option("--stop", "do_stop", is_flag=True, help="Stop the background daemon")
@click.option("--start", "do_start", is_flag=True, help="Start the background daemon")
def watch_cmd(directories, agent, classification, interval,
              show_status, do_stop, do_start):
    """Watch directories and auto-stamp new/modified files.

    Monitors directories for new or modified files and automatically
    stamps them with AKF trust metadata. Files that already have
    AKF metadata are skipped.

    Examples:

        akf watch .                          # foreground mode

        akf watch /tmp/output /tmp/reports   # watch multiple dirs

        akf watch --status                   # is daemon running?

        akf watch --stop                     # stop background daemon

        akf watch --start                    # start background daemon
    """
    if show_status:
        from ._auto import service_status
        status = service_status()
        if status["running"]:
            click.secho(f"Daemon running (PID {status['pid']})", fg="green", bold=True)
        else:
            click.secho("Daemon not running", fg="yellow", bold=True)
        if status["installed"]:
            click.echo(f"  Service: {status['service_file']}")
        else:
            click.echo("  Service not installed. Run 'akf install' to set up.")
        return

    if do_stop:
        from .daemon import stop_daemon
        if stop_daemon():
            click.secho("Daemon stopped.", fg="green")
        else:
            click.secho("No running daemon found.", fg="yellow")
        return

    if do_start:
        from .daemon import is_running, run_daemon
        if is_running():
            click.secho(f"Daemon already running (PID {is_running()})", fg="yellow")
            return
        # Start in background via double-fork
        click.echo("Starting daemon...")
        import subprocess
        subprocess.Popen(
            [sys.executable, "-m", "akf.daemon"],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        import time
        time.sleep(0.5)
        pid = is_running()
        if pid:
            click.secho(f"Daemon started (PID {pid})", fg="green")
        else:
            click.secho("Daemon may have failed to start. Check ~/.akf/watch.log", fg="yellow")
        return

    # Foreground mode
    from .watch import watch as _watch

    if not directories:
        directories = (".",)

    dirs_display = ", ".join(str(Path(d).resolve()) for d in directories)
    click.secho(f"Watching: {dirs_display}", fg="cyan", bold=True)
    click.echo(f"  Classification: {classification}")
    click.echo(f"  Interval: {interval}s")
    if agent:
        click.echo(f"  Agent: {agent}")
    click.echo()
    click.echo("Press Ctrl+C to stop.")
    click.echo()

    try:
        _watch(list(directories), agent=agent, classification=classification, interval=interval)
    except KeyboardInterrupt:
        click.echo()
        click.secho("Watcher stopped.", fg="yellow")


# ---------------------------------------------------------------------------
# certify
# ---------------------------------------------------------------------------


def _print_certify_summary(report) -> None:
    """Print a coloured summary of a CertifyReport."""
    click.echo()
    for r in report.results:
        icon = click.style("PASS", fg="green", bold=True) if r.certified else click.style("FAIL", fg="red", bold=True)
        score = f"{r.trust_score:.2f}"
        click.echo(f"  {icon}  {r.filepath}  (trust={score})")
        if r.error:
            click.secho(f"         error: {r.error}", fg="yellow")
        for d in r.detections:
            click.secho(f"         detection: [{d.severity}] {d.detection_class}", fg="red")
        for c in r.compliance_issues:
            click.secho(f"         compliance: {c}", fg="yellow")

    click.echo()
    click.echo(f"  Total: {report.total_files}  Certified: {report.certified_count}  "
               f"Failed: {report.failed_count}  Skipped: {report.skipped_count}")
    if report.avg_trust:
        click.echo(f"  Average trust: {report.avg_trust:.4f}")
    click.echo()
    if report.all_certified:
        click.secho("  All files certified.", fg="green", bold=True)
    else:
        click.secho("  Certification incomplete.", fg="red", bold=True)


def _print_certify_markdown(report) -> None:
    """Print a Markdown table of certification results."""
    click.echo("| File | Status | Trust | Issues |")
    click.echo("|------|--------|-------|--------|")
    for r in report.results:
        status = "PASS" if r.certified else "FAIL"
        issues = []
        if r.error:
            issues.append(r.error)
        issues.extend(d.detection_class for d in r.detections)
        issues.extend(r.compliance_issues)
        issues_str = ", ".join(issues) if issues else "-"
        click.echo(f"| {r.filepath} | {status} | {r.trust_score:.2f} | {issues_str} |")
    click.echo()
    click.echo(f"**Total:** {report.total_files} | "
               f"**Certified:** {report.certified_count} | "
               f"**Failed:** {report.failed_count} | "
               f"**Skipped:** {report.skipped_count}")


def _print_team_certify_summary(team_report) -> None:
    """Print a coloured summary of a TeamCertifyReport."""
    click.echo()
    click.secho(f"  Team: {team_report.team_id}", bold=True)
    click.echo()

    for agent_id, ar in sorted(team_report.agent_reports.items()):
        icon = click.style("PASS", fg="green") if ar.failed_count == 0 else click.style("FAIL", fg="red")
        click.echo(f"    {icon}  {agent_id}  "
                   f"({ar.certified_count}/{ar.file_count} certified, trust={ar.avg_trust:.4f})")

    click.echo()
    click.echo(f"  Total: {team_report.total_files}  Certified: {team_report.certified_count}  "
               f"Failed: {team_report.failed_count}")
    if team_report.avg_trust:
        click.echo(f"  Average trust: {team_report.avg_trust:.4f}")
    click.echo()
    if team_report.all_agents_certified:
        click.secho("  All agents certified.", fg="green", bold=True)
    else:
        click.secho("  Team certification incomplete.", fg="red", bold=True)


@main.command("certify")
@click.argument("path", type=click.Path(exists=True))
@click.option("--min-trust", type=float, default=0.7, help="Minimum trust score to certify (default: 0.7)")
@click.option("--evidence-file", type=click.Path(exists=True), help="Path to JUnit XML or JSON evidence file")
@click.option("--format", "fmt", type=click.Choice(["summary", "json", "markdown"]), default="summary",
              help="Output format")
@click.option("--fail-on-untrusted", is_flag=True, help="Exit with code 1 if any file fails certification")
@click.option("--agent", default=None, help="Agent identifier for provenance")
@click.option("--team", is_flag=True, help="Show per-agent breakdown (team mode)")
def certify_cmd(path, min_trust, evidence_file, fmt, fail_on_untrusted, agent, team) -> None:
    """Certify files meet trust standards.

    Aggregates trust scoring, detection, and compliance into a pass/fail verdict.
    Accepts a single file or a directory.
    """
    from .certify import (
        CertifyReport,
        certify_directory,
        certify_file,
        certify_team,
        parse_evidence_json,
        parse_junit_xml,
    )

    # Load external evidence if provided
    evidence = None
    if evidence_file:
        if evidence_file.endswith(".xml"):
            evidence = parse_junit_xml(evidence_file)
        else:
            evidence = parse_evidence_json(evidence_file)

    p = Path(path)

    # Team mode
    if team and p.is_dir():
        team_report = certify_team(str(p), min_trust=min_trust, evidence=evidence)

        import json as _json

        if fmt == "json":
            click.echo(_json.dumps(team_report.to_dict(), indent=2))
        else:
            _print_team_certify_summary(team_report)

        if fail_on_untrusted and not team_report.all_agents_certified:
            sys.exit(1)
        return

    if p.is_dir():
        report = certify_directory(str(p), min_trust=min_trust, evidence=evidence)
    else:
        result = certify_file(str(p), min_trust=min_trust, evidence=evidence)
        report = CertifyReport(
            total_files=1,
            certified_count=1 if result.certified else 0,
            failed_count=0 if result.certified else 1,
            skipped_count=0,
            avg_trust=result.trust_score,
            results=[result],
        )

    # Output
    import json as _json

    if fmt == "json":
        click.echo(_json.dumps(report.to_dict(), indent=2))
    elif fmt == "markdown":
        _print_certify_markdown(report)
    else:
        _print_certify_summary(report)

    if fail_on_untrusted and not report.all_certified:
        sys.exit(1)


@main.command("log")
@click.option("--count", default=10, type=int, help="Number of commits to show (default: 10)")
@click.option("--trust", "trust_only", is_flag=True, help="Show only trust-annotated commits")
def log_cmd(count, trust_only) -> None:
    """Show trust-annotated git history.

    Displays recent commits with AKF trust indicators based on git notes.
    """
    import subprocess

    # Get recent commits
    try:
        result = subprocess.run(
            ["git", "log", f"--format=%H %s", "-n", str(count)],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        click.secho("Error: not a git repository or git is not installed.", fg="red")
        sys.exit(1)

    lines = result.stdout.strip().splitlines()
    if not lines:
        click.secho("No commits found.", fg="yellow")
        return

    for line in lines:
        if not line.strip():
            continue
        sha, _, subject = line.partition(" ")
        short_sha = sha[:7]

        # Try to read AKF git note
        trust_score = None
        try:
            note_result = subprocess.run(
                ["git", "notes", "--ref=akf", "show", sha],
                capture_output=True,
                text=True,
                check=True,
            )
            note_data = json.loads(note_result.stdout.strip())
            # Look for trust score in common locations
            trust_score = note_data.get("trust") or note_data.get("trust_score")
            if trust_score is None and "claims" in note_data:
                claims = note_data["claims"]
                if claims:
                    scores = [c.get("t", c.get("trust", 0)) for c in claims]
                    trust_score = sum(scores) / len(scores) if scores else None
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
            trust_score = None

        # Filter if --trust flag is set
        if trust_only and trust_score is None:
            continue

        # Format output
        if trust_score is not None:
            if trust_score >= 0.7:
                indicator = click.style("+ ACCEPT", fg="green")
            elif trust_score >= 0.4:
                indicator = click.style("~ LOW   ", fg="yellow")
            else:
                indicator = click.style("- REJECT", fg="red")
            click.echo(f"{indicator}  {trust_score:.2f}  {short_sha}  {subject}")
        else:
            indicator = click.style("? none  ", dim=True)
            click.echo(f"{indicator}        {short_sha}  {subject}")


# ---------------------------------------------------------------------------
# Agent identity commands
# ---------------------------------------------------------------------------

@main.group("agent")
def agent_group() -> None:
    """Agent identity management commands."""
    pass


@agent_group.command("create")
@click.option("--name", required=True, help="Agent display name")
@click.option("--platform", default=None, help="Platform (e.g. claude-code, copilot)")
@click.option("--capabilities", default=None, help="Comma-separated capabilities")
@click.option("--trust-ceiling", type=float, default=None, help="Max trust score 0.0-1.0")
@click.option("--model", default=None, help="AI model identifier")
@click.option("--version", default=None, help="Agent version")
@click.option("--provider", default=None, help="Provider name")
@click.option("--register/--no-register", default=True, help="Auto-register in .akf/agents.json")
def agent_create_cmd(name, platform, capabilities, trust_ceiling, model, version, provider, register) -> None:
    """Create a new agent identity card."""
    from .agent_card import AgentRegistry, create_agent_card

    caps = [c.strip() for c in capabilities.split(",")] if capabilities else None
    card = create_agent_card(
        name=name,
        platform=platform,
        capabilities=caps,
        trust_ceiling=trust_ceiling,
        model=model,
        version=version,
        provider=provider,
    )

    if register:
        registry = AgentRegistry()
        registry.register(card)
        click.secho(f"Registered agent: {card.id}", fg="green")
    else:
        click.secho(f"Created agent: {card.id}", fg="green")

    click.echo(f"  Name:     {card.name}")
    if card.platform:
        click.echo(f"  Platform: {card.platform}")
    if card.capabilities:
        click.echo(f"  Caps:     {', '.join(card.capabilities)}")
    if card.trust_ceiling is not None:
        click.echo(f"  Ceiling:  {card.trust_ceiling}")
    if card.model:
        click.echo(f"  Model:    {card.model}")
    click.echo(f"  Hash:     {card.card_hash}")


@agent_group.command("list")
def agent_list_cmd() -> None:
    """List all registered agent cards."""
    from .agent_card import AgentRegistry

    registry = AgentRegistry()
    cards = registry.list()
    if not cards:
        click.echo("No agents registered. Use 'akf agent create --name <name>' to add one.")
        return

    click.secho(f"Registered agents ({len(cards)}):", bold=True)
    for card in cards:
        plat = f" [{card.platform}]" if card.platform else ""
        ceil = f" ceil={card.trust_ceiling}" if card.trust_ceiling is not None else ""
        click.echo(f"  {card.id[:12]}..  {card.name}{plat}{ceil}")


@agent_group.command("verify")
@click.argument("agent_id")
def agent_verify_cmd(agent_id) -> None:
    """Verify the integrity of an agent card."""
    from .agent_card import AgentRegistry, verify_agent_card

    registry = AgentRegistry()
    card = registry.get(agent_id)
    if card is None:
        click.secho(f"Agent not found: {agent_id}", fg="red")
        sys.exit(1)

    if verify_agent_card(card):
        click.secho(f"PASS  Agent card {card.name} ({agent_id}) is valid.", fg="green")
    else:
        click.secho(f"FAIL  Agent card {card.name} ({agent_id}) has been tampered with!", fg="red")
        sys.exit(1)


@agent_group.command("export-a2a")
@click.argument("agent_id")
@click.option("--output", default=None, help="Output file path (default: .akf/agent-cards/<id>.json)")
def agent_export_a2a_cmd(agent_id, output) -> None:
    """Export an agent card as A2A-compatible JSON."""
    from .a2a_bridge import save_a2a_card
    from .agent_card import AgentRegistry

    registry = AgentRegistry()
    card = registry.get(agent_id)
    if card is None:
        click.secho(f"Agent not found: {agent_id}", fg="red")
        sys.exit(1)

    path = save_a2a_card(card, path=output)
    click.secho(f"Exported A2A card to {path}", fg="green")


@agent_group.command("import-a2a")
@click.argument("card_path", type=click.Path(exists=True))
def agent_import_a2a_cmd(card_path) -> None:
    """Import an A2A agent card and register it."""
    import json as _json

    from .a2a_bridge import from_a2a_card
    from .agent_card import AgentRegistry

    with open(card_path) as f:
        data = _json.load(f)

    card = from_a2a_card(data)
    registry = AgentRegistry()
    registry.register(card)
    click.secho(f"Imported agent: {card.name} ({card.id})", fg="green")


@main.command("completion")
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
def completion_cmd(shell) -> None:
    """Generate shell completion script.

    Install completions by adding the output to your shell profile:

    \b
      akf completion bash >> ~/.bashrc
      akf completion zsh >> ~/.zshrc
      akf completion fish > ~/.config/fish/completions/akf.fish
    """
    from click.shell_completion import get_completion_class

    comp_cls = get_completion_class(shell)
    if comp_cls is None:
        click.secho(f"Unsupported shell: {shell}", fg="red")
        sys.exit(1)

    comp = comp_cls(main, {}, "akf", "_AKF_COMPLETE")
    click.echo(comp.source())
