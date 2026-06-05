# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- GUI: before/after previews of the first queued file's first page.

### Fixed

- GUI/desktop app now finds `tesseract`/`ocrmypdf` even when they are not on `PATH`
  (common install dirs like `/opt/homebrew/bin` are searched), and invokes them by
  absolute path with an augmented environment. Previously the packaged app greyed out
  orientation/OCR despite the binaries being installed.

## [0.1.0] - 2026-06-05

### Added

- Core pipeline: rasterize a PDF, snap each page to cardinal orientation (Tesseract OSD),
  correct fine skew (jdeskew), and reassemble.
- `--clean`: binarize scanned pages to crisp black-on-white using Sauvola local
  thresholding (keeps thin staff lines / strokes connected on uneven scans).
- `--ocr`: optional searchable text layer via OCRmyPDF.
- `auto-rotate` command-line interface and a Python library API (`deskew_pdf`).
- Cross-platform desktop GUI (`auto-rotate-gui`, Toga) with runtime capability detection.
- Native installers via Briefcase (Windows MSI, macOS DMG, Linux deb/rpm/Flatpak).
- BSD-3-Clause license and open-source project scaffolding.

[Unreleased]: https://github.com/gedejong/auto-rotate/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/gedejong/auto-rotate/releases/tag/v0.1.0
