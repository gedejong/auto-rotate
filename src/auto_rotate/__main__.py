"""Entry point for ``python -m auto_rotate`` and the Briefcase-packaged desktop app.

Briefcase launches the bundled app via ``python -m auto_rotate``, so the package needs a
``__main__`` that starts the GUI event loop. (The CLI lives at the ``auto-rotate`` console
script; the GUI also has its own ``auto-rotate-gui`` gui-script.)
"""

from auto_rotate.gui.app import main

if __name__ == "__main__":
    main().main_loop()
