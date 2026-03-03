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


@click.group()
@click.version_option(version="1.0.0", prog_name="akf")
def main() -> None:
    """AKF — Agent Knowledge Format CLI."""
    pass


@main.command("create")
@click.argument("file", type=click.Path())
@click.option("--claim", "-c", multiple=True, required=True, help="Claim content")
@click.option("--trust", "-t", multiple=True, required=True, type=float, help="Trust score (0-1)")
@click.option("--src", "-s", multiple=True, help="Source for each claim")
@click.option("--tier", multiple=True, type=int, help="Authority tier (1-5)")
@click.option("--ver", is_flag=True, help="Mark claims as verified")
@click.option("--ai", is_flag=True, help="Mark claims as AI-generated")
@click.option("--by", "author", help="Author email or ID")
@click.option("--label", "classification", help="Security classification")
@click.option("--agent", "agent_id", help="AI agent ID")
def create_cmd(file, claim, trust, src, tier, ver, ai, author, classification, agent_id) -> None:
    """Create a new .akf file with specified claims."""
    if len(claim) != len(trust):
        click.secho("Error: Number of --claim and --trust must match", fg="red")
        sys.exit(1)

    claims = []
    for i, (c, t) in enumerate(zip(claim, trust)):
        kwargs: dict = {}
        if src and i < len(src):
            kwargs["src"] = src[i]
        if tier and i < len(tier):
            kwargs["tier"] = tier[i]
        if ver:
            kwargs["ver"] = True
        if ai:
            kwargs["ai"] = True
        claims.append({"c": c, "t": t, **kwargs})

    envelope: dict = {}
    if author:
        envelope["by"] = author
    if classification:
        envelope["label"] = classification
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
        label_str = unit.label or "none"
        hash_str = "\u2713 integrity" if unit.hash else "no hash"
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

    click.secho(f"AKF {unit.v} | {unit.id}", bold=True)
    if unit.by:
        click.echo(f"  by: {unit.by}")
    if unit.label:
        click.echo(f"  label: {unit.label}")
    click.echo(f"  claims: {len(unit.claims)}")
    click.echo()

    for claim in unit.claims:
        if claim.t >= 0.8:
            color = "green"
            icon = "\U0001f7e2"
        elif claim.t >= 0.5:
            color = "yellow"
            icon = "\U0001f7e1"
        else:
            color = "red"
            icon = "\U0001f534"

        tier_str = f"Tier {claim.tier}" if claim.tier else ""
        src_str = claim.src or ""
        parts = [f'{icon} {claim.t:.2f}  "{claim.c}"']
        if src_str:
            parts.append(src_str)
        if tier_str:
            parts.append(tier_str)
        if claim.ver:
            parts.append(click.style("verified", fg="green"))
        if claim.ai:
            parts.append(click.style("\u26a0 AI", fg="yellow"))
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

        click.secho(
            f"  {result.decision:6s}  {result.score:.4f}  \"{claim.c}\"  "
            f"(t={claim.t}, tier={claim.tier or 3}, auth={result.breakdown['authority']})",
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
                click.echo(json.dumps(hop.model_dump(by_alias=True), indent=2))


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
        kwargs: dict = {"ai": True}
        if risk and i < len(risk):
            kwargs["risk"] = risk[i]
        new_claim = Claim(c=c, t=t, **kwargs)
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
@click.argument("file", type=click.Path(exists=True))
@click.option("--output", "-o", required=True, type=click.Path(), help="Output .akf file")
def convert_cmd(file, output) -> None:
    """Extract AKF metadata from any format into standalone .akf."""
    from . import universal as akf_u

    akf_u.to_akf(file, output)
    click.secho("Converted {} -> {}".format(file, output), fg="green")


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
            click.secho(f"    + [{cid}] \"{claim.c}\" (t={claim.t})", fg="green")

    if removed:
        click.secho(f"  - Removed: {len(removed)} claims", fg="red")
        for cid in removed:
            claim = next(c for c in u1.claims if c.id == cid)
            click.secho(f"    - [{cid}] \"{claim.c}\" (t={claim.t})", fg="red")

    # Trust changes in common claims
    for cid in common:
        c1 = next(c for c in u1.claims if c.id == cid)
        c2 = next(c for c in u2.claims if c.id == cid)
        if c1.t != c2.t:
            delta = c2.t - c1.t
            color = "green" if delta > 0 else "red"
            click.secho(f"  ~ [{cid}] trust {c1.t} -> {c2.t} ({delta:+.4f})", fg=color)

    # Label change
    if u1.label != u2.label:
        click.echo(f"  Label: {u1.label or 'none'} -> {u2.label or 'none'}")

    # Provenance
    p1 = len(u1.prov) if u1.prov else 0
    p2 = len(u2.prov) if u2.prov else 0
    if p1 != p2:
        click.echo(f"  Provenance hops: {p1} -> {p2}")
