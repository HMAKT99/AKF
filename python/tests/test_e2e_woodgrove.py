"""
End-to-End Test: Woodgrove Bank Q3 Earnings Analysis
=====================================================

This test walks through the complete hackathon demo scenario:
  Sarah (analyst) -> Copilot (AI enrichment) -> Review -> Agent consumption

It validates the full AKF lifecycle: create, enrich, review, classify,
share control, transform, and provenance auditing.
"""

import json
import os
import tempfile
import pytest
from akf.builder import AKFBuilder
from akf.core import create_multi, load, validate
from akf.models import AKF, Claim
from akf.provenance import add_hop, compute_integrity_hash, format_tree, validate_chain
from akf.security import can_share_external, validate_inheritance
from akf.transform import AKFTransformer
from akf.trust import compute_all, effective_trust


class TestWoodgroveE2E:
    def test_full_scenario(self):
        # ============================================================
        # STEP 1: Sarah creates Q3-Analysis.akf with 3 initial claims
        # ============================================================
        q3_analysis = (
            AKFBuilder()
            .by("sarah@woodgrove.com")
            .label("confidential")
            .inherit(True)
            .claim(
                "Woodgrove Q3 revenue was $4.2B, up 12% YoY",
                0.98,
                source="SEC 10-Q Filing",
                authority_tier=1,
                verified=True,
                verified_by="sarah@woodgrove.com",
            )
            .tag("revenue", "Q3")
            .claim(
                "Cloud segment grew 15-18% driven by AI workloads",
                0.85,
                source="Gartner Cloud Report 2025",
                authority_tier=2,
            )
            .tag("cloud", "growth")
            .claim(
                "Enterprise pipeline is strong with 3 deals over $50M",
                0.72,
                source="Internal CRM estimate",
                authority_tier=4,
            )
            .tag("pipeline")
            .build()
        )

        # Verify initial state
        assert q3_analysis.version == "1.0"
        assert q3_analysis.author == "sarah@woodgrove.com"
        assert q3_analysis.classification == "confidential"
        assert q3_analysis.inherit_classification is True
        assert len(q3_analysis.claims) == 3
        assert q3_analysis.claims[0].confidence == 0.98
        assert q3_analysis.claims[0].verified is True

        # Verify initial provenance (hop 0: created)
        assert q3_analysis.prov is not None
        assert len(q3_analysis.prov) == 1
        assert q3_analysis.prov[0].actor == "sarah@woodgrove.com"
        assert q3_analysis.prov[0].action == "created"

        # Verify initial validation
        result = validate(q3_analysis)
        assert result.valid, "Step 1 validation failed: {}".format(result.errors)

        sarah_claim_ids = [c.id for c in q3_analysis.claims]

        # ============================================================
        # STEP 2: Copilot enriches with 2 AI claims
        # ============================================================
        copilot_claim_1 = Claim(
            content="AI copilot adoption rate is 34% across Fortune 500",
            confidence=0.78,
            source="McKinsey AI Survey 2025",
            authority_tier=2,
            ai_generated=True,
            tags=["AI", "adoption"],
        )

        copilot_claim_2 = Claim(
            content="H2 revenue will accelerate to 25% growth based on pipeline momentum",
            confidence=0.63,
            source="Copilot inference from Q1-Q3 trend",
            authority_tier=5,
            ai_generated=True,
            risk="AI inference — extrapolated from limited data points. Not supported by analyst consensus.",
            tags=["forecast", "AI-generated"],
        )

        # Add Copilot's claims to the unit
        enriched_claims = list(q3_analysis.claims) + [copilot_claim_1, copilot_claim_2]
        enriched = q3_analysis.model_copy(update={"claims": enriched_claims})

        # Add provenance hop for Copilot's enrichment
        copilot_claim_ids = [copilot_claim_1.id, copilot_claim_2.id]
        enriched = add_hop(
            enriched,
            by="copilot-m365",
            action="enriched",
            adds=copilot_claim_ids,
        )

        # Verify enrichment
        assert len(enriched.claims) == 5
        assert len(enriched.prov) == 2
        assert enriched.prov[1].actor == "copilot-m365"
        assert enriched.prov[1].action == "enriched"

        ai_claims = [c for c in enriched.claims if c.ai_generated]
        assert len(ai_claims) == 2

        # The flagged claim should have a risk description
        flagged = [c for c in enriched.claims if c.risk]
        assert len(flagged) == 1
        assert "inference" in flagged[0].risk.lower()

        # ============================================================
        # STEP 3: Sarah reviews — confirms 1, rejects 1, adds 1
        # ============================================================
        rejected_id = copilot_claim_2.id

        # Remove the rejected claim
        reviewed_claims = [c for c in enriched.claims if c.id != rejected_id]

        # Sarah adds her own claim
        sarah_new_claim = Claim(
            content="Key competitor Contoso lost 2 enterprise accounts to Woodgrove in Q3",
            confidence=0.80,
            source="Sales team debrief",
            authority_tier=3,
            verified=True,
            verified_by="sarah@woodgrove.com",
            tags=["competitive"],
        )
        reviewed_claims.append(sarah_new_claim)

        # Update the unit
        reviewed = enriched.model_copy(update={"claims": reviewed_claims})

        # Add review provenance hop
        reviewed = add_hop(
            reviewed,
            by="sarah@woodgrove.com",
            action="reviewed",
            adds=[sarah_new_claim.id],
            drops=[rejected_id],
        )

        # Verify review
        assert len(reviewed.claims) == 5  # 3 original + 1 AI confirmed + 1 new
        assert len(reviewed.prov) == 3  # created, enriched, reviewed

        # The rejected claim should be gone
        remaining_ids = {c.id for c in reviewed.claims}
        assert rejected_id not in remaining_ids

        # The new claim should be present
        assert sarah_new_claim.id in remaining_ids

        # Review provenance should track adds and drops
        review_hop = reviewed.prov[2]
        assert review_hop.actor == "sarah@woodgrove.com"
        assert review_hop.action == "reviewed"
        assert sarah_new_claim.id in review_hop.claims_added
        assert rejected_id in review_hop.claims_removed

        # ============================================================
        # STEP 4: Validate classification inheritance
        # ============================================================
        assert reviewed.classification == "confidential"
        assert reviewed.inherit_classification is True

        # A public child should be REJECTED
        public_child = AKF(
            version="1.0",
            claims=[Claim(content="public leak", confidence=0.5)],
            classification="public",
        )
        assert validate_inheritance(reviewed, public_child) is False

        # A confidential child should be ACCEPTED
        confidential_child = AKF(
            version="1.0",
            claims=[Claim(content="ok", confidence=0.5)],
            classification="confidential",
        )
        assert validate_inheritance(reviewed, confidential_child) is True

        # A restricted child should be ACCEPTED (higher is fine)
        restricted_child = AKF(
            version="1.0",
            claims=[Claim(content="ok", confidence=0.5)],
            classification="restricted",
        )
        assert validate_inheritance(reviewed, restricted_child) is True

        # ============================================================
        # STEP 5: Simulate external share — Purview blocks
        # ============================================================
        assert can_share_external(reviewed) is False

        ai_claims_present = any(c.ai_generated for c in reviewed.claims)
        assert ai_claims_present

        # ============================================================
        # STEP 6: Research agent consumes -> Weekly-Brief.akf
        # ============================================================
        weekly_brief = (
            AKFTransformer(reviewed)
            .filter(trust_min=0.5)
            .penalty(-0.03)
            .by("research-agent")
            .build()
        )

        assert len(weekly_brief.claims) > 0
        assert len(weekly_brief.claims) < len(reviewed.claims)

        # Classification should be inherited
        assert weekly_brief.classification == "confidential"
        assert validate_inheritance(reviewed, weekly_brief) is True

        # Provenance should extend the chain
        assert len(weekly_brief.prov) == len(reviewed.prov) + 1
        agent_hop = weekly_brief.prov[-1]
        assert agent_hop.actor == "research-agent"
        assert agent_hop.action == "consumed"

        # Parent reference should exist
        assert weekly_brief.meta["parent_id"] == reviewed.id

        # Trust scores should be reduced by penalty
        for claim in weekly_brief.claims:
            original = next(c for c in reviewed.claims if c.id == claim.id)
            assert claim.confidence == pytest.approx(original.confidence - 0.03, abs=0.001)

        # Brief should validate
        brief_result = validate(weekly_brief)
        assert brief_result.valid, "Brief validation failed: {}".format(brief_result.errors)

        # ============================================================
        # STEP 7: Validate provenance chain across all hops
        # ============================================================
        assert validate_chain(weekly_brief.prov) is True

        chain = weekly_brief.prov
        assert chain[0].action == "created"
        assert chain[1].action == "enriched"
        assert chain[2].action == "reviewed"
        assert chain[3].action == "consumed"

        assert chain[0].actor == "sarah@woodgrove.com"
        assert chain[1].actor == "copilot-m365"
        assert chain[2].actor == "sarah@woodgrove.com"
        assert chain[3].actor == "research-agent"

        # Pretty-print the provenance tree
        tree = format_tree(weekly_brief)
        assert "sarah@woodgrove.com" in tree
        assert "copilot-m365" in tree
        assert "research-agent" in tree

        # ============================================================
        # STEP 8: Validate integrity hashes
        # ============================================================
        assert reviewed.integrity_hash is not None
        assert reviewed.integrity_hash.startswith("sha256:")

        assert weekly_brief.integrity_hash is not None
        assert weekly_brief.integrity_hash.startswith("sha256:")

        assert reviewed.integrity_hash != weekly_brief.integrity_hash

        recomputed = compute_integrity_hash(weekly_brief)
        assert recomputed == weekly_brief.integrity_hash

        tampered = weekly_brief.model_copy(
            update={"claims": [Claim(content="tampered!", confidence=0.01)]}
        )
        tampered_hash = compute_integrity_hash(tampered)
        assert tampered_hash != weekly_brief.integrity_hash

        # ============================================================
        # STEP 9: Round-trip file save/load
        # ============================================================
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False) as f:
            path = f.name
        try:
            weekly_brief.save(path)
            reloaded = load(path)

            assert reloaded.id == weekly_brief.id
            assert reloaded.classification == weekly_brief.classification
            assert len(reloaded.claims) == len(weekly_brief.claims)
            assert len(reloaded.prov) == len(weekly_brief.prov)

            for orig, loaded in zip(weekly_brief.claims, reloaded.claims):
                assert orig.content == loaded.content
                assert orig.confidence == loaded.confidence

            # Verify no null fields in saved file
            with open(path) as f:
                raw = json.load(f)

            def assert_no_nulls(obj, path=""):
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        assert v is not None, "Null at {}.{}".format(path, k)
                        assert_no_nulls(v, "{}.{}".format(path, k))
                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        assert_no_nulls(item, "{}[{}]".format(path, i))

            assert_no_nulls(raw)
        finally:
            os.unlink(path)
