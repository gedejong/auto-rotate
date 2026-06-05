"""GUI-agnostic logic: capability detection, job options, file processing.

Kept free of Toga so it can be unit-tested without a display. The Toga widgets in
:mod:`auto_rotate.gui.app` are a thin shell over this.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ..deskew import DEFAULT_ANGLE_MAX
from ..ocr import ocrmypdf_available
from ..orientation import tesseract_available
from ..pipeline import PageResult, deskew_pdf


@dataclass(frozen=True)
class Features:
    """Which optional features the current machine can run."""

    orient: bool  # needs the `tesseract` binary
    ocr: bool  # needs the `ocrmypdf` CLI (and tesseract)


def available_features() -> Features:
    """Detect which optional features are usable on this machine."""
    return Features(orient=tesseract_available(), ocr=ocrmypdf_available())


@dataclass(frozen=True)
class Options:
    """User-selected processing options from the GUI."""

    dpi: int = 300
    orient: bool = True
    clean: bool = False
    ocr: bool = False
    angle_max: float = DEFAULT_ANGLE_MAX


def default_output_path(input_pdf: Path) -> Path:
    """Suggested output path: ``<name> - upright.pdf`` beside the input."""
    return input_pdf.with_name(f"{input_pdf.stem} - upright.pdf")


def process_file(
    input_pdf: Path,
    output_pdf: Path,
    options: Options,
    on_page: Callable[[PageResult], None] | None = None,
) -> list[PageResult]:
    """Run the core pipeline for one file with the given options."""
    return deskew_pdf(
        input_pdf,
        output_pdf,
        dpi=options.dpi,
        orient=options.orient,
        angle_max=options.angle_max,
        clean=options.clean,
        ocr=options.ocr,
        on_page=on_page,
    )
