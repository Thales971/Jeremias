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
    if re.search(r"\b(piada|conta uma piada|me faz rir)\b", t):
        return [("joke", "")]
    if re.search(r"\b(not[ií]cia|manchete|g1)\b", t):
        return [("news", "")]
    if re.search(r"\b(d[oó]lar|euro|cota[cç][aã]o)\b", t):
        return [("fx", "")]
    if re.search(r"\b(ip p[uú]blico|meu ip)\b", t):
        return [("ip", "")]
    if re.search(r"\b(traduz|translate)\b", t):
        return [("translate", raw)]
    if re.search(r"\b(gera(r)? senha|senha forte)\b", t):
        n = re.search(r"(\d+)", t)
        return [("password", n.group(1) if n else "16")]
    if re.search(r"\b(escolhe entre|escolhe)\b.+\bou\b", t):
        return [("choose", raw)]
    if re.search(r"\b(faltam quantos dias|quantos dias faltam|countdown)\b", t):
        return [("countdown", raw)]
    if re.search(r"\b(acha o arquivo|procura o arquivo|busca arquivo|onde est[aá] o arquivo)\b", t):
        return [("find", raw)]
    if re.search(r"\b(pr[oó]xima (m[uú]sica|faixa))\b", t):
        return [("media", "next")]
    if re.search(r"\b((m[uú]sica|faixa) anterior)\b", t):
        return [("media", "prev")]
    if re.search(r"\b(pausa a m[uú]sica|toca a m[uú]sica|play.?pause|continua a m[uú]sica)\b", t):
        return [("media", "play")]
    if re.search(r"\bpomodoro\b", t):
        return [("pomodoro", "")]
    if re.search(r"\b(me avisa|timer|alarme|me lembra)\b", t) or re.search(
        r"\b(daqui a|em)\s+\d+\s*(minuto|minutos|segundo|segundos|hora|horas)\b", t
    ):
        return [("timer", raw)]
    if re.search(r"\b(minhas notas|l[eê] as notas|mostra as notas)\b", t):
        return [("notes", "")]
    if re.search(r"\b(anota[r]?|nota que)\b", t):
        return [("note", raw)]
    if re.search(r"\b(area de transferencia|área de transferência|clipboard|o que tem copiado)\b", t):
        return [("clipget", "")]
    if re.search(r"\b(copia(r)? (isso|isto|o texto)|copia:)\b", t):
        return [("clipset", raw)]
    if re.search(r"\b(cpu|mem[oó]ria|status do pc|uso do pc|recursos|vitals)\b", t):
        return [("sysinfo", "")]
    if re.search(r"\b(lista|mostra)\b.+\b(desktop|area de trabalho|área de trabalho|documentos|downloads)\b", t):
        if "download" in t:
            arg = "downloads"
        elif "documento" in t:
            arg = "documentos"
        else:
            arg = "desktop"
        return [("listdir", arg)]
    if re.search(r"\b(whatsapp|zap|wpp)\b", t):
        return [("whatsapp", raw)]
    if re.search(r"\b(email|e-mail)\b", t) and "@" in raw:
        return [("email", raw)]
    if re.search(r"\bgmail\b", t) and "@" not in raw:
        return [("gmail", "")]
    if re.search(r"\byoutube\b", t):
        q = re.sub(r"^.*youtube\s*", "", raw, flags=re.I)
        q = re.sub(r"^(abre|abrir|pesquisa|busca)\s*", "", q, flags=re.I).strip()
        return [("youtube", q)]
    if re.search(r"\b(iniciar com o windows|comecar com o windows|auto[- ]?start|iniciar automaticamente)\b", t):
        return [("autostart", "")]
    if re.search(r"\b(trava|bloquear|lock)\b.*\b(pc|tela|windows|sessao)\b", t) or t.strip() in {"trava o pc", "bloquear tela"}:
        return [("lock", "")]
    if re.search(r"\b(aumenta|sobe)\b.*\bvolume\b", t):
        return [("volume", "up")]
    if re.search(r"\b(diminui|abaixa)\b.*\bvolume\b", t):
        return [("volume", "down")]
    if re.search(r"\bmute\b|\bmuta o som\b|\bsilencia\b", t):
        return [("volume", "mute")]
    lang = re.search(r"\broda em (python|py|node|js|javascript|powershell|ps|cmd|bash|sh|ruby|php|lua)\b", t)
    if lang:
        arg = re.sub(r"^.*?roda em \w+\s*[:\-]?\s*", "", raw, flags=re.I).strip()
        return [("lang", lang.group(1) + "|||" + arg)]
    if re.search(r"\b(terminal|cmd|powershell|prompt|roda o comando|executa o comando)\b", t):
        arg = re.sub(r"^.*?(terminal|cmd|powershell|comando)\s*[:\-]?\s*", "", raw, flags=re.I).strip()
        return [("terminal", arg or "whoami")]
    mathy = re.search(
        r"\b(calcula|calcule|quanto [eé]|seno|cosseno|tangente|raiz|fatorial|equa[cç][aã]o|elevado a)\b",
        t,
    ) or re.search(r"\b(sen|cos|tan|ln)\s*[\(\d]", t) or re.search(r"\blog\s*[\(\d]", t) \
      or re.search(r"\d+\s*[+\-*/^x]\s*\d+", t) or re.search(r"^\s*\d+\s*!\s*$", t)
    if mathy and not re.search(r"\b(abrir|abre|pasta|chrome|terminal|python|print\s*\()\b", t):
        return [("math", raw)]
    if re.search(r"\b(temperatura|clima|previs[aã]o do tempo|(como|qual).{0,12}tempo)\b", t):
        m = re.search(r"\b(?:em|de|pra|para)\s+([A-Za-zÀ-ÿ\s]{2,40})$", raw, re.I)
        out.append(("weather", (m.group(1) if m else "Valinhos").strip()))
    if re.search(r"\b(pesquis(a|ar)|busca[r]?|wikipedia|o que [eé])\b", t) or (
        re.search(r"\bquem [eé]\b", t) and not re.search(r"\b(voc[eê]|tu|vc)\b", t)
    ):
        arg = re.sub(r"^(jeremias[,:\s]*)", "", raw, flags=re.I)
        arg = re.sub(
            r"^(pesquisa[r]?|busca[r]?|wikipedia|o que é|quem é)\s+",
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
            elif tool == "joke":
                result = tools.joke()
            elif tool == "youtube":
                result = tools.youtube(arg)
            elif tool == "gmail":
                result = tools.open_site("https://mail.google.com", "Gmail")
            elif tool == "whatsapp":
                result = tools.whatsapp(arg)
            elif tool == "email":
                result = tools.email(arg)
            elif tool == "math":
                result = tools.math_eval(arg)
            elif tool == "autostart":
                result = tools.enable_autostart()
            elif tool == "lock":
                result = tools.lock_pc()
            elif tool == "volume":
                result = tools.volume(arg)
            elif tool == "lang":
                lang, code = arg.split("|||", 1)
                result = tools.run_lang(lang, code, confirm=confirm)
            elif tool == "timer":
                result = tools.arm_timer(arg)
            elif tool == "note":
                result = tools.note_add(arg)
            elif tool == "notes":
                result = tools.note_list()
            elif tool == "clipget":
                result = tools.clipboard_get()
            elif tool == "clipset":
                text = re.sub(r"^.*?(copia(r)? (isso|isto|o texto)|copia:)\s*", "", arg, flags=re.I).strip()
                result = tools.clipboard_set(text)
            elif tool == "sysinfo":
                result = tools.sysinfo()
            elif tool == "listdir":
                result = tools.list_known(arg)
            elif tool == "news":
                result = tools.news()
            elif tool == "fx":
                result = tools.fx()
            elif tool == "ip":
                result = tools.public_ip()
            elif tool == "translate":
                result = tools.translate(arg)
            elif tool == "password":
                result = tools.password(int(arg or 16))
            elif tool == "choose":
                result = tools.choose(arg)
            elif tool == "countdown":
                result = tools.countdown(arg)
            elif tool == "find":
                result = tools.find_files(arg)
            elif tool == "media":
                result = tools.media(arg)
            elif tool == "pomodoro":
                result = tools.pomodoro()
            else:
                result = "ferramenta desconhecida"
            hits.append({"tool": tool, "arg": arg, "result": result})
        except Exception as exc:  # noqa: BLE001
            hits.append({"tool": tool, "arg": arg, "result": f"Falha ({tool}): {exc}"})
    return hits


def _complete(url: str, key: str, model: str, messages: list[dict[str, str]], extra: dict[str, str] | None = None) -> str:
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
    if extra:
        headers.update(extra)
    payload = {"model": model, "temperature": 0.7, "max_tokens": 320, "messages": messages}
    req = Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
    with urlopen(req, timeout=25) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return (body["choices"][0]["message"]["content"] or "").strip()


def _llm(cfg: dict[str, Any], personality: str, history: list[dict[str, str]], user: str) -> str | None:
    messages = [{"role": "system", "content": persona.system_prompt(personality)}, *history[-10:], {"role": "user", "content": user}]
    or_key = (cfg.get("openrouter_api_key") or "").strip()
    if or_key:
        try:
            return _complete(
                "https://openrouter.ai/api/v1/chat/completions",
                or_key,
                "meta-llama/llama-3.3-70b-instruct",
                messages,
                {"HTTP-Referer": "https://github.com/Thales971/Jeremias", "X-Title": "Jeremias"},
            )
        except Exception:
            pass
    xai = (cfg.get("xai_api_key") or "").strip()
    if xai:
        try:
            return _complete("https://api.x.ai/v1/chat/completions", xai, "grok-4.5", messages)
        except Exception:
            pass
    groq = (cfg.get("groq_api_key") or "").strip()
    if groq:
        try:
            return _complete("https://api.groq.com/openai/v1/chat/completions", groq, "llama-3.3-70b-versatile", messages)
        except Exception:
            pass
    return None


def think(
    message: str,
    cfg: dict[str, Any],
    history: list[dict[str, str]],
    confirm: ConfirmFn | None = None,
) -> tuple[str, list[dict[str, str]]]:
    personality = cfg.get("personality") or "zueira"
    hits = run_tools(message, cfg.get("city") or "Valinhos", confirm)
    if hits:
        return hits[0]["result"] if len(hits) == 1 else "\n".join(h["result"] for h in hits), hits

    reply = _llm(cfg, personality, history, message)
    if reply:
        return reply, hits

    if re.search(r"\b(oi|ol[aá]|eae|e ai|bom dia|boa tarde|boa noite)\b", message.lower()):
        return persona.greet(personality), hits
    return persona.style(personality, "unknown"), hits
