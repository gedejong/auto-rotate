"""Tests for the GUI-agnostic controller logic."""

from __future__ import annotations

from pathlib import Path

import pytest

from auto_rotate.gui import controller
from auto_rotate.gui.controller import (
    PREVIEW_MAX_PX,
    Features,
    Options,
    available_features,
    default_output_path,
    process_file,
    render_preview,
)
from auto_rotate.pipeline import PageResult


def test_default_output_path() -> None:
    out = default_output_path(Path("/docs/My Scan.pdf"))
    assert out == Path("/docs/My Scan - upright.pdf")


def test_available_features_reflects_binaries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(controller, "tesseract_available", lambda: True)
    monkeypatch.setattr(controller, "ocrmypdf_available", lambda: False)
    assert available_features() == Features(orient=True, ocr=False)


def test_process_file_passes_options_and_callback(skewed_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.pdf"
    seen: list[PageResult] = []
    results = process_file(
        skewed_pdf, out, Options(dpi=150, orient=False, clean=False), on_page=seen.append
    )
    assert out.is_file()
    assert len(results) == 1
    assert seen == results  # callback fired once per page, in order


def test_render_preview_thumbnails_first_page(skewed_pdf: Path) -> None:
    preview = render_preview(skewed_pdf)
    assert preview.mode == "RGB"
    assert max(preview.size) <= PREVIEW_MAX_PX
