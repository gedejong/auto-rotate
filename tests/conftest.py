"""Shared fixtures: synthetic text images and PDFs built with PIL + img2pdf."""

from __future__ import annotations

import io
from collections.abc import Callable
from pathlib import Path

import img2pdf
import numpy as np
import pytest
from numpy.typing import NDArray
from PIL import Image, ImageDraw, ImageFont

# A page of lines of text gives the FFT/radial-projection estimator clear
# directional structure to lock onto.
_LINES = [
    "The quick brown fox jumps over the lazy dog.",
    "Pack my box with five dozen liquor jugs.",
    "How vexingly quick daft zebras jump!",
    "Sphinx of black quartz, judge my vow.",
]


def make_text_image(width: int = 1000, height: int = 1400) -> Image.Image:
    """Render a white page of repeated black text lines as an RGB image."""
    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default(size=34)
    y = 40
    line_height = 60
    while y < height - line_height:
        draw.text((40, y), _LINES[(y // line_height) % len(_LINES)], fill=(0, 0, 0), font=font)
        y += line_height
    return image


def skew_image(image: Image.Image, degrees: float) -> Image.Image:
    """Rotate ``image`` by ``degrees`` (CCW), expanding and filling white."""
    return image.rotate(
        degrees, expand=True, fillcolor=(255, 255, 255), resample=Image.Resampling.BICUBIC
    )


def images_to_pdf(images: list[Image.Image], path: Path, dpi: int = 300) -> Path:
    """Write ``images`` as a multi-page PDF with DPI metadata, returning ``path``."""
    page_bytes: list[bytes] = []
    for image in images:
        buffer = io.BytesIO()
        image.convert("RGB").save(buffer, format="PNG", dpi=(dpi, dpi))
        page_bytes.append(buffer.getvalue())
    pdf_bytes = img2pdf.convert(page_bytes)
    assert pdf_bytes is not None
    path.write_bytes(pdf_bytes)
    return path


@pytest.fixture
def text_image() -> NDArray[np.uint8]:
    return np.asarray(make_text_image())


@pytest.fixture
def skewed_pdf(tmp_path: Path) -> Path:
    """A single-page PDF whose text is skewed by a known +7°."""
    skewed = skew_image(make_text_image(), 7.0)
    return images_to_pdf([skewed], tmp_path / "skewed.pdf")


@pytest.fixture
def multipage_pdf(tmp_path: Path) -> Path:
    """A three-page upright PDF."""
    pages = [make_text_image() for _ in range(3)]
    return images_to_pdf(pages, tmp_path / "multi.pdf")


@pytest.fixture
def make_pdf(tmp_path: Path) -> Callable[[list[Image.Image]], Path]:
    """Factory to build an ad-hoc PDF from a list of images."""
    counter = {"n": 0}

    def _make(images: list[Image.Image]) -> Path:
        counter["n"] += 1
        return images_to_pdf(images, tmp_path / f"doc_{counter['n']}.pdf")

    return _make
