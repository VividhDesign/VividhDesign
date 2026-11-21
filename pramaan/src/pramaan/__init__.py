"""Pramaan: catch fake and wrong case citations in Indian legal documents."""

__version__ = "0.1.0"

from .citations import extract  # noqa: E402

__all__ = ["extract", "__version__"]
