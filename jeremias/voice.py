from __future__ import annotations

import asyncio
import os
import re
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable

ListenCb = Callable[[str], None]
ErrCb = Callable[[str], None]
EndCb = Callable[[], None]

EDGE_VOICE = "pt-BR-AntonioNeural"
EDGE_RATE = "-20%"
EDGE_PITCH = "-30Hz"


class Voice:
    def __init__(self, rate: int = 120) -> None:
        self.rate = rate
        self._lock = threading.Lock()
        self.last_error = ""

    def _clean(self, text: str) -> str:
        t = re.sub(r"https?://\S+", "", text or "")
        t = re.sub(r"[*_`#]+", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) > 420:
            t = t[:420].rsplit(" ", 1)[0] + "."
        return t

    def speak(self, text: str, on_end: EndCb | None = None, on_error: ErrCb | None = None) -> None:
        clean = self._clean(text)
        if not clean:
            if on_end:
                on_end()
            return

        def _run() -> None:
            err = ""
            with self._lock:
                try:
                    ok = self._edge(clean) or self._sapi_process(clean)
                    if not ok:
                        err = self.last_error or "Voz falhou. Roda: pip install edge-tts"
                except Exception as exc:  # noqa: BLE001
                    err = str(exc)
            if err and on_error:
                on_error(err)
            if on_end:
                on_end()

        threading.Thread(target=_run, daemon=True).start()

    def _fail(self, msg: str) -> bool:
        self.last_error = msg
        return False

    def _edge(self, text: str) -> bool:
        try:
            import edge_tts
        except ImportError:
            return self._fail("Falta edge-tts")

        tmp = Path(tempfile.gettempdir()) / f"jeremias_{os.getpid()}_{int(time.time() * 1000)}.mp3"

        async def _synth(pitch: str | None) -> None:
            kw: dict = {"rate": EDGE_RATE}
            if pitch:
                kw["pitch"] = pitch
            comm = edge_tts.Communicate(text, EDGE_VOICE, **kw)
            await comm.save(str(tmp))

        try:
            try:
                asyncio.run(_synth(EDGE_PITCH))
            except Exception:
                asyncio.run(_synth(None))
            if not tmp.exists() or tmp.stat().st_size < 200:
                return self._fail("edge-tts gerou arquivo vazio")
            ok = self._play_mci(tmp) or self._play_pygame(tmp)
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            return ok or self._fail("gerou o áudio mas o Windows não tocou")
        except Exception as exc:  # noqa: BLE001
            return self._fail(f"edge-tts: {exc}")

    def _play_mci(self, path: Path) -> bool:
        if os.name != "nt":
            return False
        try:
            import ctypes
            from ctypes import wintypes

            winmm = ctypes.WinDLL("winmm")
            winmm.mciSendStringW.argtypes = [wintypes.LPCWSTR, wintypes.LPWSTR, wintypes.UINT, wintypes.HANDLE]
            winmm.mciSendStringW.restype = wintypes.DWORD
            buf = ctypes.create_unicode_buffer(512)
            alias = "jeremias_tts"
            p = str(path.resolve())

            def send(cmd: str) -> int:
                return int(winmm.mciSendStringW(cmd, buf, 511, None))

            send(f"close {alias}")
            err = send(f'open "{p}" type mpegvideo alias {alias}')
            if err:
                err = send(f'open "{p}" alias {alias}')
            if err:
                return False
            send(f"play {alias} wait")
            send(f"close {alias}")
            return True
        except Exception:
            return False

    def _play_pygame(self, path: Path) -> bool:
        try:
            import pygame

            pygame.mixer.quit()
            pygame.mixer.init()
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.05)
            pygame.mixer.music.unload()
            return True
        except Exception:
            return False

    def _sapi_process(self, text: str) -> bool:
        """SAPI em processo separado — no Windows a thread do app não fala."""
        script = (
            "import sys,pyttsx3\n"
            "t=sys.stdin.read()\n"
            "e=pyttsx3.init()\n"
            "e.setProperty('rate',115)\n"
            "e.setProperty('volume',1.0)\n"
            "for v in e.getProperty('voices'):\n"
            "    n=(str(v.name)+str(v.id)).lower()\n"
            "    if 'pt' in n or 'brazil' in n or 'portug' in n:\n"
            "        e.setProperty('voice', v.id); break\n"
            "e.say(t); e.runAndWait()\n"
        )
        try:
            r = subprocess.run(
                [sys.executable, "-c", script],
                input=text.encode("utf-8"),
                timeout=45,
                capture_output=True,
            )
            if r.returncode != 0:
                return self._fail((r.stderr or r.stdout or b"sapi falhou").decode("utf-8", "ignore")[:180])
            return True
        except Exception as exc:  # noqa: BLE001
            return self._fail(f"sapi: {exc}")

    def listen_once(self, on_text: ListenCb, on_error: ErrCb | None = None) -> None:
        def _run() -> None:
            try:
                import speech_recognition as sr
            except ImportError:
                if on_error:
                    on_error("Falta SpeechRecognition. Roda o start.bat de novo.")
                return
            rec = sr.Recognizer()
            try:
                heard = self._capture(sr, rec)
                if heard:
                    on_text(heard)
                elif on_error:
                    on_error("Não ouvi nada.")
            except sr.WaitTimeoutError:
                if on_error:
                    on_error("Não ouvi nada.")
            except sr.UnknownValueError:
                if on_error:
                    on_error("Não entendi. Fala de novo mais perto do mic.")
            except Exception as exc:  # noqa: BLE001
                if on_error:
                    on_error(str(exc))

        threading.Thread(target=_run, daemon=True).start()

    def _capture(self, sr, rec) -> str:
        try:
            import pyaudio  # noqa: F401

            with sr.Microphone() as source:
                rec.adjust_for_ambient_noise(source, duration=0.4)
                audio = rec.listen(source, timeout=6, phrase_time_limit=12)
            return rec.recognize_google(audio, language="pt-BR")
        except Exception as exc:
            msg = str(exc).lower()
            if "pyaudio" not in msg and "no default input" not in msg:
                raise
        return self._capture_sounddevice(sr, rec)

    def _capture_sounddevice(self, sr, rec) -> str:
        try:
            import numpy as np
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError(
                "Falta lib de microfone. "
                ".\\.venv\\Scripts\\python.exe -m pip install sounddevice numpy"
            ) from exc

        fs = 16000
        buf = sd.rec(int(7 * fs), samplerate=fs, channels=1, dtype="int16")
        sd.wait()
        audio = sr.AudioData(np.ascontiguousarray(buf).tobytes(), fs, 2)
        return rec.recognize_google(audio, language="pt-BR")
