"""Command-line interface for auto_rotate."""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from pathlib import Path

from . import __version__
from .deskew import DEFAULT_ANGLE_MAX
from .errors import AutoRotateError
from .pipeline import deskew_pdf


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="auto-rotate",
        description="Deskew and turn upright every page of a PDF.",
    )
    parser.add_argument("input", type=Path, help="Input PDF path.")
    parser.add_argument("output", type=Path, help="Output PDF path.")
    parser.add_argument(
        "--dpi",
        type=int,
        default=300,
        help="Rasterization DPI (default: 300).",
    )
    orient = parser.add_mutually_exclusive_group()
    orient.add_argument(
        "--orient",
        dest="orient",
        action="store_true",
        help="Snap pages to cardinal orientation via Tesseract OSD (default).",
    )
    orient.add_argument(
        "--no-orient",
        dest="orient",
        action="store_false",
        help="Skip cardinal-orientation detection (no `tesseract` needed).",
    )
    parser.set_defaults(orient=True)
    parser.add_argument(
        "--angle-max",
        type=float,
        default=DEFAULT_ANGLE_MAX,
        help=f"Max fine-skew angle to search, in degrees (default: {DEFAULT_ANGLE_MAX}).",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Binarize pages to pure black-on-white (flattens scan background).",
    )
    parser.add_argument(
        "--ocr",
        action="store_true",
        help="Add a searchable text layer with OCRmyPDF (needs `ocrmypdf`).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Log the correction applied to each page.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint. Returns a process exit code."""
    args = _build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(message)s",
    )
    try:
        results = deskew_pdf(
            args.input,
            args.output,
            dpi=args.dpi,
            orient=args.orient,
            angle_max=args.angle_max,
            clean=args.clean,
            ocr=args.ocr,
        )
    except AutoRotateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"Wrote {args.output} ({len(results)} page{'s' if len(results) != 1 else ''}).")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
