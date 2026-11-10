"""Optional API loops; the static generator never imports or runs upstream code."""
from .engine import optimize, describe_methods

__all__ = ["optimize", "describe_methods"]
