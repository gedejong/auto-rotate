"""Exception hierarchy for auto_rotate."""

from __future__ import annotations


class AutoRotateError(Exception):
    """Base class for all errors raised by auto_rotate."""


class InputError(AutoRotateError):
    """The input PDF is missing, empty, or otherwise unreadable."""


class TesseractMissing(AutoRotateError):
    """Orientation detection was requested but the `tesseract` binary is unavailable."""


class OcrMissing(AutoRotateError):
    """A searchable text layer was requested but the `ocrmypdf` CLI is unavailable."""


class OcrError(AutoRotateError):
    """The `ocrmypdf` subprocess failed."""
