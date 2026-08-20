"""Jeremias — assistente pessoal de desktop."""

from __future__ import annotations

import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    try:
        import customtkinter  # noqa: F401
    except ImportError:
        print("Falta o CustomTkinter. Roda:  pip install -r requirements.txt")
        sys.exit(1)

    from jeremias.hud import launch

    launch()


if __name__ == "__main__":
    main()
