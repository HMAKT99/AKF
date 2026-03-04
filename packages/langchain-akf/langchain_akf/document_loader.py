"""AKF document loader for LangChain."""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from langchain_core.document_loaders import BaseLoader
from langchain_core.documents import Document

import akf


class AKFLoader(BaseLoader):
    """Load .akf files as LangChain Documents.

    Each claim becomes a separate Document with AKF metadata preserved.

    Usage:
        loader = AKFLoader("data/report.akf")
        docs = loader.load()
    """

    def __init__(self, file_path: str, min_trust: float = 0.0):
        self.file_path = file_path
        self.min_trust = min_trust

    def lazy_load(self) -> Iterator[Document]:
        """Load .akf file and yield Documents for each claim."""
        unit = akf.load(self.file_path)
        for claim in unit.claims:
            if claim.confidence >= self.min_trust:
                metadata = {
                    "source": claim.source or "unknown",
                    "confidence": claim.confidence,
                    "authority_tier": claim.authority_tier,
                    "verified": claim.verified or False,
                    "ai_generated": claim.ai_generated or False,
                    "classification": unit.classification,
                    "akf_file": self.file_path,
                }
                yield Document(page_content=claim.content, metadata=metadata)
