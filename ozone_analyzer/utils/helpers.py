"""Common utility helpers."""

from typing import Any, Optional


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Convert ``value`` to float, returning ``default`` on failure."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default
