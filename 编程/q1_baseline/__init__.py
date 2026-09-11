"""Stage-5 deterministic Q1 baseline implementation.

This package builds and validates the model.  It never solves anything merely by
being imported; a solve only occurs through the explicit human-run CLI command.
"""

from .parameters import Q1Parameters

__all__ = ["Q1Parameters"]

