from __future__ import annotations

import asyncio
import re
import tempfile
import threading
import time
from pathlib import Path
from typing import Callable

ListenCb = Callable[[str], None]
ErrCb = Callable[[str], None]
EndCb = Callable[[], None]

# Antonio, grave, frio — o mais perto de Ultron em pt-BR sem API paga.
EDGE_VOICE = "pt-BR-AntonioNeural"
EDGE_RATE = "-18%"
EDGE_PITCH = "-25Hz"


class Voice:
    def __init__(self, rate: int = 130) -> None:
        self.rate = rate
        self._engine = None
        self._lock = threading.Lock()
        self._tmp = Path(tempfile.gettempdir()) / "jeremias-voice.mp3"

    def _clean(self, text: str) -> str:
        t = re.sub(r"https?://\S+", "", text or "")
        t = re.sub(r"[*_`#]+", "", t)
        t = re.sub(r"\s+", " ", t).strip()
        if len(t) > 420:
            t = t[:420].rsplit(" ", 1)[0] + "."
        return t

    def speak(self, text: str, on_end: EndCb | None = None) -> None:
        clean = self._clean(text)
        if not clean:
            if on_end:
                on_end()
            return

        def _run() -> None:
            with self._lock:
                ok = self._speak_edge(clean) or self._speak_sapi(clean)
                if not ok:
                    print("TTS falhou — instala: pip install edge-tts pygame")
            if on_end:
                on_end()

        threading.Thread(target=_run, daemon=True).start()

    def _speak_edge(self, text: str) -> bool:
        try:
            import edge_tts
        except ImportError:
            return False

        async def _synth() -> None:
            comm = edge_tts.Communicate(text, EDGE_VOICE, rate=EDGE_RATE, pitch=EDGE_PITCH)
            await comm.save(str(self._tmp))

        try:
            asyncio.run(_synth())
            return self._play_mp3(self._tmp)
        except Exception:
            return False

    def _play_mp3(self, path: Path) -> bool:
        try:
            import pygame

            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(str(path))
            pygame.mixer.music.set_volume(1.0)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.08)
            return True
        except Exception:
            return False

    def _speak_sapi(self, text: str) -> bool:
        try:
            import pyttsx3
        except ImportError:
            return False
        try:
            if self._engine is None:
                self._engine = pyttsx3.init()
                self._engine.setProperty("rate", max(110, int(self.rate) - 40))
                self._engine.setProperty("volume", 1.0)
                for v in self._engine.getProperty("voices"):
                    name = f"{getattr(v, 'name', '')} {getattr(v, 'id', '')}".lower()
                    if "pt" in name or "portug" in name or "brazil" in name:
                        self._engine.setProperty("voice", v.id)
                        break
            self._engine.say(text)
            self._engine.runAndWait()
            return True
        except Exception:
            return False

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
                text = self._capture(sr, rec)
                if text:
                    on_text(text)
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
                "Falta lib de microfone. No PowerShell, na pasta Jeremias:  "
                ".\\.venv\\Scripts\\python.exe -m pip install sounddevice numpy"
            ) from exc

        fs = 16000
        buf = sd.rec(int(7 * fs), samplerate=fs, channels=1, dtype="int16")
        sd.wait()
        audio = sr.AudioData(np.ascontiguousarray(buf).tobytes(), fs, 2)
        return rec.recognize_google(audio, language="pt-BR")
