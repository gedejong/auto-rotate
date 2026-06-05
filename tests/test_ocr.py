"""Unit tests for the OCR step (subprocess mocked)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from auto_rotate import ocr
from auto_rotate.errors import OcrError, OcrMissing


def _completed(returncode: int, stderr: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["ocrmypdf"], returncode=returncode, stderr=stderr)


def test_run_ocr_success(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ocr, "ocrmypdf_available", lambda: True)
    captured: dict[str, list[str]] = {}

    def _fake_run(cmd: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["cmd"] = cmd
        return _completed(0)

    monkeypatch.setattr(subprocess, "run", _fake_run)
    ocr.run_ocr(tmp_path / "in.pdf", tmp_path / "out.pdf")

    assert captured["cmd"][0] == "ocrmypdf"
    assert captured["cmd"][1:] == [str(tmp_path / "in.pdf"), str(tmp_path / "out.pdf")]


def test_run_ocr_propagates_failure(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ocr, "ocrmypdf_available", lambda: True)
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: _completed(7, "boom"))
    with pytest.raises(OcrError, match="boom"):
        ocr.run_ocr(tmp_path / "in.pdf", tmp_path / "out.pdf")


def test_run_ocr_requires_binary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(ocr, "ocrmypdf_available", lambda: False)
    with pytest.raises(OcrMissing):
        ocr.run_ocr(tmp_path / "in.pdf", tmp_path / "out.pdf")
