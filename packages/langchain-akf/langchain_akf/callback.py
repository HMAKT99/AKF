"""AKF callback handler for LangChain."""

from __future__ import annotations

from typing import Any

from langchain_core.callbacks import BaseCallbackHandler

import akf


class AKFCallbackHandler(BaseCallbackHandler):
    """LangChain callback that wraps chain outputs in AKF metadata.

    Usage:
        handler = AKFCallbackHandler(agent_id="my-agent", classification="internal")
        chain.invoke(input, config={"callbacks": [handler]})
        # Access AKF units via handler.units
    """

    def __init__(
        self,
        agent_id: str = "langchain-agent",
        classification: str = "internal",
        default_confidence: float = 0.7,
    ):
        self.agent_id = agent_id
        self.classification = classification
        self.default_confidence = default_confidence
        self.units: list[akf.AKF] = []

    def on_chain_end(self, outputs: dict[str, Any], **kwargs: Any) -> None:
        """Wrap chain output in AKF metadata."""
        if isinstance(outputs, dict):
            for key, value in outputs.items():
                if isinstance(value, str) and value.strip():
                    unit = akf.create(
                        value,
                        confidence=self.default_confidence,
                        source=f"langchain:{key}",
                        ai_generated=True,
                    )
                    self.units.append(unit)
