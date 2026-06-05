#!/usr/bin/env python3
"""Generate the Auto-Rotate app icon set from the source artwork.

The source art is a full-bleed iOS-style squircle on an opaque dark field.
We cut the four corners to transparency with an anti-aliased superellipse
mask, square the result, and emit the PNG / ICO / ICNS the GUI packaging
expects (base name ``autorotate``), plus a README hero PNG.

Run from the repo root::

    python packaging/make_icons.py "$HOME/Downloads/Logo Auto-Rotate.png"
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

# Superellipse fit to the source artwork's existing corner shape.
EXPONENT = 3.0          # continuous-corner exponent (~iOS squircle)
SUPERSAMPLE = 4         # for anti-aliased mask edges
RES_DIR = Path("src/auto_rotate/gui/resources")
README_LOGO = Path("docs/assets/logo.png")
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
ICNS_SIZES = [16, 32, 64, 128, 256, 512, 1024]


def squircle_alpha(w: int, h: int, rx: float, ry: float, n: float) -> np.ndarray:
    """Anti-aliased alpha (0..255) for a full-bleed rounded rect with
    superellipse corners of radii ``rx``/``ry`` and exponent ``n``."""
    s = SUPERSAMPLE
    ys, xs = np.mgrid[0:h * s, 0:w * s].astype(np.float64)
    xs = (xs + 0.5) / s
    ys = (ys + 0.5) / s
    # distance past each corner's straight-edge tangent, clamped at 0
    dx = np.maximum(rx - xs, np.maximum(xs - (w - rx), 0.0))
    dy = np.maximum(ry - ys, np.maximum(ys - (h - ry), 0.0))
    inside = (dx / rx) ** n + (dy / ry) ** n <= 1.0
    big = inside.astype(np.float32)
    # box-downsample to original resolution -> coverage in [0,1]
    big = big.reshape(h, s, w, s).mean(axis=(1, 3))
    return np.clip(big * 255.0, 0, 255).astype(np.uint8)


def mask_corners(src: Path) -> Image.Image:
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    # corner radii measured from the source (full-bleed, edges flush to frame)
    rx = w * 151.0 / 552.0
    ry = h * 153.0 / 566.0
    alpha = squircle_alpha(w, h, rx, ry, EXPONENT)
    a = np.array(im)
    a[:, :, 3] = np.minimum(a[:, :, 3], alpha)
    return Image.fromarray(a, "RGBA")


def square(im: Image.Image, size: int) -> Image.Image:
    """Center the masked art on a transparent square, then scale to ``size``.

    Pads the short axis so nothing is distorted or clipped."""
    w, h = im.size
    side = max(w, h)
    canvas = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    canvas.paste(im, ((side - w) // 2, (side - h) // 2))
    return canvas.resize((size, size), Image.LANCZOS)


def main() -> None:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(
        Path.home(), "Downloads", "Logo Auto-Rotate.png"
    )
    masked = mask_corners(src)

    RES_DIR.mkdir(parents=True, exist_ok=True)
    README_LOGO.parent.mkdir(parents=True, exist_ok=True)

    icon512 = square(masked, 512)
    icon512.save(RES_DIR / "autorotate.png")
    icon512.save(README_LOGO)
    print(f"wrote {RES_DIR / 'autorotate.png'} and {README_LOGO} (512x512)")

    # Windows .ico (multi-resolution)
    icon256 = square(masked, 256)
    icon256.save(
        RES_DIR / "autorotate.ico",
        sizes=[(s, s) for s in ICO_SIZES],
    )
    print(f"wrote {RES_DIR / 'autorotate.ico'} {ICO_SIZES}")

    # macOS .icns via iconutil (preferred) with a Pillow fallback
    icon1024 = square(masked, 1024)
    icns_path = RES_DIR / "autorotate.icns"
    try:
        with tempfile.TemporaryDirectory() as td:
            iconset = Path(td, "autorotate.iconset")
            iconset.mkdir()
            for s in [16, 32, 128, 256, 512]:
                icon1024.resize((s, s), Image.LANCZOS).save(iconset / f"icon_{s}x{s}.png")
                d = s * 2
                icon1024.resize((d, d), Image.LANCZOS).save(iconset / f"icon_{s}x{s}@2x.png")
            icon1024.save(iconset / "icon_512x512@2x.png")  # 1024
            subprocess.run(
                ["iconutil", "-c", "icns", str(iconset), "-o", str(icns_path)],
                check=True,
            )
        print(f"wrote {icns_path} (iconutil)")
    except (FileNotFoundError, subprocess.CalledProcessError):
        icon1024.save(icns_path, sizes=[(s, s) for s in ICNS_SIZES])
        print(f"wrote {icns_path} (Pillow fallback)")


if __name__ == "__main__":
    main()
