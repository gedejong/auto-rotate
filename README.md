# Auto-Rotate

[![CI](https://github.com/gedejong/auto-rotate/actions/workflows/ci.yml/badge.svg)](https://github.com/gedejong/auto-rotate/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/auto-rotate.svg)](https://pypi.org/project/auto-rotate/)
[![Python](https://img.shields.io/pypi/pyversions/auto-rotate.svg)](https://pypi.org/project/auto-rotate/)
[![License: BSD-3-Clause](https://img.shields.io/badge/license-BSD--3--Clause-blue.svg)](LICENSE)

Automatically **deskew and turn upright** every page of a PDF — CLI, Python library, and a
cross-platform desktop app.

Each page is rasterized, snapped to its correct cardinal orientation
(0/90/180/270°) with Tesseract's orientation-and-script detection, then
fine-skew corrected with [`jdeskew`](https://pypi.org/project/jdeskew/)
(FFT + radial projection), and reassembled into a new PDF. Optionally, a
searchable text layer is added with OCRmyPDF.

```
PDF page
  → rasterize @ DPI (pypdfium2)
  → cardinal orientation snap   (Tesseract OSD, lossless np.rot90)   [--orient, default on]
  → fine-skew correction ±15°   (jdeskew, white-filled corners)
  → binarize to black-on-white  (Sauvola local threshold)            [--clean, default off]
  → rebuild PDF (img2pdf)
  → searchable text layer       (OCRmyPDF)                           [--ocr, default off]
```

## Install

**Desktop app (no Python needed)** — download the installer for your OS from the
[latest release](https://github.com/gedejong/auto-rotate/releases): Windows `.msi`,
macOS `.dmg` (Apple Silicon, macOS 14+), or Linux `.deb`/`.rpm`/Flatpak. (Until the app is
code-signed, macOS needs a right-click → Open on first launch, and Windows SmartScreen needs
"Run anyway".)

**CLI / library** via [pipx](https://pipx.pypa.io/) or pip:

```bash
pipx install auto-rotate            # the `auto-rotate` command
pipx install "auto-rotate[ocr]"     # + the `--ocr` capability
pip install auto-rotate             # as a library
```

**From source** with [uv](https://docs.astral.sh/uv/):

```bash
uv sync                  # core
uv sync --all-extras     # core + gui + ocr + dev tools
```

### System binaries

| Feature | Requires |
| --- | --- |
| `--orient` (default) | the **`tesseract`** binary on PATH |
| `--ocr` | **`ocrmypdf`** (the `[ocr]` extra) + `tesseract` |
| `--no-orient` | nothing — pure Python, no system binaries |

On macOS: `brew install tesseract ocrmypdf`.

## Usage

```bash
auto-rotate input.pdf output.pdf                  # cardinal orientation + deskew (image-only)
auto-rotate input.pdf output.pdf --no-orient      # deskew only, no Tesseract needed
auto-rotate input.pdf output.pdf --clean          # + pure black-on-white (great for scans)
auto-rotate input.pdf output.pdf --ocr            # + searchable text layer
auto-rotate input.pdf output.pdf --dpi 400 -v     # higher render DPI, log per-page corrections
```

```
positional: input, output
--dpi N            rasterization DPI (default 300)
--orient/--no-orient   cardinal-orientation detection (default: on)
--angle-max DEG    max fine-skew angle searched (default 15.0)
--clean            binarize to pure black-on-white (flattens scan background)
--ocr              add a searchable text layer (needs ocrmypdf)
-v, --verbose      log the correction applied to each page
```

### Desktop app

```bash
auto-rotate-gui     # if installed via pip/pipx with the [gui] extra
```

Add one or more PDFs, toggle **orient / clean / OCR**, pick a DPI, and Run; each file is
written next to its source as `<name> - upright.pdf`, with per-page progress in the log.
Orientation and OCR controls are enabled only when Tesseract / OCRmyPDF are detected.

### Library

```python
from pathlib import Path
from auto_rotate import deskew_pdf

results = deskew_pdf(Path("scan.pdf"), Path("upright.pdf"), dpi=300, orient=True)
for r in results:
    print(f"page {r.index + 1}: cardinal {r.cardinal}° + skew {r.skew:.2f}°")
```

## Notes & limitations

- The output is **rasterized**. Without `--ocr` it is image-only (no selectable text);
  `--ocr` restores a searchable layer via OCR.
- `jdeskew` only resolves tilt within ±`--angle-max` (default 15°). Gross rotation
  (sideways/upside-down pages) is handled by the orientation stage, so keep
  `--orient` on for arbitrary inputs.
- Tesseract OSD needs a reasonable amount of text to lock onto orientation; on
  blank or text-sparse pages it falls back to leaving the page as-is (0°).
- `--clean` uses a local (Sauvola) threshold, which keeps thin faint strokes (e.g.
  music staff lines) connected far better than a global threshold. It still cannot
  recover ink that is essentially absent from the scan — very faint lines may stay
  broken; raising the render `--dpi` is the best lever there.

## Development

```bash
uv run ruff check . && uv run ruff format --check .
uv run pyright
uv run pytest                  # unit suite (system binaries mocked)
uv run pytest -m integration   # end-to-end tests against real tesseract/ocrmypdf
```
