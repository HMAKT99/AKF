"""Tests for AKF agent module."""

import json
import os
import tempfile

import pytest
from akf.agent import (
    consume,
    derive,
    detect,
    from_tool_call,
    generation_prompt,
    response_schema,
    to_context,
    validate_output,
)
from akf.builder import AKFBuilder
from akf.core import create


class TestConsume:
    def test_consume_unit(self):
        parent = (
            AKFBuilder()
            .by("sarah@test.com")
            .claim("High trust", 0.98, source="SEC", authority_tier=1)
            .claim("Low trust", 0.3, source="guess", authority_tier=5)
            .build()
        )
        derived = consume(parent, "test-agent")
        assert len(derived.claims) <= len(parent.claims)
        assert derived.prov is not None

    def test_consume_file(self):
        unit = (
            AKFBuilder()
            .by("user@test.com")
            .claim("test", 0.9, source="test", authority_tier=1)
            .build()
        )
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False, mode="w") as f:
            f.write(unit.to_json())
            path = f.name
        try:
            derived = consume(path, "agent-1")
            assert len(derived.claims) > 0
        finally:
            os.unlink(path)


class TestDerive:
    def test_derive_with_new_claims(self):
        parent = (
            AKFBuilder()
            .by("sarah@test.com")
            .claim("Revenue $4.2B", 0.98, source="SEC", authority_tier=1)
            .build()
        )
        derived = derive(
            parent,
            "ai-agent",
            claims=[{"content": "AI insight", "confidence": 0.7, "ai_generated": True}],
        )
        assert len(derived.claims) >= 2
        assert any(c.content == "AI insight" for c in derived.claims)


class TestGenerationPrompt:
    def test_returns_string(self):
        prompt = generation_prompt()
        assert isinstance(prompt, str)
        assert "AKF" in prompt
        assert "claims" in prompt


class TestValidateOutput:
    def test_valid_json(self):
        j = '{"v":"1.0","claims":[{"c":"test","t":0.5}]}'
        result = validate_output(j)
        assert result.valid

    def test_json_in_code_block(self):
        text = '```json\n{"v":"1.0","claims":[{"c":"test","t":0.5}]}\n```'
        result = validate_output(text)
        assert result.valid

    def test_invalid_text(self):
        result = validate_output("This is not AKF at all")
        assert not result.valid


class TestResponseSchema:
    def test_minimal(self):
        schema = response_schema("minimal")
        assert schema["type"] == "object"
        assert "claims" in schema["properties"]

    def test_standard(self):
        schema = response_schema("standard")
        claim_props = schema["properties"]["claims"]["items"]["properties"]
        assert "src" in claim_props

    def test_full(self):
        schema = response_schema("full")
        claim_props = schema["properties"]["claims"]["items"]["properties"]
        assert "risk" in claim_props


class TestFromToolCall:
    def test_basic(self):
        claim = from_tool_call({"content": "Test result", "confidence": 0.8})
        assert claim.content == "Test result"
        assert claim.confidence == 0.8
        assert claim.ai_generated is True

    def test_percentage_normalization(self):
        claim = from_tool_call({"text": "Result", "score": 85})
        assert claim.confidence == 0.85

    def test_missing_content_raises(self):
        with pytest.raises(ValueError):
            from_tool_call({"score": 0.5})


class TestToContext:
    def test_formats_claims(self):
        unit = create("Revenue $4.2B", confidence=0.98, source="SEC")
        ctx = to_context(unit)
        assert "Revenue" in ctx
        assert "AKF Knowledge Context" in ctx

    def test_truncation(self):
        unit = create("A" * 5000, confidence=0.5)
        ctx = to_context(unit, max_tokens=100)
        assert len(ctx) < 5000


class TestDetect:
    def test_detect_dict(self):
        d = {"v": "1.0", "claims": [{"c": "test", "t": 0.5}]}
        result = detect(d)
        assert result is not None
        assert result["format"] == "dict"

    def test_detect_json_string(self):
        j = '{"v":"1.0","claims":[{"c":"test","t":0.5}]}'
        result = detect(j)
        assert result is not None
        assert result["format"] == "json_string"

    def test_detect_file(self):
        unit = create("test", confidence=0.5)
        with tempfile.NamedTemporaryFile(suffix=".akf", delete=False, mode="w") as f:
            f.write(unit.to_json())
            path = f.name
        try:
            result = detect(path)
            assert result is not None
            assert result["format"] == "akf_file"
        finally:
            os.unlink(path)

    def test_detect_non_akf(self):
        assert detect({"key": "value"}) is None
        assert detect("not json") is None
