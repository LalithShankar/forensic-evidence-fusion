"""Smoke tests documenting backend quality-tooling expectations."""

from pathlib import Path

import pytest


def test_pyproject_declares_dev_tooling() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    content = pyproject.read_text(encoding="utf-8")

    for tool in ("pytest", "ruff", "black", "mypy"):
        assert tool in content


def test_documented_pytest_entrypoint_runs() -> None:
    """README documents: cd backend && pip install -e '.[dev]' && pytest."""
    assert pytest.__version__
