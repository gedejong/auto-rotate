#!/usr/bin/env python3
"""Hand-authored vector master for the Auto-Rotate logo.

Emits ``docs/assets/logo.svg`` — a 512x512 squircle (matching the raster
icon's superellipse), a circular rotation arrow, and a tilted PDF page.
Geometry is parameterised so colours, the arrow sweep, and the page tilt
can be tuned without re-deriving paths by hand.

    python packaging/make_logo_svg.py            # -> docs/assets/logo.svg
"""

from __future__ import annotations

import math
from pathlib import Path

OUT = Path("docs/assets/logo.svg")

# ----------------------------------------------------------------------------
# Tunables (iterate here)
# ----------------------------------------------------------------------------
N = 3.0                      # squircle superellipse exponent (matches raster)
RX = 151.0 * 512 / 552       # corner radius x  (~140.1)
RY = 153.0 * 512 / 566       # corner radius y  (~138.4)

# Squircle background = diagonal hue (top-right blue -> bottom-left green-teal)
# overlaid with an all-corner vignette that darkens to navy.
BG_STOPS = [(0.0, "#1d4068"), (0.5, "#15545f"), (1.0, "#0a5249")]
VIGNETTE = dict(cx=0.5, cy=0.5, r=0.72)
VIGNETTE_STOPS = [(0.0, "#06263c", 0.0), (0.55, "#06263c", 0.0),
                  (1.0, "#051f31", 0.72)]
# The "circle within the squircle": a hard-edged disc, nearly filling the
# squircle, with its own diagonal gradient -- bluer top-right, greener
# bottom-left (sampled from the source) -- plus a soft centre highlight.
DISC = dict(cx=256.0, cy=252.0, r=246.0)
DISC_STOPS = [(0.0, "#23698c", 1.0), (0.5, "#1a738a", 1.0), (1.0, "#0a7a6f", 1.0)]
DISC_HI = ("#bfeeff", 0.13)   # soft radial centre lift on top of the disc

# rotation arrow (ring), centred in the box; tail tucks behind the page top-left
ARROW = dict(cx=256.0, cy=256.0, r=166.0, w=34.0,
             a_start=170.0, a_end=58.0,   # math degrees, CCW, 90=up; sweeps CCW
             head_len=52.0, head_w=78.0)
ARROW_COLOR = "#ffffff"
ARROW_PAD = 18.0             # transparent halo knocked out of the arrow round the page

# PDF page (rotated hard to the left): light-blue body inside a white frame,
# with "PDF" set in its own white box (left, ~3/4 width, inset from the top)
# over the blue, so the white fold lands on the blue background beside it.
PAGE = dict(cx=238.0, cy=244.0, w=182.0, h=226.0, r=21.0, tilt=-39.0,
            dogear=48.0, border=13.0, foldr=13.0)
PAGE_FRAME = "#ffffff"   # the white outline (sits inside) + fold + the "PDF" box
PAGE_TOP = "#dbe8f2"     # light-blue body, slightly darker than the white
PAGE_BOT = "#bdd3e3"
LABEL = dict(wfrac=0.74, top=23.0, h=46.0)  # white "PDF" box (flush to left frame)
INK = "#1f6385"          # "PDF" wordmark + body lines


# ----------------------------------------------------------------------------
def squircle_path() -> str:
    S = 512.0

    def quarter(cx, cy, sx, sy, x_is_sin):
        out = []
        for i in range(1, 25):
            t = i / 24 * (math.pi / 2)
            s = math.sin(t) ** (2 / N)
            c = math.cos(t) ** (2 / N)
            if x_is_sin:
                x, y = cx + sx * RX * s, cy + sy * RY * c
            else:
                x, y = cx + sx * RX * c, cy + sy * RY * s
            out.append(f"L {x:.2f},{y:.2f}")
        return out

    p = [f"M {RX:.2f},0", f"L {S - RX:.2f},0"]
    p += quarter(S - RX, RY, +1, -1, True)
    p.append(f"L {S:.2f},{S - RY:.2f}")
    p += quarter(S - RX, S - RY, +1, +1, False)
    p.append(f"L {RX:.2f},{S:.2f}")
    p += quarter(RX, S - RY, -1, +1, True)
    p.append(f"L 0,{RY:.2f}")
    p += quarter(RX, RY, -1, -1, False)
    p.append("Z")
    return " ".join(p)


def _pt(cx, cy, r, deg):
    """math-degree point (CCW, 90=up) in SVG screen coords (y down)."""
    a = math.radians(deg)
    return cx + r * math.cos(a), cy - r * math.sin(a)


def arrow_markup() -> str:
    a = ARROW
    cx, cy, r = a["cx"], a["cy"], a["r"]
    x0, y0 = _pt(cx, cy, r, a["a_start"])
    x1, y1 = _pt(cx, cy, r, a["a_end"])
    # sweep the long way around the bottom (gap stays at top); screen-CCW = flag 0
    arc = (f'<path d="M {x0:.2f},{y0:.2f} '
           f'A {r:.2f},{r:.2f} 0 1 0 {x1:.2f},{y1:.2f}" '
           f'fill="none" stroke="{ARROW_COLOR}" stroke-width="{a["w"]:.1f}" '
           f'stroke-linecap="round"/>')
    # arrowhead at the a_end tip: base perpendicular to the radius, point "up"
    rux, ruy = (x1 - cx) / r, (y1 - cy) / r          # outward radial unit
    p1, p2 = (-ruy, rux), (ruy, -rux)                # the two perpendiculars
    px, py = p1 if p1[1] < p2[1] else p2             # choose the upward one
    hl, hw = a["head_len"], a["head_w"] / 2
    tip = (x1 + px * hl, y1 + py * hl)
    b1 = (x1 + rux * hw, y1 + ruy * hw)
    b2 = (x1 - rux * hw, y1 - ruy * hw)
    head = (f'<path d="M {tip[0]:.2f},{tip[1]:.2f} L {b1[0]:.2f},{b1[1]:.2f} '
            f'L {b2[0]:.2f},{b2[1]:.2f} Z" fill="{ARROW_COLOR}"/>')
    return arc + "\n    " + head


_S = 0.7071  # sin/cos 45, for filleting the 45-degree dog-ear cut


def _body_path(w, h, r, d, fr=0.0) -> str:
    """Page outline (origin at centre) with a folded, rounded top-right corner."""
    x, y = -w / 2, -h / 2
    f = fr * _S
    return (f"M {x + r},{y} L {x + w - d - fr},{y} "
            f"Q {x + w - d},{y} {x + w - d + f},{y + f} "          # into the cut
            f"L {x + w - f},{y + d - f} "
            f"Q {x + w},{y + d} {x + w},{y + d + fr} "             # cut -> right edge
            f"L {x + w},{y + h - r} Q {x + w},{y + h} {x + w - r},{y + h} "
            f"L {x + r},{y + h} Q {x},{y + h} {x},{y + h - r} "
            f"L {x},{y + r} Q {x},{y} {x + r},{y} Z")


def _fold_path(w, h, d, fr) -> str:
    """The folded-over corner flap (rounded triangle), origin at centre."""
    x, y = -w / 2, -h / 2
    ax, ay = x + w - d, y          # top vertex
    bx, by = x + w, y + d          # right vertex
    cx, cy = x + w - d, y + d      # inner vertex
    f = fr * _S
    return (f"M {ax + f},{ay + f} "                      # after A, along the cut
            f"L {bx - f},{by - f} Q {bx},{by} {bx - fr},{by} "   # B (cut->bottom)
            f"L {cx + fr},{cy} Q {cx},{cy} {cx},{cy - fr} "      # C (bottom->left)
            f"L {ax},{ay + fr} Q {ax},{ay} {ax + f},{ay + f} Z") # A


def _rect_right_rounded(x, y, w, h, r) -> str:
    """Rect with a square left edge (merges into the frame) and rounded right."""
    return (f"M {x},{y} L {x + w - r},{y} Q {x + w},{y} {x + w},{y + r} "
            f"L {x + w},{y + h - r} Q {x + w},{y + h} {x + w - r},{y + h} "
            f"L {x},{y + h} Z")


def page_body_path() -> str:
    p = PAGE
    return _body_path(p["w"], p["h"], p["r"], p["dogear"], p["foldr"])


def page_transform() -> str:
    p = PAGE
    return f'translate({p["cx"]},{p["cy"]}) rotate({p["tilt"]})'


def page_cut_path() -> str:
    """Padded silhouette knocked out of the arrow so the page reads separate."""
    p, pad = PAGE, ARROW_PAD
    return _body_path(p["w"] + 2 * pad, p["h"] + 2 * pad,
                      p["r"] + pad, p["dogear"] + pad, p["foldr"] + pad)


def page_markup() -> str:
    p, lab = PAGE, LABEL
    w, h, d, b = p["w"], p["h"], p["dogear"], p["border"]
    x, y = -w / 2, -h / 2
    body = _body_path(w, h, p["r"], d, p["foldr"])
    fold = _fold_path(w, h, d, p["foldr"])
    # white "PDF" box: flush to the left frame (no left curves), ~3/4 width,
    # inset from the top; square left edge so it merges into the white border
    bx, by = x, y + b + lab["top"]
    bw, bh = b + (w - 2 * b) * lab["wfrac"], lab["h"]
    pdf_box = _rect_right_rounded(bx, by, bw, bh, 8)
    label_y = by + bh - 11
    # body text lines, on the blue body below the box
    line_x = x + b + 16
    line_w_full = (w - 2 * b) - 32
    line_y0 = y + 0.56 * h
    lines = ""
    for i in range(2):
        ly = line_y0 + i * 28
        lw = line_w_full if i == 0 else line_w_full * 0.62
        lines += (f'<rect x="{line_x}" y="{ly}" width="{lw:.1f}" height="13" '
                  f'rx="6.5" fill="{INK}" opacity="0.82"/>\n      ')
    return f"""<g transform="{page_transform()}">
      <path d="{body}" fill="url(#page)" stroke="{PAGE_FRAME}" stroke-width="{2 * b}"
            stroke-linejoin="round" clip-path="url(#pageclip)"/>
      <path d="{fold}" fill="{PAGE_FRAME}"/>
      <path d="{pdf_box}" fill="{PAGE_FRAME}"/>
      <text x="{bx + 12}" y="{label_y}" font-family="Helvetica, Arial, sans-serif"
            font-size="40" font-weight="700" fill="{INK}"
            letter-spacing="0.5">PDF</text>
      {lines.rstrip()}
    </g>"""


def build() -> str:
    bg_stops = "\n      ".join(
        f'<stop offset="{o:.2f}" stop-color="{c}"/>' for o, c in BG_STOPS
    )
    disc_stops = "\n      ".join(
        f'<stop offset="{o:.2f}" stop-color="{c}" stop-opacity="{a:.2f}"/>'
        for o, c, a in DISC_STOPS
    )
    vig_stops = "\n      ".join(
        f'<stop offset="{o:.2f}" stop-color="{c}" stop-opacity="{a:.2f}"/>'
        for o, c, a in VIGNETTE_STOPS
    )
    dc, vg = DISC, VIGNETTE
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"
     width="512" height="512" role="img" aria-label="Auto-Rotate">
  <defs>
    <linearGradient id="bg" x1="1" y1="0" x2="0" y2="1">
      {bg_stops}
    </linearGradient>
    <radialGradient id="vignette" cx="{vg['cx']}" cy="{vg['cy']}" r="{vg['r']}">
      {vig_stops}
    </radialGradient>
    <linearGradient id="disc" x1="1" y1="0" x2="0" y2="1">
      {disc_stops}
    </linearGradient>
    <radialGradient id="discHi" cx="0.5" cy="0.42" r="0.5">
      <stop offset="0" stop-color="{DISC_HI[0]}" stop-opacity="{DISC_HI[1]}"/>
      <stop offset="1" stop-color="{DISC_HI[0]}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="page" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{PAGE_TOP}"/>
      <stop offset="1" stop-color="{PAGE_BOT}"/>
    </linearGradient>
    <clipPath id="squircle"><path d="{squircle_path()}"/></clipPath>
    <clipPath id="pageclip" clipPathUnits="userSpaceOnUse">
      <path d="{page_body_path()}"/>
    </clipPath>
    <mask id="pagecut" maskUnits="userSpaceOnUse" x="0" y="0" width="512" height="512">
      <rect width="512" height="512" fill="white"/>
      <g transform="{page_transform()}"><path d="{page_cut_path()}" fill="black"/></g>
    </mask>
  </defs>

  <g clip-path="url(#squircle)">
    <rect width="512" height="512" fill="url(#bg)"/>
    <rect width="512" height="512" fill="url(#vignette)"/>
    <circle cx="{dc['cx']}" cy="{dc['cy']}" r="{dc['r']}" fill="url(#disc)"/>
    <circle cx="{dc['cx']}" cy="{dc['cy']}" r="{dc['r']}" fill="url(#discHi)"/>
  </g>

  <g mask="url(#pagecut)">
    {arrow_markup()}
  </g>

  {page_markup()}
</svg>
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build())
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
