"""auto_rotate: deskew and upright every page of a PDF (jdeskew + Tesseract OSD)."""

from __future__ import annotations

from .errors import (
    AutoRotateError,
    InputError,
    OcrError,
    OcrMissing,
    TesseractMissing,
)
from .pipeline import PageResult, deskew_pdf

__version__ = "0.1.1"

__all__ = [
    "AutoRotateError",
    "InputError",
    "OcrError",
    "OcrMissing",
    "PageResult",
    "TesseractMissing",
    "__version__",
    "deskew_pdf",
]
