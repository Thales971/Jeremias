"""Jeremias — assistente pessoal de desktop."""

from __future__ import annotations

import sys
import traceback
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    try:
        import tkinter  # noqa: F401
    except ImportError:
        print("Esse Python veio sem Tkinter (janela gráfica).")
        print("Desinstala e instala de novo em https://www.python.org/downloads/")
        print('Marca "Add python.exe to PATH" e deixa "tcl/tk and IDLE" ligado.')
        return 1

    try:
        import customtkinter  # noqa: F401
    except ImportError:
        print("Falta o CustomTkinter. Roda de novo o start.bat.")
        return 1

    from jeremias.hud import launch

    launch()
    return 0


if __name__ == "__main__":
    try:
        code = main()
    except Exception:
        traceback.print_exc()
        code = 1
    sys.exit(code)
