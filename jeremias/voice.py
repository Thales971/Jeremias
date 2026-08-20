from __future__ import annotations

import threading
from typing import Callable

ListenCb = Callable[[str], None]
ErrCb = Callable[[str], None]


class Voice:
    def __init__(self, rate: int = 175) -> None:
        self.rate = rate
        self._engine = None
        self._rec = None
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
                    on_error("Falta speech_recognition. pip install SpeechRecognition pyaudio")
                return
            rec = sr.Recognizer()
            try:
                with sr.Microphone() as source:
                    rec.adjust_for_ambient_noise(source, duration=0.4)
                    audio = rec.listen(source, timeout=6, phrase_time_limit=12)
                text = rec.recognize_google(audio, language="pt-BR")
                on_text(text)
            except sr.WaitTimeoutError:
                if on_error:
                    on_error("Não ouvi nada.")
            except Exception as exc:  # noqa: BLE001
                if on_error:
                    on_error(str(exc))

        threading.Thread(target=_run, daemon=True).start()
