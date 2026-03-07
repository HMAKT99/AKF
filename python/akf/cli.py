"""AKF v1.0 — Command-line interface."""

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
@click.version_option(version="1.1.0", prog_name="akf")
@click.pass_context
def main(ctx) -> None:
    """AKF — Agent Knowledge Format CLI."""
    if ctx.invoked_subcommand is None:
        click.secho("AKF — Agent Knowledge Format v1.0", bold=True)
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


@main.command("scan")
@click.argument("file_or_dir", type=click.Path(exists=True))
@click.option("--recursive", "-r", is_flag=True, help="Scan directories recursively")
def scan_cmd(file_or_dir, recursive) -> None:
    """Security scan any file or directory for AKF metadata."""
    from . import universal as akf_u
    from pathlib import Path

    target = Path(file_or_dir)
    if target.is_dir():
        reports = akf_u.scan_directory(str(target), recursive=recursive)
        enriched = [r for r in reports if r.enriched]
        click.secho("Scanned {} files, {} AKF-enriched".format(len(reports), len(enriched)), bold=True)
        for r in reports:
            if r.enriched:
                ai_str = " [AI: {:.0f}%]".format(r.ai_contribution * 100) if r.ai_contribution else ""
                trust_str = " trust: {:.2f}".format(r.overall_trust) if r.overall_trust else ""
                label_str = " ({})".format(r.classification) if r.classification else ""
                click.secho("  {} — {} claims{}{}{}".format(
                    r.format, r.claim_count, trust_str, ai_str, label_str), fg="green")
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
@click.argument("file", type=click.Path(exists=True))
@click.option("--regulation", "-r", help="Check specific regulation (eu_ai_act, sox, hipaa, gdpr, nist_ai, iso_42001)")
@click.option("--trail", is_flag=True, help="Show audit trail")
@click.option("--export", "export_fmt", type=click.Choice(["json", "markdown", "csv"]), help="Export audit result")
def audit_cmd(file, regulation, trail, export_fmt) -> None:
    """Run compliance audit on an .akf file."""
    from .compliance import audit, check_regulation, audit_trail, export_audit

    if trail:
        try:
            click.echo(audit_trail(file, format="text"))
        except (ValueError, json.JSONDecodeError) as e:
            click.secho(f"Error: {e}", fg="red")
            sys.exit(1)
        return

    try:
        if regulation:
            result = check_regulation(file, regulation)
        else:
            result = audit(file)
    except (ValueError, json.JSONDecodeError) as e:
        click.secho(f"Error: Could not audit {file}: {e}", fg="red")
        click.echo(f"  Tip: Run 'akf embed {file}' or 'akf stamp {file}' to add metadata first")
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
@click.option("--label", default=None, help="Classification label")
@click.option("--format", "fmt", default="auto", help="Output format: auto, embed, sidecar")
def stamp_cmd(file, label, fmt):
    """Add AKF trust metadata to any file.

    Stamps the file with trust scores, provenance, and classification.
    The file remains openable in its native application.
    """
    from . import universal as akf_u

    meta = akf_u.extract(file)
    claims_count = 0
    avg_trust = 0.0
    classification = label or "internal"

    if meta:
        claims = meta.get("claims", [])
        claims_count = len(claims)
        if claims_count > 0:
            avg_trust = sum(
                c.get("confidence", c.get("t", 0)) for c in claims
            ) / claims_count
        classification = label or meta.get("classification") or meta.get("label") or "internal"

    metadata = {}
    if label:
        metadata["classification"] = label

    if fmt == "sidecar":
        from . import sidecar
        sidecar.create(file, metadata)
    else:
        akf_u.embed(file, metadata=metadata if metadata else None,
                    classification=label)

    click.echo(
        f"\u2713 Stamped {file} ({claims_count} claims, avg trust: {avg_trust:.2f}, label: {classification})"
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
