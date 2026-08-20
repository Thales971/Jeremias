from __future__ import annotations

import threading
from typing import Callable

ListenCb = Callable[[str], None]
ErrCb = Callable[[str], None]


class Voice:
    def __init__(self, rate: int = 175) -> None:
        self.rate = rate
        self._engine = None
        self._lock = threading.Lock()

    def _tts(self):
        if self._engine is None:
            import pyttsx3

            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.rate)
            for v in self._engine.getProperty("voices"):
                name = f"{getattr(v, 'name', '')} {getattr(v, 'id', '')}".lower()
                if "pt" in name or "portug" in name or "brazil" in name:
                    self._engine.setProperty("voice", v.id)
                    break
        return self._engine

    def speak(self, text: str) -> None:
        if not text:
            return

        def _run() -> None:
            with self._lock:
                try:
                    eng = self._tts()
                    eng.say(text)
                    eng.runAndWait()
                except Exception:
                    pass

        threading.Thread(target=_run, daemon=True).start()

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
