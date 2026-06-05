"""Toga desktop front end for auto_rotate.

Thin widget shell over :mod:`auto_rotate.gui.controller`. Capability gating, file
selection, and a background worker that streams per-page progress into a log.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW

from ..pipeline import PageResult
from .controller import Options, available_features, default_output_path, process_file

APP_ID = "dev.gedejong.autorotate"
FORMAL_NAME = "Auto-Rotate"


class AutoRotateApp(toga.App):
    def startup(self) -> None:
        self._features = available_features()
        self._files: list[Path] = []

        add_btn = toga.Button("Add PDFs…", on_press=self._on_add)
        clear_btn = toga.Button("Clear", on_press=self._on_clear, style=Pack(margin_left=6))
        file_row = toga.Box(children=[add_btn, clear_btn], style=Pack(direction=ROW))
        self._file_label = toga.Label("No files added.")

        self._orient = toga.Switch(
            "Auto-orient pages (Tesseract)",
            value=self._features.orient,
            enabled=self._features.orient,
        )
        self._clean = toga.Switch("Clean to black-on-white", value=False)
        self._ocr = toga.Switch(
            "Add searchable text layer (OCR)", value=False, enabled=self._features.ocr
        )
        self._dpi = toga.NumberInput(min=72, max=1200, step=50, value=300)
        dpi_row = toga.Box(
            children=[toga.Label("DPI:", style=Pack(margin_right=6)), self._dpi],
            style=Pack(direction=ROW),
        )

        self._run_btn = toga.Button("Run", on_press=self._on_run)
        # max=None -> indeterminate spinner (valid at runtime; the stub omits None).
        self._progress = toga.ProgressBar(max=None)  # pyright: ignore[reportArgumentType]
        self._log = toga.MultilineTextInput(readonly=True, style=Pack(flex=1))

        children: list[toga.Widget] = [
            toga.Label("Files", style=Pack(font_weight="bold")),
            file_row,
            self._file_label,
            toga.Label("Options", style=Pack(font_weight="bold", margin_top=8)),
            self._orient,
            self._clean,
            self._ocr,
            dpi_row,
        ]
        if not self._features.orient:
            children.append(
                toga.Label(
                    "Install Tesseract to enable orientation; add OCRmyPDF for OCR.",
                    style=Pack(margin_top=4),
                )
            )
        children += [
            self._run_btn,
            self._progress,
            toga.Label("Log", style=Pack(font_weight="bold", margin_top=8)),
            self._log,
        ]

        # Hold a precisely-typed reference; App.main_window's type is a broad union.
        self._window = toga.MainWindow(title=self.formal_name, size=(640, 680))
        self._window.content = toga.Box(
            children=children, style=Pack(direction=COLUMN, margin=12, gap=4)
        )
        self.main_window = self._window
        self._window.show()

    async def _on_add(self, widget: toga.Widget) -> None:
        result = await self._window.dialog(
            toga.OpenFileDialog("Select PDFs", file_types=["pdf"], multiple_select=True)
        )
        if result:
            self._files.extend(Path(p) for p in result)
            self._refresh_files()

    def _on_clear(self, widget: toga.Widget) -> None:
        self._files.clear()
        self._refresh_files()

    def _refresh_files(self) -> None:
        self._file_label.text = "\n".join(f.name for f in self._files) or "No files added."

    def _append(self, text: str) -> None:
        self._log.value = f"{self._log.value}{text}\n" if self._log.value else f"{text}\n"

    def _set_busy(self, busy: bool) -> None:
        self._run_btn.enabled = not busy
        if busy:
            self._progress.start()
        else:
            self._progress.stop()

    async def _on_run(self, widget: toga.Widget) -> None:
        if not self._files:
            self._append("Add at least one PDF first.")
            return

        dpi = int(self._dpi.value) if self._dpi.value is not None else 300
        options = Options(
            dpi=dpi, orient=self._orient.value, clean=self._clean.value, ocr=self._ocr.value
        )
        self._set_busy(True)
        loop = asyncio.get_event_loop()

        for pdf in list(self._files):
            output = default_output_path(pdf)
            self._append(f"Processing {pdf.name} → {output.name}")

            def on_page(result: PageResult, name: str = pdf.name) -> None:
                loop.call_soon_threadsafe(
                    self._append,
                    f"  {name} page {result.index + 1}: "
                    f"cardinal {result.cardinal}° + skew {result.skew:.2f}°",
                )

            def work(p: Path = pdf, o: Path = output) -> list[PageResult]:
                return process_file(p, o, options, on_page=on_page)

            try:
                await loop.run_in_executor(None, work)
                self._append(f"  done → {output}")
            except Exception as exc:  # surface any failure (bad PDF, missing binary) in the log
                self._append(f"  error: {exc}")

        self._set_busy(False)


def main() -> toga.App:
    """Build the app instance (Briefcase entry point)."""
    return AutoRotateApp(
        FORMAL_NAME,
        APP_ID,
        author="Edwin de Jong",
        description="Deskew and turn upright every page of a PDF.",
    )


def run() -> None:
    """Console/GUI-script entry point: build the app and start the event loop."""
    main().main_loop()
