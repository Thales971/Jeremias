from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import threading
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
    "gmail": ["gmail"],
    "documentos": ["explorer"],
}

KNOWN_FOLDERS = {
    "documentos": lambda: Path.home() / "Documents",
    "downloads": lambda: Path.home() / "Downloads",
    "imagens": lambda: Path.home() / "Pictures",
    "fotos": lambda: Path.home() / "Pictures",
    "musicas": lambda: Path.home() / "Music",
    "vídeos": lambda: Path.home() / "Videos",
    "videos": lambda: Path.home() / "Videos",
    "desktop": lambda: desktop_dir(),
    "area de trabalho": lambda: desktop_dir(),
    "área de trabalho": lambda: desktop_dir(),
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
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "pt"},
            headers={"User-Agent": "Jeremias/1.0"},
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
            headers={"User-Agent": "Jeremias/1.0"},
            timeout=10,
        )
        if w.status_code == 429:
            return _weather_wttr(city)
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
    except Exception:
        return _weather_wttr(city)


def _weather_wttr(city: str) -> str:
    r = requests.get(
        f"https://wttr.in/{city}",
        params={"format": "j1"},
        headers={"User-Agent": "Jeremias/1.0"},
        timeout=10,
    )
    r.raise_for_status()
    data = r.json()
    cur = data["current_condition"][0]
    area = data.get("nearest_area", [{}])[0]
    where = area.get("areaName", [{}])[0].get("value", city)
    desc = cur["weatherDesc"][0]["value"].lower()
    return (
        f"{where}: {cur['temp_C']}°C, {desc}. "
        f"Umidade {cur['humidity']}%, vento {cur['windspeedKmph']} km/h."
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
    if key in {"gmail"}:
        return open_site("https://mail.google.com", "Gmail")
    if key in {"whatsapp web", "zap web"}:
        return open_site("https://web.whatsapp.com", "WhatsApp Web")
    folder_fn = KNOWN_FOLDERS.get(key)
    if folder_fn:
        path = folder_fn()
        if os.name == "nt":
            os.startfile(path)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(["xdg-open", str(path)])
        return str(path)
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


JOKES = [
    "Por que o livro de matemática se suicidou? Porque tinha muitos problemas.",
    "O zero disse pro oito: que cinto estiloso.",
    "Sabe qual o peixe hidratado? O pi-au.",
    "O que o pato falou pra pata? Vem quá.",
    "Por que o jacaré tirou o filho da escola? Porque ele réptil de ano.",
    "Qual o contrário de volátil? Vem cá sobrinho.",
    "O que a impressora falou pro papel? Esse trabalho é uma viajem.",
    "Dois fios se encontraram. O que um falou pro outro? E aí, terra.",
    "Por que o pinheiro não luta caratê? Porque ele tem medo de karateka.",
]


def joke() -> str:
    import random

    return random.choice(JOKES)


def greeting() -> str:
    h = datetime.now().hour
    if h < 12:
        return "Bom dia"
    if h < 18:
        return "Boa tarde"
    return "Boa noite"


def youtube(query: str = "") -> str:
    if query.strip():
        webbrowser.open(f"https://www.youtube.com/results?search_query={quote(query.strip())}")
        return f"YouTube: {query.strip()}"
    webbrowser.open("https://www.youtube.com")
    return "YouTube aberto."


def open_site(url: str, label: str) -> str:
    webbrowser.open(url)
    return label


def whatsapp(raw: str) -> str:
    m = re.search(r"(\+?\d[\d\s\-()]{8,})\s*(?:e diz|:|,)?\s*(.*)$", raw, re.I)
    digits = re.sub(r"\D", "", m.group(1)) if m else ""
    if len(digits) == 11:
        digits = "55" + digits
    text = (m.group(2) if m else "Oi").strip() or "Oi"
    url = (
        f"https://wa.me/{digits}?text={quote(text)}"
        if digits
        else f"https://web.whatsapp.com/send?text={quote(text)}"
    )
    webbrowser.open(url)
    return f"WhatsApp {'para ' + digits if digits else ''} — {text}"


def email(raw: str) -> str:
    found = re.search(r"([\w.+-]+@[\w.-]+\.[a-z]{2,})", raw, re.I)
    to = found.group(1) if found else ""
    subject_m = re.search(r"assunto\s+(.+?)(?:\s+corpo\s+|$)", raw, re.I)
    body_m = re.search(r"corpo\s+(.+)$", raw, re.I)
    subject = subject_m.group(1).strip() if subject_m else "Mensagem do Jeremias"
    body = body_m.group(1).strip() if body_m else raw
    webbrowser.open(f"mailto:{to}?subject={quote(subject)}&body={quote(body)}")
    return f"E-mail para {to or '(sem destino)'} · {subject}"


def run_lang(lang: str, code: str, confirm: ConfirmFn | None = None) -> str:
    lang = lang.lower().strip()
    runners = {
        "python": ["python", "-c", code],
        "py": ["python", "-c", code],
        "node": ["node", "-e", code],
        "js": ["node", "-e", code],
        "javascript": ["node", "-e", code],
        "powershell": ["powershell", "-NoProfile", "-Command", code],
        "ps": ["powershell", "-NoProfile", "-Command", code],
        "cmd": ["cmd", "/c", code],
        "bash": ["bash", "-c", code],
        "sh": ["sh", "-c", code],
        "ruby": ["ruby", "-e", code],
        "php": ["php", "-r", code],
        "lua": ["lua", "-e", code],
    }
    argv = runners.get(lang)
    if not argv:
        return run_terminal(code, confirm=confirm)
    completed = subprocess.run(argv, capture_output=True, text=True, timeout=20)
    out = ((completed.stdout or "") + (completed.stderr or "")).strip()
    return out[:6000] or f"(sem saída, código {completed.returncode})"


def volume(action: str) -> str:
    if os.name != "nt":
        return "Volume por atalho só no Windows."
    import ctypes

    key = {"up": 0xAF, "down": 0xAE, "mute": 0xAD}.get(action, 0xAF)
    ctypes.windll.user32.keybd_event(key, 0, 0, 0)
    ctypes.windll.user32.keybd_event(key, 0, 2, 0)
    return {"up": "volume +", "down": "volume -", "mute": "mute"}.get(action, action)


def lock_pc() -> str:
    if os.name != "nt":
        return "Travar a sessão é Windows por enquanto."
    import ctypes

    ctypes.windll.user32.LockWorkStation()
    return "Tela bloqueada."


def enable_autostart() -> str:
    root = Path(__file__).resolve().parent.parent
    if os.name != "nt":
        return "No Windows eu coloco um atalho na pasta Inicializar. Aqui não é Windows."
    startup = Path(os.environ["APPDATA"]) / r"Microsoft\Windows\Start Menu\Programs\Startup"
    startup.mkdir(parents=True, exist_ok=True)
    bat = startup / "Jeremias.bat"
    bat.write_text(
        f'@echo off\ncd /d "{root}"\n'
        "if exist .venv\\Scripts\\pythonw.exe (.venv\\Scripts\\pythonw.exe main.py) else pythonw main.py\n",
        encoding="utf-8",
    )
    return f"Vai abrir com o Windows: {bat}"


def math_eval(question: str) -> str:
    from jeremias.math import evaluate

    data = evaluate(question)
    if not data.get("ok"):
        return data.get("result") or "não calculei"
    return f"{data['expr']}  →  {data['result']}"


ROOT = Path(__file__).resolve().parent.parent
NOTES_PATH = ROOT / "notes.json"
_timer_hook: Callable[[str], None] | None = None


def set_timer_hook(fn: Callable[[str], None] | None) -> None:
    global _timer_hook
    _timer_hook = fn


def parse_delay(raw: str) -> tuple[int, str]:
    t = raw.lower()
    label = re.sub(r".*?(me avisa|timer|alarme|lembra)\s*(pra|para|de|que)?\s*", "", raw, flags=re.I).strip() or "timer"
    sec = 60
    m = re.search(r"(\d+)\s*(hora|horas)\b", t)
    if m:
        sec = int(m.group(1)) * 3600
    m = re.search(r"(\d+)\s*(minuto|minutos|min)\b", t)
    if m:
        sec = int(m.group(1)) * 60
    m = re.search(r"(\d+)\s*(segundo|segundos|seg)\b", t)
    if m:
        sec = int(m.group(1))
    return max(1, min(sec, 24 * 3600)), label


def arm_timer(raw: str) -> str:
    seconds, label = parse_delay(raw)
    def fire() -> None:
        if _timer_hook:
            _timer_hook(label)
    threading.Timer(seconds, fire).start()
    if seconds >= 60:
        human = f"{seconds // 60} min"
    else:
        human = f"{seconds} s"
    return f"Timer {human} armado. {label}"


def note_add(raw: str) -> str:
    text = re.sub(r"^(jeremias[,:\s]*)", "", raw, flags=re.I)
    text = re.sub(r"^(anota[r]?|nota)\s*(que)?\s*", "", text, flags=re.I).strip()
    if not text:
        return "O que eu anoto?"
    items: list = []
    if NOTES_PATH.exists():
        try:
            items = json.loads(NOTES_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            items = []
    items.append({"at": datetime.now().strftime("%d/%m %H:%M"), "text": text})
    NOTES_PATH.write_text(json.dumps(items[-80:], ensure_ascii=False, indent=2), encoding="utf-8")
    return f"Anotado: {text}"


def note_list() -> str:
    if not NOTES_PATH.exists():
        return "Nenhuma nota ainda."
    try:
        items = json.loads(NOTES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return "Arquivo de notas corrompido."
    if not items:
        return "Nenhuma nota ainda."
    return "\n".join(f"- {i['at']} {i['text']}" for i in items[-12:])


def clipboard_get() -> str:
    if os.name != "nt":
        return "Clipboard só no Windows."
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", "Get-Clipboard"],
        capture_output=True,
        text=True,
        timeout=8,
    )
    return (r.stdout or "").strip() or "(área de transferência vazia)"


def clipboard_set(text: str) -> str:
    if os.name != "nt":
        return "Clipboard só no Windows."
    subprocess.run(["clip"], input=text.encode("utf-16le"), timeout=8, check=False)
    return f"Copiado: {text[:80]}"


def sysinfo() -> str:
    parts = [now_pt()]
    try:
        import psutil

        cpu = psutil.cpu_percent(interval=0.35)
        ram = psutil.virtual_memory()
        root = "C:\\" if os.name == "nt" else "/"
        disk = psutil.disk_usage(root)
        parts.append(f"CPU {cpu:.0f}%")
        parts.append(f"RAM {ram.percent:.0f}% ({ram.used // (1024**3)}/{ram.total // (1024**3)} GB)")
        parts.append(f"disco {disk.percent:.0f}%")
    except Exception:
        parts.append("vitals: pip install psutil")
    return " · ".join(parts)


def list_known(name: str) -> str:
    key = name.lower().strip()
    folders = {
        "desktop": desktop_dir,
        "area de trabalho": desktop_dir,
        "área de trabalho": desktop_dir,
        "documentos": lambda: Path.home() / "Documents",
        "downloads": lambda: Path.home() / "Downloads",
    }
    fn = folders.get(key, desktop_dir)
    path = fn()
    if not path.exists():
        return f"Não achei {path}"
    names = sorted(p.name + ("/" if p.is_dir() else "") for p in path.iterdir())[:40]
    return f"{path}:\n" + "\n".join(names)
