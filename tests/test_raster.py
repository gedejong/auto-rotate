"""Tests for PDF rasterization and rebuild."""

from __future__ import annotations

from pathlib import Path

import pypdfium2 as pdfium
import pytest
from PIL import Image

from auto_rotate.errors import InputError
from auto_rotate.raster import build_pdf, render_pages, save_page_png


def test_render_pages_yields_rgb_images(multipage_pdf: Path) -> None:
    images = list(render_pages(multipage_pdf, dpi=150))
    assert len(images) == 3
    assert all(image.mode == "RGB" for image in images)


def test_render_pages_dpi_scales_pixel_size(multipage_pdf: Path) -> None:
    low = next(render_pages(multipage_pdf, dpi=100))
    high = next(render_pages(multipage_pdf, dpi=200))
    # Doubling DPI doubles raster dimensions (within a rounding pixel).
    assert abs(high.width - 2 * low.width) <= 2


def test_render_pages_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(InputError):
        list(render_pages(tmp_path / "nope.pdf", dpi=150))


def test_build_pdf_round_trip_preserves_page_count(multipage_pdf: Path, tmp_path: Path) -> None:
    out = tmp_path / "rebuilt.pdf"
    page_paths: list[Path] = []
    for index, image in enumerate(render_pages(multipage_pdf, dpi=150)):
        page_path = tmp_path / f"p{index}.png"
        save_page_png(image, page_path, dpi=150)
        page_paths.append(page_path)

    build_pdf(page_paths, out)

    rebuilt = pdfium.PdfDocument(str(out))
    try:
        assert len(rebuilt) == 3
    finally:
        rebuilt.close()


def test_build_pdf_dpi_sets_physical_page_size(tmp_path: Path) -> None:
    # A 300x600px image at 150 dpi must yield a 2in x 4in (144pt x 288pt) page.
    image = Image.new("RGB", (300, 600), (255, 255, 255))
    page_path = tmp_path / "p.png"
    save_page_png(image, page_path, dpi=150)
    out = tmp_path / "sized.pdf"
    build_pdf([page_path], out)

    pdf = pdfium.PdfDocument(str(out))
    try:
        width, height = pdf[0].get_size()  # points (1/72 in)
    finally:
        pdf.close()
    assert width == pytest.approx(144, abs=1)
    assert height == pytest.approx(288, abs=1)


def test_build_pdf_empty_raises(tmp_path: Path) -> None:
    with pytest.raises(InputError):
        build_pdf([], tmp_path / "x.pdf")
