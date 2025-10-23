"""
Backward-compatible CLI shim.
"""

from __future__ import annotations

from .main import app

__all__ = ["app"]


if __name__ == "__main__":
    app()
