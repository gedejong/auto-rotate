"""End-to-end orchestration: PDF in, upright/deskewed PDF out."""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from .clean import DEFAULT_WINDOW, binarize
from .deskew import DEFAULT_ANGLE_MAX, estimate_and_deskew
from .ocr import run_ocr
from .orientation import apply_cardinal, detect_cardinal_rotation
from .raster import build_pdf, render_pages, save_page_png

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class PageResult:
    """Per-page correction applied by :func:`deskew_pdf`."""

    index: int  # zero-based page index
    cardinal: int  # clockwise cardinal rotation applied (0/90/180/270)
    skew: float  # fine-skew angle corrected, in degrees


def _correct_page(
    image: Image.Image, index: int, *, orient: bool, angle_max: float, clean_window: int
) -> tuple[Image.Image, PageResult]:
    array: NDArray[np.uint8] = np.asarray(image)

    cardinal = 0
    if orient:
        cardinal = detect_cardinal_rotation(array)
        array = apply_cardinal(array, cardinal)

    array, skew = estimate_and_deskew(array, angle_max=angle_max)
    logger.info("Page %d: cardinal %d° + skew %.3f°", index + 1, cardinal, skew)

    if clean_window:
        # Binarize last, so it cleans up the grey edges deskew interpolation leaves.
        # Mode "1" keeps the rebuilt PDF small (img2pdf encodes it as CCITT G4).
        cleaned = Image.fromarray(binarize(array, window=clean_window)).convert("1")
        return cleaned, PageResult(index=index, cardinal=cardinal, skew=skew)
    return Image.fromarray(array), PageResult(index=index, cardinal=cardinal, skew=skew)


def deskew_pdf(
    input_pdf: Path,
    output_pdf: Path,
    *,
    dpi: int = 300,
    orient: bool = True,
    angle_max: float = DEFAULT_ANGLE_MAX,
    clean: bool = False,
    ocr: bool = False,
    on_page: Callable[[PageResult], None] | None = None,
) -> list[PageResult]:
    """Deskew and upright every page of ``input_pdf``, writing ``output_pdf``.

    Pages are rasterized at ``dpi``, optionally snapped to cardinal orientation
    via Tesseract OSD (``orient``), fine-skew corrected with jdeskew, optionally
    binarized to crisp black-on-white (``clean``), then reassembled. With ``ocr``
    the result is post-processed by OCRmyPDF to add a searchable text layer.
    ``on_page`` is invoked with each :class:`PageResult` as it completes (for live
    progress). Returns the per-page corrections applied.
    """
    results: list[PageResult] = []
    # Scale the Sauvola window (tuned at 300 DPI) to the actual render DPI; 0 = skip.
    clean_window = max(15, round(DEFAULT_WINDOW * dpi / 300)) if clean else 0

    with tempfile.TemporaryDirectory(prefix="auto_rotate_") as tmpdir:
        tmp = Path(tmpdir)
        page_paths: list[Path] = []

        for index, image in enumerate(render_pages(input_pdf, dpi=dpi)):
            corrected, result = _correct_page(
                image, index, orient=orient, angle_max=angle_max, clean_window=clean_window
            )
            page_path = tmp / f"page_{index:04d}.png"
            save_page_png(corrected, page_path, dpi=dpi)
            page_paths.append(page_path)
            results.append(result)
            if on_page is not None:
                on_page(result)

        if ocr:
            interim_pdf = tmp / "interim.pdf"
            build_pdf(page_paths, interim_pdf)
            run_ocr(interim_pdf, output_pdf)
        else:
            build_pdf(page_paths, output_pdf)

    return results
