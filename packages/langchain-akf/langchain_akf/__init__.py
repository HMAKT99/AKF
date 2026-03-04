"""LangChain integration for Agent Knowledge Format (AKF).

Provides:
- AKFCallbackHandler: Auto-wraps chain output in AKF metadata
- AKFLoader: Reads .akf files as LangChain Documents
"""

from .callback import AKFCallbackHandler
from .document_loader import AKFLoader

__all__ = ["AKFCallbackHandler", "AKFLoader"]
