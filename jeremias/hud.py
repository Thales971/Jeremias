from __future__ import annotations

import queue
import tkinter as tk
from tkinter import messagebox
from typing import Any

import customtkinter as ctk

from jeremias import brain, config, personality
from jeremias.voice import Voice

BG = "#05070c"
NAVY = "#0b1220"
PANEL = "#101827"
LINE = "#243049"
YELLOW = "#f0c43a"
STEEL = "#8b93a7"
FG = "#e7edf7"


class JeremiasApp(ctk.CTk):
    def __init__(self) -> None:
        super().__init__()
        self.cfg = config.load()
        self.history: list[dict[str, str]] = []
        self.voice = Voice(rate=int(self.cfg.get("voice_rate") or 175))
        self.bus: queue.Queue[tuple[str, Any]] = queue.Queue()
        self.angle = 0
        self.busy = False

        ctk.set_appearance_mode("dark")
        self.title("JEREMIAS")
        self.geometry("1180x740")
        self.minsize(860, 600)
        self.configure(fg_color=BG)

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_left()
        self._build_center()
        self._build_right()

        self.after(40, self._tick)
        self.after(80, self._drain)
        self._log("jeremias", personality.greet(self.cfg["personality"]))
        if self.cfg.get("voice_enabled", True):
            self.voice.speak(personality.greet(self.cfg["personality"]))

    def _build_left(self) -> None:
        side = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=16, width=250)
        side.grid(row=0, column=0, sticky="nsew", padx=(16, 8), pady=16)
        side.grid_propagate(False)
        ctk.CTkLabel(
            side,
            text="JEREMIAS",
            text_color=YELLOW,
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
        ).pack(pady=(18, 4))
        ctk.CTkLabel(side, text="SISTEMA ONLINE", text_color=STEEL, font=ctk.CTkFont(size=11)).pack()
        self.canvas = tk.Canvas(side, width=210, height=210, bg=NAVY, highlightthickness=0)
        self.canvas.pack(pady=16)
        self.status = ctk.CTkLabel(side, text="idle", text_color=YELLOW, font=ctk.CTkFont(size=12))
        self.status.pack()
        self.persona_btn = ctk.CTkButton(
            side,
            text=f"modo {self.cfg['personality']}",
            fg_color=PANEL,
            hover_color=LINE,
            text_color=FG,
            command=self._toggle_persona,
        )
        self.persona_btn.pack(padx=16, pady=(20, 8), fill="x")
        ctk.CTkButton(
            side,
            text="tela cheia",
            fg_color=PANEL,
            hover_color=LINE,
            text_color=FG,
            command=self._toggle_full,
        ).pack(padx=16, pady=4, fill="x")

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
            placeholder_text="Fala ou digita um comando…",
            fg_color=BG,
            border_color=LINE,
            text_color=FG,
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=8)
        self.entry.bind("<Return>", lambda _e: self._submit())
        ctk.CTkButton(bar, text="mic", width=56, fg_color=YELLOW, text_color=BG, command=self._mic).grid(
            row=0, column=1, padx=(0, 8)
        )
        ctk.CTkButton(bar, text="enviar", width=80, fg_color=YELLOW, text_color=BG, command=self._submit).grid(
            row=0, column=2
        )

    def _build_right(self) -> None:
        side = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=16, width=260)
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
            height=280,
        )
        self.term.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        self.term.configure(state="disabled")
        for label, cmd in (
            ("clima agora", "Qual a temperatura em Valinhos?"),
            ("abrir chrome", "Abre o Chrome"),
            ("pasta Teste", "Cria uma pasta chamada Teste"),
            ("python 2+2", "Roda python: print(2+2)"),
            ("print da tela", "Tira um print"),
        ):
            ctk.CTkButton(
                side,
                text=label,
                fg_color=PANEL,
                hover_color=LINE,
                text_color=FG,
                command=lambda c=cmd: self._submit(c),
            ).pack(fill="x", padx=12, pady=3)

    def _toggle_persona(self) -> None:
        self.cfg["personality"] = "formal" if self.cfg["personality"] == "zueira" else "zueira"
        config.save(self.cfg)
        self.persona_btn.configure(text=f"modo {self.cfg['personality']}")
        self._log("jeremias", f"Personalidade: {self.cfg['personality']}.")

    def _toggle_full(self) -> None:
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

    def _log(self, who: str, text: str) -> None:
        self.chat.configure(state="normal")
        prefix = "VOCÊ" if who == "user" else "JEREMIAS"
        self.chat.insert("end", f"{prefix}\n{text}\n\n")
        self.chat.configure(state="disabled")
        self.chat.see("end")

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
                elif kind == "confirm":
                    msg, box = payload
                    box.put(bool(messagebox.askyesno("Jeremias", msg)))
                elif kind == "done":
                    reply, hits = payload
                    self.busy = False
                    self._set_status("idle")
                    self._log("jeremias", reply)
                    for h in hits:
                        if h["tool"] in {"terminal", "code"}:
                            self._term(f"$ {h['arg']}\n{h['result']}")
                    if self.cfg.get("voice_enabled", True):
                        self.voice.speak(reply)
        except queue.Empty:
            pass
        self.after(80, self._drain)

    def _tick(self) -> None:
        c = self.canvas
        c.delete("all")
        cx = cy = 105
        c.create_oval(cx - 92, cy - 92, cx + 92, cy + 92, outline=LINE, width=1)
        c.create_oval(cx - 70, cy - 70, cx + 70, cy + 70, outline=STEEL, width=1)
        c.create_arc(
            cx - 86,
            cy - 86,
            cx + 86,
            cy + 86,
            start=self.angle,
            extent=48,
            outline=YELLOW,
            width=3,
            style="arc",
        )
        c.create_arc(
            cx - 54,
            cy - 54,
            cx + 54,
            cy + 54,
            start=-self.angle * 1.4,
            extent=70,
            outline=STEEL,
            width=2,
            style="arc",
        )
        c.create_oval(cx - 12, cy - 12, cx + 12, cy + 12, fill=YELLOW, outline="")
        step = 8 if self.busy else 3
        self.angle = (self.angle + step) % 360
        self.after(33, self._tick)


def launch() -> None:
    app = JeremiasApp()
    app.mainloop()
