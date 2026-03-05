"""Tests for Delta 2: GenerationParams extended fields and Origin.generation alias."""

from akf.models import Claim, Origin, GenerationParams


class TestGenerationParamsExtended:
    def test_basic_creation(self):
        gp = GenerationParams(temperature=0.3, tokens_output=847, cost_usd=0.004)
        assert gp.temperature == 0.3
        assert gp.cost_usd == 0.004

    def test_all_fields_optional(self):
        gp = GenerationParams()
        assert gp.temperature is None
        assert gp.tokens_input is None
        assert gp.cost_usd is None

    def test_token_fields(self):
        gp = GenerationParams(tokens_input=12400, tokens_output=847, tokens_total=13247)
        assert gp.tokens_input == 12400
        assert gp.tokens_output == 847
        assert gp.tokens_total == 13247

    def test_tools_used(self):
        gp = GenerationParams(tools_used=["web_search", "calculator"])
        assert len(gp.tools_used) == 2

    def test_prompt_hash(self):
        gp = GenerationParams(prompt_hash="sha256:e8f2a1b3")
        assert gp.prompt_hash == "sha256:e8f2a1b3"

    def test_context_fields(self):
        gp = GenerationParams(
            context_sources=["erp_db", "market_data"],
            context_window_used_pct=0.75,
            cached_tokens=500,
        )
        assert len(gp.context_sources) == 2
        assert gp.context_window_used_pct == 0.75
        assert gp.cached_tokens == 500

    def test_latency(self):
        gp = GenerationParams(latency_ms=1234.5)
        assert gp.latency_ms == 1234.5

    def test_preserves_unknown_fields(self):
        gp = GenerationParams(temperature=0.5, custom_field="preserved")
        assert gp.custom_field == "preserved"

    def test_excluded_from_dict_when_none(self):
        gp = GenerationParams(temperature=0.5)
        d = gp.to_dict()
        assert "top_p" not in d
        assert "temperature" in d

    def test_compact_serialization(self):
        gp = GenerationParams(temperature=0.3, tokens_input=1000, cost_usd=0.01)
        d = gp.to_dict(compact=True)
        assert d["temp"] == 0.3
        assert d["in_tok"] == 1000
        assert d["cost"] == 0.01


class TestOriginGeneration:
    def test_generation_alias(self):
        o = Origin(
            type="ai", model="gpt-4o",
            generation=GenerationParams(temperature=0.7),
        )
        assert o.parameters.temperature == 0.7

    def test_generation_in_origin(self):
        o = Origin(
            type="ai", model="gpt-4o",
            generation=GenerationParams(
                temperature=0.3,
                tokens_input=12400,
                tokens_output=847,
                cost_usd=0.004,
                tools_used=["erp_query", "time_series_forecast"],
                prompt_hash="sha256:e8f2a1b3",
            ),
        )
        assert o.parameters.cost_usd == 0.004
        assert len(o.parameters.tools_used) == 2

    def test_claim_with_full_generation(self):
        c = Claim(
            content="test",
            confidence=0.9,
            origin=Origin(
                type="ai", model="gpt-4o",
                generation=GenerationParams(
                    temperature=0.3, tokens_input=1000, tokens_output=200,
                    cost_usd=0.001, tools_used=["search"],
                ),
            ),
        )
        assert c.origin.parameters.cost_usd == 0.001

    def test_parameters_still_works(self):
        o = Origin(
            type="ai",
            parameters=GenerationParams(temperature=0.5),
        )
        assert o.parameters.temperature == 0.5


class TestNewOriginTypes:
    def test_collaboration_type(self):
        o = Origin(type="collaboration")
        assert o.type == "collaboration"

    def test_multi_agent_type(self):
        o = Origin(type="multi_agent")
        assert o.type == "multi_agent"
