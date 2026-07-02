---
akf:
  v: "1.0"
  claims:
    - c: "Trust metadata for docs/recipes/skill-provenance.md"
      t: 0.7
      id: a21eb0c4
      src: unspecified
      tier: 5
      ver: false
      ai: true
      evidence:
        - type: other
          detail: examples verified against shipped CLI behavior
          at: "2026-07-02T17:06:46.734585+00:00"
  id: "akf-8f690dcfa95f"
  agent: "claude-code"
  at: "2026-07-02T17:06:46.734803+00:00"
  label: public
  inherit: true
  ext: false
  hash: "sha256:c09b80e6b731a097"
  sv: "1.1"
---
# Recipe: Skill Supply-Chain Provenance

Agents install skills and plugins from marketplaces — often automatically,
often without review. The skill ecosystem has already had its first malware
wave. A skill file is executable *instruction*, and today nothing tells an
agent (or its human) who published it, when, or whether anyone verified it.

AKF stamps embed in Markdown natively (YAML frontmatter), so a skill file can
carry its own provenance.

## Publishing a skill

Stamp before you publish:

```bash
akf stamp skills/my-skill.md --preset skill \
    --agent "acme-tools" \
    --claim "Skill published by Acme Tools: converts CSV to trust reports" \
    --evidence "reviewed by @maintainer"
```

The `skill` preset sets: `public` classification, 365-day trust half-life,
and authority tier 3 (unverified third party). Human review evidence raises
effective trust; a signed stamp raises it further:

```bash
akf keygen                       # once
akf sign skills/my-skill.md      # Ed25519 signature travels in the stamp
```

## Installing a skill

Check before your agent loads it:

```bash
akf check skills/downloaded-skill.md
# OK trust=0.78 agent=acme-tools evidence=human_review age=12d
#   → published, reviewed, unmodified since stamping

# UNSTAMPED reason=no_metadata
#   → no provenance at all; read it yourself before letting an agent load it

# STALE reason=modified_after_stamp
#   → the file changed after the publisher stamped it. Diff before trusting.
```

`STALE` is the supply-chain signal: it means the skill on disk is not the
skill that was stamped — whether by a legitimate update or a tampered
download.

## Rules stanza for your agent

```markdown
## Skill trust
- Never load a skill file without `akf check` first.
- UNSTAMPED or STALE skills require human review before use.
- When you author or modify a skill: `akf stamp <file> --preset skill --agent <your-id>`.
```

## Verifying a whole skills directory

```bash
akf scan skills/ --recursive     # trust report for every file
akf certify skills/ --min-trust 0.6
```

## A worked example

This repository dogfoods the recipe: [`skills/openclaw-akf/SKILL.md`](../../skills/openclaw-akf/SKILL.md)
carries an AKF stamp in its frontmatter. Run `akf check` on it.
