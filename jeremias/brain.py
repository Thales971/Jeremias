from __future__ import annotations

import json
import re
from typing import Any, Callable
from urllib.request import Request, urlopen

from jeremias import personality as persona
from jeremias import tools

ConfirmFn = Callable[[str], bool]


def _strip(text: str) -> str:
    return re.sub(r"[\u0300-\u036f]", "", text.lower().encode("utf-8", "ignore").decode("utf-8"))


def detect(raw: str) -> list[tuple[str, str]]:
    t = raw.lower()
    out: list[tuple[str, str]] = []
    if re.search(r"\b(temperatura|clima|previs[aã]o do tempo|(como|qual).{0,12}tempo)\b", t):
        m = re.search(r"\b(?:em|de|pra|para)\s+([A-Za-zÀ-ÿ\s]{2,40})$", raw, re.I)
        out.append(("weather", (m.group(1) if m else "Valinhos").strip()))
    if re.search(r"\b(pesquis(a|ar)|busca[r]?|o que [eé]|quem [eé]|wikipedia|google)\b", t):
        arg = re.sub(r"^(jeremias[,:\s]*)", "", raw, flags=re.I)
        arg = re.sub(
            r"^(pesquisa[r]?|busca[r]?|google|wikipedia|o que é|quem é)\s+",
            "",
            arg,
            flags=re.I,
        ).strip()
        if arg:
            out.append(("search", arg))
    if re.search(r"\b(hora|horas s[aã]o|que dia|data de hoje)\b", t):
        out.append(("time", ""))
    if re.search(r"\b(abr[aei]|inicia[r]?|abre o|abrir o)\b", t):
        arg = re.sub(r"^(jeremias[,:\s]*)", "", raw, flags=re.I)
        arg = re.sub(r"^(abre|abra|abrir|inicia|iniciar)(\s+o|\s+a)?\s+", "", arg, flags=re.I).strip()
        if arg:
            out.append(("open", arg))
    if re.search(r"\b(cria[r]?\s+(uma\s+)?pasta|mkdir|nova pasta)\b", t):
        m = re.search(r"(?:pasta|mkdir)\s+(?:chamada|com o nome|nome)?\s*[\"']?([^\"']+)[\"']?", raw, re.I)
        out.append(("folder", (m.group(1) if m else "Jeremias").strip()))
    if re.search(r"\b(screenshot|captura de tela|tira um print|print da tela)\b", t) and "print(" not in raw.lower():
        out.append(("screenshot", ""))
    if re.search(r"\b(terminal|cmd|powershell|prompt|roda o comando|executa o comando)\b", t):
        arg = re.sub(r"^.*?(terminal|cmd|powershell|comando)\s*[:\-]?\s*", "", raw, flags=re.I).strip()
        out.append(("terminal", arg or "whoami"))
    if re.search(r"\b(python|interpreta|roda esse c[oó]digo|executa esse c[oó]digo)\b", t) or "```" in raw or "print(" in raw:
        fenced = re.search(r"```(?:python)?\s*([\s\S]*?)```", raw, re.I)
        arg = (fenced.group(1) if fenced else re.sub(r"^.*?(python|c[oó]digo)\s*[:\-]?\s*", "", raw, flags=re.I)).strip()
        if arg:
            out.append(("code", arg))
    return out


def run_tools(raw: str, city_default: str, confirm: ConfirmFn | None) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for tool, arg in detect(raw):
        try:
            if tool == "weather":
                result = tools.weather(arg or city_default)
            elif tool == "search":
                result = tools.search(arg)
            elif tool == "time":
                result = tools.now_pt()
            elif tool == "open":
                result = f"Aberto: {tools.open_app(arg)}"
            elif tool == "folder":
                result = f"Pasta: {tools.create_folder(arg)}"
            elif tool == "screenshot":
                result = f"Print: {tools.screenshot()}"
            elif tool == "terminal":
                result = tools.run_terminal(arg, confirm=confirm)
            elif tool == "code":
                result = tools.run_python(arg)
            else:
                result = "ferramenta desconhecida"
            hits.append({"tool": tool, "arg": arg, "result": result})
        except Exception as exc:  # noqa: BLE001
            hits.append({"tool": tool, "arg": arg, "result": f"Falha ({tool}): {exc}"})
    return hits


def _grok(api_key: str, personality: str, history: list[dict[str, str]], user: str) -> str:
    payload = {
        "model": "grok-4.5",
        "temperature": 0.7 if personality != "formal" else 0.35,
        "max_tokens": 320,
        "messages": [{"role": "system", "content": persona.system_prompt(personality)}, *history[-10:], {"role": "user", "content": user}],
    }
    req = Request(
        "https://api.x.ai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    with urlopen(req, timeout=45) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return (body["choices"][0]["message"]["content"] or "").strip()


def think(
    message: str,
    cfg: dict[str, Any],
    history: list[dict[str, str]],
    confirm: ConfirmFn | None = None,
) -> tuple[str, list[dict[str, str]]]:
    personality = cfg.get("personality") or "zueira"
    hits = run_tools(message, cfg.get("city") or "Valinhos", confirm)
    tool_block = ""
    if hits:
        tool_block = "\n\n[resultados de ferramentas]\n" + "\n".join(
            f"- {h['tool']}: {h['result']}" for h in hits
        )

    key = (cfg.get("xai_api_key") or "").strip()
    if key:
        try:
            reply = _grok(key, personality, history, message + tool_block)
            if reply:
                return reply, hits
        except Exception as exc:  # noqa: BLE001
            if hits:
                return hits[0]["result"] + f"\n(LLM offline: {exc})", hits
            return persona.style(personality, "error", str(exc)), hits

    if hits:
        h = hits[0]
        if h["tool"] == "time":
            return persona.style(personality, "time", h["result"]), hits
        if h["tool"] == "open":
            return persona.style(personality, "open", h["arg"]), hits
        if h["tool"] == "folder":
            return persona.style(personality, "folder", h["result"]), hits
        if h["tool"] == "screenshot":
            return persona.style(personality, "shot", h["result"]), hits
        return h["result"], hits

    if re.search(r"\b(oi|ol[aá]|eae|e ai|bom dia|boa tarde|boa noite)\b", message.lower()):
        return persona.greet(personality), hits
    return persona.style(personality, "unknown"), hits
