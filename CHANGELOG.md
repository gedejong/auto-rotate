# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2026-06-05

### Added

- New hand-drawn application logo and a regenerated icon set, used by the desktop
  app (macOS/Windows/Linux) and the README.
- Distribution: published to a Homebrew tap
  (`brew install --cask gedejong/auto-rotate/auto-rotate`, auto-bumped on release);
  winget and Flathub submissions opened.

### Changed

- README documents the unsigned desktop builds and recommends `pipx` for a
  prompt-free install.

## [0.1.0] - 2026-06-05

### Added

- Core pipeline: rasterize a PDF, snap each page to cardinal orientation (Tesseract OSD),
  correct fine skew (jdeskew), and reassemble.
- `--clean`: binarize scanned pages to crisp black-on-white using Sauvola local
  thresholding (keeps thin staff lines / strokes connected on uneven scans).
- `--ocr`: optional searchable text layer via OCRmyPDF.
- `auto-rotate` command-line interface and a Python library API (`deskew_pdf`).
- Cross-platform desktop GUI (`auto-rotate-gui`, Toga) with runtime capability detection
  and before/after previews of the first queued file's first page.
- Native installers via Briefcase (Windows MSI, macOS DMG, Linux deb/rpm/Flatpak).
- BSD-3-Clause license and open-source project scaffolding.

### Fixed

- The desktop app finds `tesseract`/`ocrmypdf` even when they are not on `PATH` (common
  install dirs like `/opt/homebrew/bin` are searched), and invokes them by absolute path
  with an augmented environment — so orientation/OCR work in the packaged app instead of
  being greyed out.

[Unreleased]: https://github.com/gedejong/auto-rotate/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/gedejong/auto-rotate/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/gedejong/auto-rotate/releases/tag/v0.1.0
