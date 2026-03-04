"""Tests for AKF knowledge base module."""

import pytest
from akf.knowledge_base import KnowledgeBase


class TestKnowledgeBase:
    def test_add_and_query(self, tmp_path):
        kb = KnowledgeBase(str(tmp_path / "kb"))
        claim_id = kb.add("Revenue was $4.2B", 0.98, source="SEC", topic="finance")
        assert claim_id is not None

        claims = kb.query(topic="finance")
        assert len(claims) == 1
        assert claims[0].content == "Revenue was $4.2B"

    def test_add_multiple_to_same_topic(self, tmp_path):
        kb = KnowledgeBase(str(tmp_path / "kb"))
        kb.add("Claim 1", 0.9, topic="tech")
        kb.add("Claim 2", 0.8, topic="tech")

        claims = kb.query(topic="tech")
        assert len(claims) == 2

    def test_query_all(self, tmp_path):
        kb = KnowledgeBase(str(tmp_path / "kb"))
        kb.add("Finance claim", 0.9, topic="finance")
        kb.add("Tech claim", 0.8, topic="tech")

        all_claims = kb.query()
        assert len(all_claims) == 2

    def test_query_min_trust(self, tmp_path):
        kb = KnowledgeBase(str(tmp_path / "kb"))
        kb.add("High", 0.9, topic="test")
        kb.add("Low", 0.3, topic="test")

        claims = kb.query(min_trust=0.5)
        assert len(claims) == 1
        assert claims[0].confidence >= 0.5

    def test_to_context(self, tmp_path):
        kb = KnowledgeBase(str(tmp_path / "kb"))
        kb.add("Important fact", 0.95, source="SEC", topic="finance")
        kb.add("Less important", 0.6, topic="general")

        ctx = kb.to_context()
        assert "Knowledge Base Context" in ctx
        assert "Important fact" in ctx

    def test_prune_low_trust(self, tmp_path):
        kb = KnowledgeBase(str(tmp_path / "kb"))
        kb.add("Good claim", 0.9, topic="test")
        kb.add("Bad claim", 0.1, topic="test")

        pruned = kb.prune(max_age_days=999, min_trust=0.5)
        assert pruned == 1

        remaining = kb.query(topic="test")
        assert len(remaining) == 1
        assert remaining[0].confidence >= 0.5

    def test_stats(self, tmp_path):
        kb = KnowledgeBase(str(tmp_path / "kb"))
        kb.add("Claim 1", 0.9, topic="a")
        kb.add("Claim 2", 0.8, topic="b")

        stats = kb.stats()
        assert stats["topics"] == 2
        assert stats["total_claims"] == 2
        assert stats["average_trust"] > 0

    def test_history(self, tmp_path):
        kb = KnowledgeBase(str(tmp_path / "kb"))
        kb.add("First", 0.9, topic="test")
        kb.add("Second", 0.8, topic="test")

        history = kb.history()
        assert len(history) == 2

    def test_empty_kb(self, tmp_path):
        kb = KnowledgeBase(str(tmp_path / "empty_kb"))
        assert kb.query() == []
        assert kb.stats()["total_claims"] == 0
        assert kb.to_context() == "[Knowledge Base Context]\n"
