# Contributing to Auto-Rotate

Thanks for your interest in improving Auto-Rotate. This project uses
[uv](https://docs.astral.sh/uv/) for everything.

## Development setup

```bash
git clone https://github.com/gedejong/auto-rotate
cd auto-rotate
uv sync --all-extras        # installs runtime + gui + ocr + dev tools
```

For the optional features you'll also want the system binaries:

- **Tesseract** (orientation, OCR): `brew install tesseract` / `apt install tesseract-ocr`
- **OCRmyPDF** (`--ocr`): `brew install ocrmypdf` / `apt install ocrmypdf`

## The checks (must pass before a PR)

```bash
uv run ruff check .            # lint
uv run ruff format --check .   # formatting
uv run pyright                 # strict type-checking
uv run pytest                  # unit suite (system binaries mocked), 85% coverage floor
uv run pytest -m integration   # optional: end-to-end against real tesseract/ocrmypdf
```

CI runs the same matrix across Linux/macOS/Windows and Python 3.11–3.13.

## Running and building the GUI

```bash
uv run auto-rotate-gui                       # run the Toga app directly
uv run briefcase dev                         # run it via Briefcase
uv run briefcase package macOS --adhoc-sign  # build a local .dmg (per-OS; build on the target OS)
```

## Conventions

- Keep the image pipeline (`src/auto_rotate/`) free of GUI/CLI concerns; both front ends
  call `pipeline.deskew_pdf`.
- New optional features that depend on a system binary should degrade gracefully (detect at
  runtime, like `orientation.tesseract_available()` / `ocr.ocrmypdf_available()`).
- Add tests for new logic; GUI widget wiring lives in `gui/app.py` (coverage-omitted) while
  testable logic lives in `gui/controller.py`.
- Update `CHANGELOG.md` under `## [Unreleased]`.
