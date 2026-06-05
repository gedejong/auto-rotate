#!/usr/bin/env python3
"""Render the Auto-Rotate icon set from the vector master ``docs/assets/logo.svg``.

The SVG (authored by ``make_logo_svg.py``) is the single source of truth: a
512x512 squircle with transparent corners. This rasterises it and emits the
PNG / ICO / ICNS the GUI packaging expects (base name ``autorotate``), plus the
512px README logo.

Needs an SVG rasteriser. The simplest way to run it::

    uv run --with cairosvg --with pillow python packaging/make_icons.py

(or ``pip install cairosvg`` into your environment first).
"""

from __future__ import annotations

import io
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

SVG = Path("docs/assets/logo.svg")
RES_DIR = Path("src/auto_rotate/gui/resources")
README_LOGO = Path("docs/assets/logo.png")
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
ICNS_SIZES = [16, 32, 128, 256, 512]   # iconutil also gets the @2x variants


def render(svg: Path, size: int) -> Image.Image:
    """Rasterise the SVG to a ``size``x``size`` RGBA image."""
    try:
        import cairosvg
    except ImportError:
        png = _render_cli(svg, size)
    else:
        png = cairosvg.svg2png(
            url=str(svg), output_width=size, output_height=size
        )
    return Image.open(io.BytesIO(png)).convert("RGBA")


def _render_cli(svg: Path, size: int) -> bytes:
    """Fallback: shell out to a renderer on PATH."""
    candidates = [
        ["rsvg-convert", "-w", str(size), "-h", str(size), str(svg)],
        ["cairosvg", str(svg), "-W", str(size), "-H", str(size), "-o", "-"],
        ["resvg", "-w", str(size), "-h", str(size), str(svg), "/dev/stdout"],
    ]
    for cmd in candidates:
        try:
            return subprocess.run(cmd, check=True, capture_output=True).stdout
        except (FileNotFoundError, subprocess.CalledProcessError):
            continue
    raise SystemExit(
        "No SVG rasteriser found. Run with:\n"
        "  uv run --with cairosvg --with pillow python packaging/make_icons.py"
    )


def main() -> None:
    RES_DIR.mkdir(parents=True, exist_ok=True)
    README_LOGO.parent.mkdir(parents=True, exist_ok=True)

    master = render(SVG, 1024)

    def at(size: int) -> Image.Image:
        return master.resize((size, size), Image.LANCZOS)

    png512 = at(512)
    png512.save(RES_DIR / "autorotate.png")
    png512.save(README_LOGO)
    print(f"wrote {RES_DIR / 'autorotate.png'} and {README_LOGO} (512x512)")

    at(256).save(RES_DIR / "autorotate.ico", sizes=[(s, s) for s in ICO_SIZES])
    print(f"wrote {RES_DIR / 'autorotate.ico'} {ICO_SIZES}")

    icns_path = RES_DIR / "autorotate.icns"
    try:
        with tempfile.TemporaryDirectory() as td:
            iconset = Path(td, "autorotate.iconset")
            iconset.mkdir()
            for s in ICNS_SIZES:
                at(s).save(iconset / f"icon_{s}x{s}.png")
                at(s * 2).save(iconset / f"icon_{s}x{s}@2x.png")
            master.save(iconset / "icon_512x512@2x.png")   # 1024
            subprocess.run(
                ["iconutil", "-c", "icns", str(iconset), "-o", str(icns_path)],
                check=True,
            )
        print(f"wrote {icns_path} (iconutil)")
    except (FileNotFoundError, subprocess.CalledProcessError):
        master.save(icns_path, sizes=[(s, s) for s in ICNS_SIZES + [1024]])
        print(f"wrote {icns_path} (Pillow fallback)")


if __name__ == "__main__":
    main()
