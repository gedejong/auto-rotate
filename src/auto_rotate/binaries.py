"""Locating external binaries (tesseract, ocrmypdf) robustly.

GUI apps launched from Finder/Dock (or a packaged bundle) do not inherit the shell
``PATH``, so a plain :func:`shutil.which` misses Homebrew/MacPorts installs that work
fine from a terminal. We also search the usual install locations, and expose an
augmented environment so subprocesses (e.g. ocrmypdf, which itself spawns tesseract and
ghostscript) can find their own helpers.
"""

from __future__ import annotations

import os
import shutil
import sys


def _extra_dirs() -> list[str]:
    if sys.platform == "darwin":
        return ["/opt/homebrew/bin", "/usr/local/bin", "/opt/local/bin", "/usr/bin"]
    if sys.platform == "win32":
        return [r"C:\Program Files\Tesseract-OCR", r"C:\Program Files\gs\bin"]
    return ["/usr/local/bin", "/usr/bin", "/bin"]


def find_binary(name: str) -> str | None:
    """Return the absolute path to ``name``, searching PATH then common install dirs.

    Uses :func:`shutil.which` for both lookups, so it honours ``PATHEXT`` on Windows.
    """
    return shutil.which(name) or shutil.which(name, path=os.pathsep.join(_extra_dirs()))


def augmented_env() -> dict[str, str]:
    """A copy of the environment with the common install dirs prepended to PATH."""
    env = dict(os.environ)
    extra = os.pathsep.join(_extra_dirs())
    env["PATH"] = extra + os.pathsep + env.get("PATH", "")
    return env
