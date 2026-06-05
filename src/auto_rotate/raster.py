"""PDF rasterization (pypdfium2) and image-to-PDF rebuild (img2pdf)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import img2pdf
import pypdfium2 as pdfium
from PIL import Image

from .errors import InputError

POINTS_PER_INCH = 72.0


def render_pages(pdf_path: Path, dpi: int) -> Iterator[Image.Image]:
    """Yield each page of ``pdf_path`` as an RGB :class:`PIL.Image` rendered at ``dpi``.

    Pages are produced lazily so a large document is never fully held in memory.
    """
    if not pdf_path.is_file():
        raise InputError(f"Input PDF not found: {pdf_path}")

    scale = dpi / POINTS_PER_INCH
    pdf = pdfium.PdfDocument(str(pdf_path))
    try:
        if len(pdf) == 0:
            raise InputError(f"Input PDF has no pages: {pdf_path}")
        for page in pdf:
            # pypdfium2's `scale` is untyped (defaults to int 1) but accepts float.
            bitmap = page.render(scale=scale)  # pyright: ignore[reportArgumentType]
            try:
                image = bitmap.to_pil()
            finally:
                bitmap.close()
            page.close()
            # Drop any alpha channel so the rebuilt PDF has a predictable, white-backed page.
            yield image.convert("RGB")
    finally:
        pdf.close()


def save_page_png(image: Image.Image, path: Path, dpi: int) -> None:
    """Save ``image`` as a PNG that carries ``dpi`` metadata.

    img2pdf derives the physical page size from this metadata; without it the
    output defaults to 72 dpi and pages come out oversized.
    """
    image.save(path, format="PNG", dpi=(dpi, dpi))


def build_pdf(image_paths: list[Path], output_pdf: Path) -> None:
    """Assemble ``image_paths`` (in order) into a single PDF at ``output_pdf``."""
    if not image_paths:
        raise InputError("No page images to assemble into a PDF.")
    pdf_bytes = img2pdf.convert([str(p) for p in image_paths])
    if pdf_bytes is None:  # pragma: no cover - img2pdf returns bytes on success
        raise InputError("img2pdf produced no output.")
    output_pdf.write_bytes(pdf_bytes)
