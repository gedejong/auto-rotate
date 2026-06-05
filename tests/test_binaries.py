"""Tests for binary resolution and environment augmentation."""

from __future__ import annotations

import pytest

from auto_rotate import binaries


def test_find_binary_uses_path_first(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(binaries.shutil, "which", lambda name, path=None: "/usr/bin/tesseract")
    assert binaries.find_binary("tesseract") == "/usr/bin/tesseract"


def test_find_binary_falls_back_to_common_dirs(monkeypatch: pytest.MonkeyPatch) -> None:
    # Not on PATH (path=None), but found when the common-dirs path is supplied.
    def fake_which(name: str, path: str | None = None) -> str | None:
        return "/opt/homebrew/bin/tesseract" if path else None

    monkeypatch.setattr(binaries.shutil, "which", fake_which)
    assert binaries.find_binary("tesseract") == "/opt/homebrew/bin/tesseract"


def test_find_binary_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(binaries.shutil, "which", lambda *a, **k: None)
    assert binaries.find_binary("nope") is None


def test_augmented_env_prepends_common_dirs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PATH", "/original/bin")
    env = binaries.augmented_env()
    # Extra dirs are prepended; the original PATH remains as the suffix.
    assert env["PATH"].endswith("/original/bin")
    assert len(env["PATH"]) > len("/original/bin")
