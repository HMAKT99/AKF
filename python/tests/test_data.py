"""Tests for AKF data module."""

import os
import tempfile

import pytest
from akf.builder import AKFBuilder
from akf.core import create
from akf.data import filter_claims, load_dataset, merge, quality_report


class TestLoadDataset:
    def test_load_multiple_files(self, tmp_path):
        for i in range(3):
            unit = create(f"Claim {i}", confidence=0.5 + i * 0.1, source=f"src{i}")
            unit.save(str(tmp_path / f"unit{i}.akf"))

        paths = [str(tmp_path / f"unit{i}.akf") for i in range(3)]
        claims = load_dataset(paths)
        assert len(claims) == 3

    def test_load_with_filters(self, tmp_path):
        for i in range(3):
            unit = create(f"Claim {i}", confidence=0.3 + i * 0.3, source=f"src{i}")
            unit.save(str(tmp_path / f"unit{i}.akf"))

        paths = [str(tmp_path / f"unit{i}.akf") for i in range(3)]
        claims = load_dataset(paths, filters={"min_trust": 0.6})
        assert all(c.confidence >= 0.6 for c in claims)


class TestQualityReport:
    def test_basic(self):
        unit = (
            AKFBuilder()
            .by("user@test.com")
            .claim("Revenue", 0.98, source="SEC", authority_tier=1, verified=True)
            .claim("AI claim", 0.7, source="model", ai_generated=True)
            .build()
        )
        report = quality_report(unit)
        assert report["total_claims"] == 2
        assert report["sourced_claims"] == 2
        assert report["verified_claims"] == 1
        assert report["ai_generated_claims"] == 1
        assert 0 <= report["quality_score"] <= 1


class TestMerge:
    def test_merge_two_units(self):
        u1 = create("Claim A", confidence=0.9, source="src1")
        u2 = create("Claim B", confidence=0.8, source="src2")
        merged = merge([u1, u2])
        assert len(merged.claims) == 2

    def test_merge_deduplicates_by_id(self):
        u1 = create("Claim A", confidence=0.9)
        # Create u2 with same claim
        u2 = u1.model_copy()
        merged = merge([u1, u2])
        assert len(merged.claims) == 1

    def test_merge_takes_highest_classification(self):
        u1 = create("A", confidence=0.9)
        u1 = u1.model_copy(update={"classification": "public"})
        u2 = create("B", confidence=0.8)
        u2 = u2.model_copy(update={"classification": "confidential"})
        merged = merge([u1, u2])
        assert merged.classification == "confidential"

    def test_merge_empty_raises(self):
        with pytest.raises(ValueError):
            merge([])


class TestFilterClaims:
    def test_filter_by_trust(self):
        unit = (
            AKFBuilder()
            .claim("High", 0.9)
            .claim("Low", 0.3)
            .build()
        )
        filtered = filter_claims(unit, min_trust=0.5)
        assert len(filtered.claims) == 1
        assert filtered.claims[0].content == "High"

    def test_filter_verified_only(self):
        unit = (
            AKFBuilder()
            .claim("Verified", 0.9, verified=True)
            .claim("Not verified", 0.9)
            .build()
        )
        filtered = filter_claims(unit, verified_only=True)
        assert len(filtered.claims) == 1

    def test_filter_exclude_ai(self):
        unit = (
            AKFBuilder()
            .claim("Human", 0.9)
            .claim("AI", 0.9, ai_generated=True)
            .build()
        )
        filtered = filter_claims(unit, exclude_ai=True)
        assert len(filtered.claims) == 1

    def test_filter_no_results_raises(self):
        unit = create("Low", confidence=0.1)
        with pytest.raises(ValueError):
            filter_claims(unit, min_trust=0.99)
