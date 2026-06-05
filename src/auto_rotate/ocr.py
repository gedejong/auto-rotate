"""Optional searchable-text-layer step via the ``ocrmypdf`` CLI."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .binaries import augmented_env, find_binary
from .errors import OcrError, OcrMissing


def ocrmypdf_available() -> bool:
    """Return whether the ``ocrmypdf`` CLI can be found (PATH or common dirs)."""
    return find_binary("ocrmypdf") is not None


def run_ocr(input_pdf: Path, output_pdf: Path) -> None:
    """Add a searchable text layer to ``input_pdf``, writing ``output_pdf``.

    Shells out to ``ocrmypdf input output`` (which itself requires the system
    ``tesseract`` binary). Raises :class:`OcrMissing` if the CLI is absent and
    :class:`OcrError` if the subprocess fails.
    """
    ocrmypdf = find_binary("ocrmypdf")
    if ocrmypdf is None:
        raise OcrMissing(
            "The --ocr flag requires the `ocrmypdf` CLI. Install it "
            "(e.g. `pip install auto-rotate[ocr]` or `brew install ocrmypdf`)."
        )
    # ocrmypdf spawns tesseract/ghostscript; augment PATH so it finds them under a
    # minimal GUI-app environment.
    result = subprocess.run(
        [ocrmypdf, str(input_pdf), str(output_pdf)],
        capture_output=True,
        text=True,
        check=False,
        env=augmented_env(),
    )
    if result.returncode != 0:
        raise OcrError(f"ocrmypdf exited with code {result.returncode}:\n{result.stderr.strip()}")
