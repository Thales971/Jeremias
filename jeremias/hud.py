from __future__ import annotations

import queue
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from jeremias import brain, config, personality, tools
from jeremias.voice import Voice

BG = "#05070c"
NAVY = "#0b1220"
PANEL = "#101827"
LINE = "#243049"
YELLOW = "#f0c43a"
STEEL = "#8b93a7"
FG = "#e7edf7"
LOG = Path(__file__).resolve().parent.parent / "chat.log"


def brain_label(cfg: dict[str, Any]) -> str:
    if (cfg.get("openrouter_api_key") or "").strip():
        return "cérebro · openrouter"
    if (cfg.get("groq_api_key") or "").strip():
        return "cérebro · groq"
    if (cfg.get("xai_api_key") or "").strip():
        return "cérebro · xai"
    return "cérebro · offline"


class JeremiasApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.cfg = config.load()
        self.cfg["voice_enabled"] = True
        self.history: list[dict[str, str]] = []
        self.cmd_hist: list[str] = []
        self.cmd_i = 0
        self.voice = Voice(rate=int(self.cfg.get("voice_rate") or 130))
        self.bus: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.angle = 0
        self.busy = False
        self.live = False
        self.speaking = False
        self.on_top = bool(self.cfg.get("always_on_top"))

        ctk.set_appearance_mode("dark")
        self.title("JEREMIAS")
        self.geometry("1240x780")
        self.minsize(900, 620)
        self.configure(fg_color=BG)
        self.attributes("-topmost", self.on_top)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_left()
        self._build_center()
        self._build_right()

        tools.set_timer_hook(lambda label: self.bus.put(("timer", label)))
        self.after(40, self._tick)
        self.after(80, self._drain)
        self.after(400, self._boot_weather)
        self.after(10000, self._refresh_vitals)
        hello = personality.greet(self.cfg["personality"])
        status = brain_label(self.cfg)
        self._log("jeremias", hello)
        extra = status if "offline" not in status else status + " — abre Ajustes e cola a chave."
        self._log("jeremias", extra)
        self._speak(hello)

    def _build_left(self) -> None:
        side = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=16, width=258)
        side.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        side.grid_propagate(False)
        ctk.CTkLabel(
            side,
            text="JEREMIAS",
            text_color=YELLOW,
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
        ).pack(pady=(16, 2))
        self.brain_lbl = ctk.CTkLabel(
            side,
            text=brain_label(self.cfg).upper(),
            text_color=YELLOW if "offline" not in brain_label(self.cfg) else STEEL,
            font=ctk.CTkFont(size=11),
        )
        self.brain_lbl.pack()
        self.canvas = tk.Canvas(side, width=200, height=200, bg=NAVY, highlightthickness=0)
        self.canvas.pack(pady=10)
        self.status = ctk.CTkLabel(side, text="idle", text_color=YELLOW, font=ctk.CTkFont(size=12))
        self.status.pack()
        self.clock = ctk.CTkLabel(side, text="", text_color=STEEL, font=ctk.CTkFont(family="Consolas", size=13))
        self.clock.pack()
        self.vitals = ctk.CTkLabel(
            side,
            text="CPU —  RAM —",
            text_color=STEEL,
            font=ctk.CTkFont(family="Consolas", size=11),
            wraplength=230,
        )
        self.vitals.pack(pady=(6, 4))
        self.persona_btn = ctk.CTkButton(
            side,
            text=f"modo {self.cfg['personality']}",
            fg_color=PANEL,
            hover_color=LINE,
            text_color=FG,
            command=self._toggle_persona,
        )
        self.persona_btn.pack(padx=16, pady=(10, 4), fill="x")
        ctk.CTkButton(
            side,
            text="testar voz",
            fg_color=YELLOW,
            hover_color=LINE,
            text_color=BG,
            command=lambda: self._speak("Jeremias no controle. Sistemas operacionais."),
        ).pack(padx=16, pady=3, fill="x")
        ctk.CTkButton(side, text="mic contínuo", fg_color=PANEL, hover_color=LINE, text_color=FG, command=self._toggle_live).pack(
            padx=16, pady=3, fill="x"
        )
        ctk.CTkButton(side, text="ajustes / api key", fg_color=PANEL, hover_color=LINE, text_color=FG, command=self._settings).pack(
            padx=16, pady=3, fill="x"
        )
        ctk.CTkButton(side, text="sempre no topo", fg_color=PANEL, hover_color=LINE, text_color=FG, command=self._toggle_top).pack(
            padx=16, pady=3, fill="x"
        )
        ctk.CTkButton(
            side,
            text="iniciar com o windows",
            fg_color=PANEL,
            hover_color=LINE,
            text_color=FG,
            command=lambda: self._submit("Iniciar automaticamente com o Windows"),
        ).pack(padx=16, pady=3, fill="x")
        ctk.CTkButton(side, text="tela cheia", fg_color=PANEL, hover_color=LINE, text_color=FG, command=self._toggle_full).pack(
            padx=16, pady=3, fill="x"
        )

    def _build_center(self) -> None:
        wrap = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=16)
        wrap.grid(row=0, column=1, sticky="nsew", padx=8, pady=16)
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)
        self.chat = ctk.CTkTextbox(
            wrap,
            fg_color=PANEL,
            text_color=FG,
            font=ctk.CTkFont(family="Consolas", size=14),
            wrap="word",
        )
        self.chat.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 8))
        self.chat.configure(state="disabled")
        bar = ctk.CTkFrame(wrap, fg_color="transparent")
        bar.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
        bar.grid_columnconfigure(0, weight=1)
        self.entry = ctk.CTkEntry(
            bar,
            placeholder_text="Fala ou digita — timer, anota, clima, conta…",
            fg_color=BG,
            border_color=LINE,
            text_color=FG,
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=8)
        self.entry.bind("<Return>", lambda _e: self._submit())
        self.entry.bind("<Up>", self._hist_up)
        self.entry.bind("<Down>", self._hist_down)
        ctk.CTkButton(bar, text="mic", width=56, fg_color=YELLOW, text_color=BG, command=self._mic).grid(
            row=0, column=1, padx=(0, 8)
        )
        ctk.CTkButton(bar, text="enviar", width=80, fg_color=YELLOW, text_color=BG, command=self._submit).grid(
            row=0, column=2
        )

    def _build_right(self) -> None:
        side = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=16, width=268)
        side.grid(row=0, column=2, sticky="nsew", padx=(8, 16), pady=16)
        side.grid_propagate(False)
        ctk.CTkLabel(side, text="TERMINAL", text_color=YELLOW, font=ctk.CTkFont(size=12, weight="bold")).pack(
            anchor="w", padx=14, pady=(16, 6)
        )
        self.term = ctk.CTkTextbox(
            side,
            fg_color=BG,
            text_color="#9fecc2",
            font=ctk.CTkFont(family="Consolas", size=12),
            height=220,
        )
        self.term.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.term.configure(state="disabled")
        self.math_lbl = ctk.CTkLabel(
            side,
            text="—",
            text_color=YELLOW,
            font=ctk.CTkFont(family="Consolas", size=16, weight="bold"),
            wraplength=230,
        )
        self.math_lbl.pack(fill="x", padx=12, pady=(4, 8))
        for label, cmd in (
            ("seno de 30", "Seno de 30"),
            ("2x+4=10", "Quanto é 2x+4=10"),
            ("clima agora", "Qual a temperatura em Valinhos?"),
            ("status do pc", "status do pc"),
            ("timer 1 min", "me avisa em 1 minuto prova"),
            ("piada", "Conta uma piada"),
            ("youtube lofi", "Abre o YouTube lofi"),
            ("abrir chrome", "Abre o Chrome"),
        ):
            ctk.CTkButton(
                side,
                text=label,
                fg_color=PANEL,
                hover_color=LINE,
                text_color=FG,
                command=lambda c=cmd: self._submit(c),
            ).pack(fill="x", padx=12, pady=2)

    def _settings(self) -> None:
        win = ctk.CTkToplevel(self)
        win.title("Ajustes — Jeremias")
        win.geometry("460x420")
        win.configure(fg_color=NAVY)
        win.attributes("-topmost", True)
        fields: dict[str, ctk.CTkEntry] = {}
        rows = [
            ("user_name", "nome"),
            ("city", "cidade"),
            ("openrouter_api_key", "openrouter"),
            ("groq_api_key", "groq"),
            ("xai_api_key", "xai"),
        ]
        for key, label in rows:
            ctk.CTkLabel(win, text=label, text_color=STEEL).pack(anchor="w", padx=18, pady=(10, 0))
            e = ctk.CTkEntry(win, fg_color=BG, border_color=LINE, text_color=FG, show="*" if "key" in key else "")
            e.pack(fill="x", padx=18)
            e.insert(0, str(self.cfg.get(key) or ""))
            fields[key] = e

        def save() -> None:
            for k, e in fields.items():
                self.cfg[k] = e.get().strip()
            config.save(self.cfg)
            self.brain_lbl.configure(
                text=brain_label(self.cfg).upper(),
                text_color=YELLOW if "offline" not in brain_label(self.cfg) else STEEL,
            )
            win.destroy()
            self._log("jeremias", "Ajustes salvos. " + brain_label(self.cfg))
            self._speak("Ajustes salvos.")

        ctk.CTkButton(win, text="salvar", fg_color=YELLOW, text_color=BG, command=save).pack(pady=18)

    def _speak(self, text: str) -> None:
        self.speaking = True
        self._set_status("falando")
        self.voice.speak(
            text,
            on_end=lambda: self.bus.put(("spoke", None)),
            on_error=lambda e: self.bus.put(("tts_err", e)),
        )

    def _toggle_live(self) -> None:
        self.live = not self.live
        msg = "Microfone contínuo ligado." if self.live else "Microfone contínuo off."
        self._log("jeremias", msg)
        self._speak(msg)
        if self.live and not self.busy and not self.speaking:
            self._mic()

    def _toggle_persona(self) -> None:
        self.cfg["personality"] = personality.next_mode(self.cfg.get("personality") or "zueira")
        config.save(self.cfg)
        self.persona_btn.configure(text=f"modo {self.cfg['personality']}")
        msg = f"Personalidade: {self.cfg['personality']}."
        self._log("jeremias", msg)
        self._speak(msg)

    def _toggle_top(self) -> None:
        self.on_top = not self.on_top
        self.attributes("-topmost", self.on_top)
        self.cfg["always_on_top"] = self.on_top
        config.save(self.cfg)
        self._log("jeremias", "Sempre no topo." if self.on_top else "Topo off.")

    def _toggle_full(self) -> None:
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

    def _boot_weather(self) -> None:
        def work() -> None:
            try:
                w = tools.weather(self.cfg.get("city") or "Valinhos")
                self.bus.put(("sys", w))
            except Exception:
                pass
            try:
                self.bus.put(("vitals", tools.sysinfo()))
            except Exception:
                pass

        import threading

        threading.Thread(target=work, daemon=True).start()

    def _refresh_vitals(self) -> None:
        def work() -> None:
            try:
                self.bus.put(("vitals", tools.sysinfo()))
            except Exception:
                pass

        import threading

        threading.Thread(target=work, daemon=True).start()
        self.after(12000, self._refresh_vitals)

    def _hist_up(self, _e=None):
        if not self.cmd_hist:
            return
        self.cmd_i = max(0, self.cmd_i - 1)
        self.entry.delete(0, "end")
        self.entry.insert(0, self.cmd_hist[self.cmd_i])

    def _hist_down(self, _e=None):
        if not self.cmd_hist:
            return
        self.cmd_i = min(len(self.cmd_hist), self.cmd_i + 1)
        self.entry.delete(0, "end")
        if self.cmd_i < len(self.cmd_hist):
            self.entry.insert(0, self.cmd_hist[self.cmd_i])

    def _log(self, who: str, text: str) -> None:
        self.chat.configure(state="normal")
        prefix = "VOCÊ" if who == "user" else "JEREMIAS"
        self.chat.insert("end", f"{prefix}\n{text}\n\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")
        try:
            with LOG.open("a", encoding="utf-8") as f:
                f.write(f"{datetime.now():%H:%M:%S} {prefix}: {text}\n")
        except OSError:
            pass

    def _term(self, text: str) -> None:
        self.term.configure(state="normal")
        self.term.insert("end", text.rstrip() + "\n")
        self.term.configure(state="disabled")
        self.term.see("end")

    def _set_status(self, s: str) -> None:
        self.status.configure(text=s)

    def _submit(self, preset: str | None = None) -> None:
        text = (preset if preset is not None else self.entry.get()).strip()
        if not text or self.busy:
            return
        self.entry.delete(0, "end")
        self.cmd_hist.append(text)
        self.cmd_i = len(self.cmd_hist)
        self._log("user", text)
        self.busy = True
        self._set_status("processando")

        def work() -> None:
            def confirm(msg: str) -> bool:
                box: queue.Queue[bool] = queue.Queue()
                self.bus.put(("confirm", (msg, box)))
                try:
                    return box.get(timeout=60)
                except queue.Empty:
                    return False

            try:
                reply, hits = brain.think(text, self.cfg, self.history, confirm=confirm)
            except Exception as exc:  # noqa: BLE001
                reply, hits = f"Falha: {exc}", []
            self.history.append({"role": "user", "content": text})
            self.history.append({"role": "assistant", "content": reply})
            self.bus.put(("done", (reply, hits)))

        import threading

        threading.Thread(target=work, daemon=True).start()

    def _mic(self) -> None:
        if self.speaking:
            return
        self._set_status("ouvindo")
        self.voice.listen_once(
            on_text=lambda t: self.bus.put(("heard", t)),
            on_error=lambda e: self.bus.put(("voice_err", e)),
        )

    def _drain(self) -> None:
        try:
            while True:
                kind, payload = self.bus.get_nowait()
                if kind == "heard":
                    self._set_status("idle")
                    self._submit(payload)
                elif kind == "voice_err":
                    self._set_status("idle")
                    self._log("jeremias", payload)
                elif kind == "tts_err":
                    self._log("jeremias", f"Voz: {payload}")
                elif kind == "sys":
                    self._log("jeremias", payload)
                elif kind == "vitals":
                    self.vitals.configure(text=str(payload).split(" · ", 1)[-1][:80])
                elif kind == "timer":
                    msg = f"Timer: {payload}"
                    self._log("jeremias", msg)
                    self._speak(msg)
                    messagebox.showinfo("Jeremias", msg)
                elif kind == "confirm":
                    msg, box = payload
                    box.put(bool(messagebox.askyesno("Jeremias", msg)))
                elif kind == "spoke":
                    self.speaking = False
                    self._set_status("idle")
                    if self.live and not self.busy:
                        self._mic()
                elif kind == "done":
                    reply, hits = payload
                    self.busy = False
                    self._set_status("idle")
                    self._log("jeremias", reply)
                    for h in hits:
                        if h["tool"] in {"terminal", "code", "lang"}:
                            self._term(f"$ {h['arg']}\n{h['result']}")
                        if h["tool"] == "math":
                            self.math_lbl.configure(text=h["result"][:80])
                    self._speak(reply)
        except queue.Empty:
            pass
        self.after(80, self._drain)

    def _tick(self) -> None:
        c = self.canvas
        c.delete("all")
        cx = cy = 100
        c.create_oval(cx - 88, cy - 88, cx + 88, cy + 88, outline=LINE, width=1)
        c.create_oval(cx - 66, cy - 66, cx + 66, cy + 66, outline=STEEL, width=1)
        c.create_arc(cx - 82, cy - 82, cx + 82, cy + 82, start=self.angle, extent=48, outline=YELLOW, width=3, style="arc")
        c.create_arc(
            cx - 50, cy - 50, cx + 50, cy + 50, start=-self.angle * 1.4, extent=70, outline=STEEL, width=2, style="arc"
        )
        c.create_oval(cx - 11, cy - 11, cx + 11, cy + 11, fill=YELLOW, outline="")
        self.clock.configure(text=datetime.now().strftime("%H:%M:%S"))
        step = 8 if self.busy or self.speaking else 3
        self.angle = (self.angle + step) % 360
        self.after(33, self._tick)


def launch() -> None:
    app = JeremiasApp()
    app.mainloop()
