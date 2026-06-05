"""End-to-end pipeline tests."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium
import pytest
from PIL import Image

from auto_rotate import deskew_pdf, pipeline
from auto_rotate.deskew import estimate_skew
from conftest import make_text_image


def _first_page_array(pdf_path: Path, dpi: int = 150) -> np.ndarray:
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        bitmap = pdf[0].render(scale=dpi / 72.0)  # pyright: ignore[reportArgumentType]
        image = bitmap.to_pil().convert("RGB")
    finally:
        pdf.close()
    return np.asarray(image)


def test_deskew_pdf_corrects_skew_without_orientation(skewed_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.pdf"
    before = estimate_skew(_first_page_array(skewed_pdf))

    results = deskew_pdf(skewed_pdf, out, dpi=200, orient=False)

    assert out.is_file()
    assert len(results) == 1
    assert results[0].cardinal == 0
    after = estimate_skew(_first_page_array(out))
    assert abs(after) < abs(before)
    assert abs(after) < 1.5


def test_deskew_pdf_clean_produces_bilevel_pages(skewed_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.pdf"
    deskew_pdf(skewed_pdf, out, dpi=150, orient=False, clean=True)

    page = _first_page_array(out)
    # A cleaned page is pure black-on-white: only the extreme intensities survive.
    assert set(np.unique(page).tolist()) <= {0, 255}
    # The paper background dominates and is white.
    assert (page == 255).mean() > 0.5


def test_deskew_pdf_preserves_page_count(multipage_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.pdf"
    results = deskew_pdf(multipage_pdf, out, dpi=120, orient=False)
    assert len(results) == 3

    pdf = pdfium.PdfDocument(str(out))
    try:
        assert len(pdf) == 3
    finally:
        pdf.close()


def test_deskew_pdf_applies_cardinal_orientation(
    make_pdf: Callable[[list[Image.Image]], Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # A page rotated a quarter turn; OSD is mocked to report it needs 90° CW.
    rotated = make_text_image().rotate(-90, expand=True)
    pdf_in = make_pdf([rotated])
    monkeypatch.setattr(pipeline, "detect_cardinal_rotation", lambda _array: 90)

    out = tmp_path / "out.pdf"
    results = deskew_pdf(pdf_in, out, dpi=150, orient=True)

    assert results[0].cardinal == 90
    # After un-rotating, the page should be roughly portrait again.
    page = _first_page_array(out)
    assert page.shape[0] > page.shape[1]


def test_deskew_pdf_ocr_path_invokes_ocrmypdf(
    skewed_pdf: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[tuple[Path, Path]] = []

    def _fake_ocr(interim: Path, output: Path) -> None:
        calls.append((interim, output))
        output.write_bytes(interim.read_bytes())

    monkeypatch.setattr(pipeline, "run_ocr", _fake_ocr)

    out = tmp_path / "out.pdf"
    deskew_pdf(skewed_pdf, out, dpi=120, orient=False, ocr=True)

    assert len(calls) == 1
    assert calls[0][1] == out
    assert out.is_file()
