"""Punto de entrada: `uv run fastapi dev` (desarrollo) o `fastapi run main.py` (Docker)."""

from app.main import app

__all__ = ["app"]
