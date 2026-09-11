"""Q2 causal daily-planning baseline package.

Importing this package never imports or invokes an optimization solver.
"""

from .config import Q2Config, Q2Parameters, load_config

__all__ = ["Q2Config", "Q2Parameters", "load_config"]

