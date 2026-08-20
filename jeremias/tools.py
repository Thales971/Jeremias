from __future__ import annotations

import io
import os
import re
import shutil
import subprocess
import webbrowser
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from pathlib import Path
from typing import Callable
from urllib.parse import quote

import requests

ConfirmFn = Callable[[str], bool]

DANGEROUS = re.compile(
    r"(format\s+|mkfs|rm\s+-rf\s+[\\/]|del\s+/[fs]|rd\s+/s|reg\s+delete|"
    r"shutdown|restart|reboot|diskpart|cipher\s+/w)",
    re.I,
)

APP_ALIASES = {
    "chrome": ["chrome", "google-chrome", "google-chrome-stable"],
    "google": ["chrome", "msedge", "firefox"],
    "navegador": ["chrome", "msedge", "firefox"],
    "edge": ["msedge", "microsoft-edge"],
    "firefox": ["firefox"],
    "notepad": ["notepad"],
    "bloco de notas": ["notepad"],
    "calculadora": ["calc", "gnome-calculator"],
    "calc": ["calc"],
    "explorer": ["explorer"],
    "arquivos": ["explorer", "nautilus"],
    "vscode": ["code"],
    "code": ["code"],
    "discord": ["discord"],
    "spotify": ["spotify"],
    "steam": ["steam"],
    "word": ["winword"],
    "excel": ["excel"],
    "paint": ["mspaint"],
    "cmd": ["cmd"],
    "powershell": ["powershell"],
    "terminal": ["wt", "powershell", "gnome-terminal"],
    "whatsapp": ["whatsapp"],
}


def desktop_dir() -> Path:
    home = Path.home()
    for name in ("Desktop", "Área de Trabalho", "OneDrive/Desktop", "OneDrive/Área de Trabalho"):
        p = home / name if "/" not in name else home / Path(name)
        if p.exists():
            return p
    return home


def now_pt() -> str:
    return datetime.now().strftime("%A, %d/%m/%Y %H:%M").capitalize()


def weather(city: str = "Valinhos") -> str:
    geo = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": city, "count": 1, "language": "pt"},
        timeout=10,
    )
    geo.raise_for_status()
    results = geo.json().get("results") or []
    if not results:
        return f'Não achei a cidade "{city}".'
    loc = results[0]
    w = requests.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
            "timezone": "America/Sao_Paulo",
        },
        timeout=10,
    )
    w.raise_for_status()
    c = w.json()["current"]
    codes = {
        0: "céu limpo",
        1: "principalmente limpo",
        2: "parcialmente nublado",
        3: "nublado",
        45: "nevoeiro",
        61: "chuva fraca",
        63: "chuva",
        65: "chuva forte",
        80: "pancadas",
        95: "trovoada",
    }
    desc = codes.get(c["weather_code"], "condição indefinida")
    where = loc["name"] + (f", {loc['admin1']}" if loc.get("admin1") else "")
    return (
        f"{where}: {c['temperature_2m']}°C, {desc}. "
        f"Umidade {c['relative_humidity_2m']}%, vento {round(c['wind_speed_10m'])} km/h."
    )


def search(query: str) -> str:
    wiki = requests.get(
        f"https://pt.wikipedia.org/api/rest_v1/page/summary/{quote(query)}",
        headers={"User-Agent": "Jeremias/1.0 (desktop assistant)"},
        timeout=10,
    )
    if wiki.ok:
        data = wiki.json()
        if data.get("extract") and data.get("type") != "disambiguation":
            return f"{data.get('title')}: {data['extract']}"
    ddg = requests.get(
        "https://api.duckduckgo.com/",
        params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
        timeout=10,
    )
    if ddg.ok:
        data = ddg.json()
        text = data.get("AbstractText") or data.get("Answer")
        if text:
            return f"{data.get('Heading') or query}: {text}"
    webbrowser.open(f"https://duckduckgo.com/?q={quote(query)}")
    return f'Abri a busca no navegador para "{query}".'


def open_app(name: str) -> str:
    raw = name.strip()
    key = raw.lower()
    if key in {"youtube", "yt"}:
        webbrowser.open("https://youtube.com")
        return "YouTube"
    if key.startswith("http://") or key.startswith("https://"):
        webbrowser.open(raw)
        return raw
    candidates = APP_ALIASES.get(key, [key])
    for exe in candidates:
        found = shutil.which(exe)
        if found:
            subprocess.Popen([found], shell=False)
            return exe
        if os.name == "nt":
            try:
                os.startfile(exe)  # type: ignore[attr-defined]
                return exe
            except OSError:
                continue
    if os.name == "nt":
        subprocess.Popen(f"start {raw}", shell=True)
        return raw
    raise FileNotFoundError(f"Não achei o app {raw}")


def create_folder(name: str) -> str:
    raw = name.strip().strip("\"'")
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = desktop_dir() / raw
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


def screenshot() -> str:
    try:
        from PIL import ImageGrab
    except ImportError as exc:
        raise RuntimeError("Instala pillow pra print (pip install pillow)") from exc
    dest = desktop_dir() / f"jeremias_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    ImageGrab.grab().save(dest)
    return str(dest)


def run_terminal(command: str, confirm: ConfirmFn | None = None) -> str:
    cmd = command.strip()
    if not cmd:
        return "Comando vazio."
    if DANGEROUS.search(cmd):
        ok = confirm(f"Comando perigoso:\n{cmd}\n\nExecutar mesmo assim?") if confirm else False
        if not ok:
            return "Cancelado. Jeremias não dispara bomba sem confirmação."
    completed = subprocess.run(
        cmd,
        shell=True,
        capture_output=True,
        text=True,
        timeout=25,
    )
    out = (completed.stdout or "") + (completed.stderr or "")
    out = out.strip() or f"(sem saída, código {completed.returncode})"
    return out[:6000]


SAFE_BUILTINS = {
    "abs": abs,
    "bool": bool,
    "dict": dict,
    "enumerate": enumerate,
    "filter": filter,
    "float": float,
    "int": int,
    "len": len,
    "list": list,
    "max": max,
    "min": min,
    "print": print,
    "range": range,
    "round": round,
    "set": set,
    "sorted": sorted,
    "str": str,
    "sum": sum,
    "tuple": tuple,
    "zip": zip,
}


def run_python(code: str) -> str:
    if re.search(r"\b(__import__|importlib|subprocess|socket|ctypes|open\s*\()\b", code):
        return "Interpretador restrito: sem open/import de sistema. Usa o terminal pra isso."
    buf = io.StringIO()
    env = {"__builtins__": SAFE_BUILTINS}
    try:
        with redirect_stdout(buf), redirect_stderr(buf):
            exec(compile(code, "<jeremias>", "exec"), env, env)  # noqa: S102
    except Exception as exc:  # noqa: BLE001
        return f"{type(exc).__name__}: {exc}"
    return buf.getvalue().strip() or "(sem saída)"
