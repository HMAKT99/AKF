"""Tests for v1.1 new models: Origin, Review, SourceDetail, ReasoningChain,
Annotation, Freshness, CostMetadata, AgentProfile, GenerationParams, MadeBy.
"""

import pytest
from akf.models import (
    AKF, Claim, Origin, GenerationParams, MadeBy, Review,
    SourceDetail, ReasoningChain, Annotation, Freshness,
    CostMetadata, AgentProfile,
)


class TestOrigin:
    def test_basic_creation(self):
        o = Origin(type="ai", model="claude-opus-4-6", provider="anthropic")
        assert o.type == "ai"
        assert o.model == "claude-opus-4-6"
        assert o.provider == "anthropic"

    def test_all_types(self):
        for t in ("human", "ai", "human_assisted_by_ai", "ai_supervised_by_human", "ai_chain"):
            o = Origin(type=t)
            assert o.type == t

    def test_with_generation_params(self):
        params = GenerationParams(temperature=0.7, top_p=0.9, max_tokens=1000)
        o = Origin(type="ai", parameters=params)
        assert o.parameters.temperature == 0.7
        assert o.parameters.max_tokens == 1000

    def test_compact_serialization(self):
        o = Origin(type="ai", model="gpt-4", version="2024-01")
        d = o.to_dict(compact=True)
        assert d["type"] == "ai"
        assert d["model"] == "gpt-4"
        assert d["ver"] == "2024-01"

    def test_round_trip(self):
        o = Origin(type="ai_supervised_by_human", model="claude", provider="anthropic")
        d = o.to_dict(compact=False)
        o2 = Origin(**d)
        assert o2.type == o.type
        assert o2.model == o.model


class TestGenerationParams:
    def test_basic(self):
        p = GenerationParams(temperature=0.5, max_tokens=2000)
        assert p.temperature == 0.5
        assert p.max_tokens == 2000

    def test_compact_alias(self):
        p = GenerationParams(**{"temp": 0.3, "max_tok": 500})
        assert p.temperature == 0.3
        assert p.max_tokens == 500

    def test_tool_names(self):
        p = GenerationParams(tool_names=["search", "calculator"])
        assert p.tool_names == ["search", "calculator"]


class TestMadeBy:
    def test_basic(self):
        m = MadeBy(actor="user@example.com", role="author")
        assert m.actor == "user@example.com"
        assert m.role == "author"

    def test_compact_alias(self):
        m = MadeBy(**{"by": "agent-1", "role": "reviewer"})
        assert m.actor == "agent-1"
        assert m.role == "reviewer"

    def test_compact_serialization(self):
        m = MadeBy(actor="editor@co.com", role="editor", at="2024-01-01T00:00:00Z")
        d = m.to_dict(compact=True)
        assert d["by"] == "editor@co.com"


class TestReview:
    def test_basic(self):
        r = Review(reviewer="alice@co.com", verdict="approved")
        assert r.reviewer == "alice@co.com"
        assert r.verdict == "approved"

    def test_all_verdicts(self):
        for v in ("approved", "rejected", "needs_changes"):
            r = Review(reviewer="x", verdict=v)
            assert r.verdict == v

    def test_compact(self):
        r = Review(reviewer="bob", verdict="rejected", comment="Missing sources")
        d = r.to_dict(compact=True)
        assert d["by"] == "bob"
        assert d["v"] == "rejected"
        assert d["msg"] == "Missing sources"

    def test_round_trip(self):
        r = Review(reviewer="alice", verdict="approved", comment="LGTM", at="2024-06-01T12:00:00Z")
        d = r.to_dict(compact=False)
        r2 = Review(**d)
        assert r2.reviewer == r.reviewer
        assert r2.verdict == r.verdict


class TestSourceDetail:
    def test_basic(self):
        sd = SourceDetail(uri="https://example.com/report.pdf", page=42)
        assert sd.uri == "https://example.com/report.pdf"
        assert sd.page == 42

    def test_compact(self):
        sd = SourceDetail(uri="https://x.com", hash="abc123", section="intro")
        d = sd.to_dict(compact=True)
        assert d["uri"] == "https://x.com"
        assert d["h"] == "abc123"
        assert d["sec"] == "intro"


class TestReasoningChain:
    def test_basic(self):
        rc = ReasoningChain(steps=["Step 1", "Step 2"], conclusion="Therefore X")
        assert len(rc.steps) == 2
        assert rc.conclusion == "Therefore X"

    def test_compact(self):
        rc = ReasoningChain(steps=["a", "b"], conclusion="c", model="gpt-4", token_count=500)
        d = rc.to_dict(compact=True)
        assert d["end"] == "c"
        assert d["tok"] == 500


class TestAnnotation:
    def test_basic(self):
        a = Annotation(key="reviewed_by", value="legal_team", scope="unit")
        assert a.key == "reviewed_by"
        assert a.scope == "unit"

    def test_compact(self):
        a = Annotation(key="priority", value="high", scope="claim")
        d = a.to_dict(compact=True)
        assert d["k"] == "priority"
        assert d["val"] == "high"


class TestFreshness:
    def test_basic(self):
        f = Freshness(retrieved_at="2024-01-01T00:00:00Z", valid_until="2024-07-01T00:00:00Z")
        assert f.retrieved_at == "2024-01-01T00:00:00Z"
        assert f.valid_until == "2024-07-01T00:00:00Z"

    def test_stale_hours(self):
        f = Freshness(stale_after_hours=24)
        assert f.stale_after_hours == 24

    def test_compact(self):
        f = Freshness(retrieved_at="2024-01-01", valid_until="2024-06-01", refresh_url="https://api.example.com/data")
        d = f.to_dict(compact=True)
        assert d["at"] == "2024-01-01"
        assert d["until"] == "2024-06-01"
        assert d["url"] == "https://api.example.com/data"


class TestCostMetadata:
    def test_basic(self):
        c = CostMetadata(input_tokens=1000, output_tokens=500, model="claude-opus-4-6", cost_usd=0.05)
        assert c.input_tokens == 1000
        assert c.cost_usd == 0.05

    def test_compact(self):
        c = CostMetadata(input_tokens=100, output_tokens=50, cost_usd=0.01)
        d = c.to_dict(compact=True)
        assert d["in_tok"] == 100
        assert d["out_tok"] == 50
        assert d["cost"] == 0.01


class TestAgentProfile:
    def test_basic(self):
        ap = AgentProfile(id="agent-1", name="Research Bot", capabilities=["search", "summarize"])
        assert ap.id == "agent-1"
        assert "search" in ap.capabilities

    def test_trust_ceiling(self):
        ap = AgentProfile(id="agent-2", trust_ceiling=0.8)
        assert ap.trust_ceiling == 0.8

    def test_compact(self):
        ap = AgentProfile(id="a1", name="Bot", version="2.0", capabilities=["read"])
        d = ap.to_dict(compact=True)
        assert d["ver"] == "2.0"
        assert d["caps"] == ["read"]


class TestEnhancedClaim:
    def test_claim_with_origin(self):
        c = Claim(
            content="Revenue grew 15%",
            confidence=0.8,
            origin=Origin(type="ai", model="claude-opus-4-6"),
        )
        assert c.origin.type == "ai"
        d = c.to_dict(compact=True)
        assert d["origin"]["type"] == "ai"

    def test_claim_with_reviews(self):
        c = Claim(
            content="Test claim",
            confidence=0.9,
            reviews=[Review(reviewer="alice", verdict="approved")],
        )
        assert len(c.reviews) == 1
        d = c.to_dict(compact=False)
        assert d["reviews"][0]["reviewer"] == "alice"

    def test_claim_with_source_detail(self):
        c = Claim(
            content="Data point",
            confidence=0.95,
            source_detail=SourceDetail(uri="https://sec.gov/filing", page=12),
        )
        assert c.source_detail.uri == "https://sec.gov/filing"

    def test_claim_with_reasoning(self):
        c = Claim(
            content="Conclusion",
            confidence=0.7,
            reasoning=ReasoningChain(steps=["Premise 1", "Premise 2"], conclusion="Therefore"),
        )
        assert len(c.reasoning.steps) == 2

    def test_claim_with_freshness(self):
        c = Claim(
            content="Stock price $150",
            confidence=0.9,
            freshness=Freshness(valid_until="2024-12-31T23:59:59Z"),
        )
        assert c.freshness.valid_until == "2024-12-31T23:59:59Z"

    def test_claim_with_cost(self):
        c = Claim(
            content="Analysis",
            confidence=0.8,
            cost=CostMetadata(input_tokens=500, output_tokens=200, cost_usd=0.02),
        )
        assert c.cost.cost_usd == 0.02

    def test_claim_supersedes(self):
        c = Claim(content="Updated data", confidence=0.9, supersedes="abc12345")
        assert c.supersedes == "abc12345"
        d = c.to_dict(compact=True)
        assert d["sup"] == "abc12345"

    def test_full_claim_round_trip(self):
        c = Claim(
            content="Full claim",
            confidence=0.85,
            origin=Origin(type="ai", model="test"),
            reviews=[Review(reviewer="bob", verdict="approved")],
            freshness=Freshness(stale_after_hours=48),
            cost=CostMetadata(input_tokens=100, output_tokens=50),
            annotations=[Annotation(key="priority", value="high")],
        )
        d = c.to_dict(compact=True)
        assert "origin" in d
        assert "reviews" in d
        assert "freshness" in d
        assert "cost" in d
        assert "annotations" in d


class TestEnhancedProvHop:
    def test_provhop_new_fields(self):
        from akf.models import ProvHop
        hop = ProvHop(
            hop=0, actor="agent-1", action="created",
            timestamp="2024-01-01T00:00:00Z",
            input_hash="sha256:abc", output_hash="sha256:def",
            duration_ms=1500,
            tool_calls=["search", "summarize"],
            agent_profile=AgentProfile(id="agent-1", name="Bot"),
        )
        assert hop.input_hash == "sha256:abc"
        assert hop.duration_ms == 1500
        assert hop.agent_profile.name == "Bot"

    def test_provhop_compact(self):
        from akf.models import ProvHop
        hop = ProvHop(
            hop=0, actor="a1", action="created",
            timestamp="2024-01-01T00:00:00Z",
            duration_ms=500, tool_calls=["search"],
        )
        d = hop.to_dict(compact=True)
        assert d["dur"] == 500
        assert d["tools"] == ["search"]


class TestEnhancedAKF:
    def test_akf_made_by(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="x", confidence=0.5)],
            made_by=[MadeBy(actor="user@co.com", role="author")],
        )
        assert len(unit.made_by) == 1
        d = unit.to_dict(compact=False)
        assert d["made_by"][0]["actor"] == "user@co.com"

    def test_akf_reviews(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="x", confidence=0.5)],
            reviews=[Review(reviewer="mgr@co.com", verdict="approved")],
        )
        assert unit.reviews[0].verdict == "approved"

    def test_akf_security_block(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="x", confidence=0.5)],
            security={"access_control": {"allowed_actors": ["alice"]}, "trust_anchors": ["root@co.com"]},
        )
        assert "access_control" in unit.security

    def test_akf_compliance_block(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="x", confidence=0.5)],
            compliance={"regulations": ["eu_ai_act", "gdpr"], "auto_audit": True},
        )
        assert "eu_ai_act" in unit.compliance["regulations"]

    def test_akf_cost(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="x", confidence=0.5)],
            cost=CostMetadata(input_tokens=5000, output_tokens=2000, cost_usd=0.15),
        )
        assert unit.cost.cost_usd == 0.15

    def test_akf_schema_version(self):
        unit = AKF(version="1.0", claims=[Claim(content="x", confidence=0.5)])
        assert unit.schema_version == "1.1"

    def test_akf_parent_id(self):
        unit = AKF(
            version="1.0",
            claims=[Claim(content="x", confidence=0.5)],
            parent_id="akf-abc123",
        )
        assert unit.parent_id == "akf-abc123"
        d = unit.to_dict(compact=True)
        assert d["parent"] == "akf-abc123"
