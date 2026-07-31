"""Smoke test — grows as the service grows."""

from __future__ import annotations

from extractor.main import healthz, readyz


def test_healthz() -> None:
    assert healthz() == {"status": "ok", "service": "extractor"}


def test_readyz() -> None:
    assert readyz() == {"status": "ok", "service": "extractor"}
