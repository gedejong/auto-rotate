"""Tests for the argparse CLI."""

from __future__ import annotations

import shutil
from pathlib import Path

import pypdfium2 as pdfium
import pytest

from auto_rotate import cli


def test_cli_runs_and_writes_output(
    skewed_pdf: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    out = tmp_path / "out.pdf"
    code = cli.main([str(skewed_pdf), str(out), "--no-orient", "--dpi", "150"])
    assert code == 0
    assert out.is_file()
    assert "1 page" in capsys.readouterr().out


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0
    assert "auto-rotate" in capsys.readouterr().out


def test_cli_missing_input_returns_error(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    code = cli.main([str(tmp_path / "nope.pdf"), str(tmp_path / "out.pdf"), "--no-orient"])
    assert code == 1
    assert "error:" in capsys.readouterr().err


def test_cli_missing_tesseract_reports_error(
    skewed_pdf: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(shutil, "which", lambda *a, **k: None)
    code = cli.main([str(skewed_pdf), str(tmp_path / "out.pdf")])  # orient defaults on
    assert code == 1
    assert "tesseract" in capsys.readouterr().err.lower()


def test_cli_missing_ocrmypdf_reports_error(
    skewed_pdf: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(shutil, "which", lambda *a, **k: None)
    code = cli.main([str(skewed_pdf), str(tmp_path / "out.pdf"), "--no-orient", "--ocr"])
    assert code == 1
    assert "ocrmypdf" in capsys.readouterr().err.lower()


@pytest.mark.integration
@pytest.mark.skipif(shutil.which("ocrmypdf") is None, reason="ocrmypdf not installed")
def test_cli_ocr_produces_searchable_pdf(skewed_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.pdf"
    code = cli.main([str(skewed_pdf), str(out), "--no-orient", "--ocr", "--dpi", "150"])
    assert code == 0
    pdf = pdfium.PdfDocument(str(out))
    try:
        text = pdf[0].get_textpage().get_text_range()
    finally:
        pdf.close()
    assert text.strip()  # a searchable text layer now exists
