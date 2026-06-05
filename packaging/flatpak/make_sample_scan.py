"""Generate a deliberately bad-looking scanned PDF for the demo screenshot.

Renders a page of text, then degrades it like a careless flatbed scan: an off-white
uneven paper tone, sensor noise, a slight blur, a few specks, a soft edge shadow, and a
several-degree skew. Used by the screenshot CI job as the GUI's input document.

Usage: python make_sample_scan.py OUTPUT.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

import img2pdf
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, DPI = 1000, 1400, 200

_TITLE = "Quarterly Field Report"
_BODY = [
    "To the regional office, please find enclosed the summary of this",
    "quarter's site visits. Conditions across the northern districts have",
    "remained variable, with intermittent supply delays affecting three of",
    "the seven monitored locations. Staff rotations were completed on",
    "schedule and no safety incidents were recorded during the period.",
    "",
    "Equipment calibration is now current at every station. The replacement",
    "sensors installed in March continue to outperform the previous units,",
    "and maintenance overhead has fallen accordingly. We recommend",
    "extending the same configuration to the remaining sites in Q3.",
    "",
    "Budget utilisation stands at sixty-one percent against forecast. A",
    "detailed breakdown by cost centre is attached as Appendix B, together",
    "with the reconciled travel ledger and the updated risk register.",
]


def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for name in ("DejaVuSerif.ttf", "DejaVuSans.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default(size=size)


def _document() -> Image.Image:
    img = Image.new("L", (W, H), 255)
    draw = ImageDraw.Draw(img)
    draw.text((90, 70), _TITLE, fill=15, font=_font(46))
    draw.line((90, 140, W - 90, 140), fill=40, width=2)
    y = 190
    for line in _BODY:
        draw.text((90, y), line, fill=25, font=_font(28))
        y += 46
    draw.text((90, H - 150), "Signed,", fill=25, font=_font(28))
    draw.text((90, H - 90), "A. Inspector", fill=20, font=_font(34))
    return img


def _degrade(doc: Image.Image, rng: np.random.Generator) -> Image.Image:
    arr = np.asarray(doc).astype(np.float32)

    # Uneven off-white paper tone (a soft diagonal gradient, never pure white).
    yy, xx = np.mgrid[0:H, 0:W]
    shade = 232 - 22 * (xx / W) - 12 * (yy / H)
    paper = np.minimum(arr, shade)

    # Sensor noise + a faint horizontal banding.
    paper += rng.normal(0, 7, paper.shape)
    paper += 4 * np.sin(yy / 3.0)

    # A few dark specks of dust.
    for _ in range(60):
        sy, sx = int(rng.integers(0, H)), int(rng.integers(0, W))
        paper[sy : sy + 2, sx : sx + 2] -= rng.integers(60, 160)

    out = Image.fromarray(np.clip(paper, 0, 255).astype(np.uint8), "L")
    out = out.filter(ImageFilter.GaussianBlur(0.6))

    # Soft shadow down the left edge (page lifting off the platen).
    shadow = Image.new("L", out.size, 255)
    sd = ImageDraw.Draw(shadow)
    for x in range(60):
        sd.line((x, 0, x, H), fill=int(150 + 105 * x / 60))
    out = Image.fromarray(
        np.clip(np.asarray(out).astype(np.float32) * (np.asarray(shadow) / 255), 0, 255).astype(
            np.uint8
        ),
        "L",
    )

    # Skew, filling the exposed corners with a light-grey "scanner bed" (light enough
    # that the cleanup resolves it to white rather than a hard black border).
    out = out.convert("RGB").rotate(-4.5, expand=True, fillcolor=(150, 150, 150))
    return out


def main() -> None:
    out_path = Path(sys.argv[1] if len(sys.argv) > 1 else "sample_scan.pdf")
    rng = np.random.default_rng(7)
    page = _degrade(_document(), rng)
    png = out_path.with_suffix(".png")
    page.save(png, dpi=(DPI, DPI))
    out_path.write_bytes(img2pdf.convert(str(png)))
    png.unlink()
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
