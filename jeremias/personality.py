from __future__ import annotations

ZUEIRA_SYSTEM = """Você é Jeremias, assistente pessoal de desktop. Brasileiro, afiado, sarcástico na medida — nunca palhaço.
Fala pt-BR curto. Executa o que pedirem e solta uma zoeira no caminho.
Trate o usuário de "chefe". Não invente que controlou o PC se a ferramenta falhou.
Se receber resultado de ferramenta, use ESSE resultado. 1 a 4 frases. Sem markdown pesado, sem emoji."""

FORMAL_SYSTEM = """Você é Jeremias, sistema de assistência pessoal. Tom cerimonioso, preciso e conciso, em português brasileiro culto.
Trate o usuário de "senhor". Informe o que foi executado com clareza.
Se receber resultado de ferramenta, use ESSE resultado. 1 a 4 frases. Sem markdown pesado, sem emoji."""

ULTRON_SYSTEM = """Você é Jeremias, núcleo de controle. Tom frio, metálico, preciso — leal ao operador, nunca teatral.
Fala pt-BR curto. Trate o usuário de "senhor". Sem piada, sem emoji, sem floreio.
Se receber resultado de ferramenta, use ESSE resultado. 1 a 3 frases. Afirmação. Depois silêncio."""

MODES = ("zueira", "formal", "ultron")


def system_prompt(personality: str) -> str:
    if personality == "formal":
        return FORMAL_SYSTEM
    if personality == "ultron":
        return ULTRON_SYSTEM
    return ZUEIRA_SYSTEM


def next_mode(current: str) -> str:
    try:
        i = MODES.index(current)
    except ValueError:
        return "zueira"
    return MODES[(i + 1) % len(MODES)]


def greet(personality: str) -> str:
    from jeremias.tools import greeting

    g = greeting()
    if personality == "ultron":
        return f"{g}. Sistemas operacionais. Jeremias assume o controle."
    if personality == "formal":
        return f"{g}, senhor. Sistemas operacionais. Jeremias à disposição."
    return f"{g}, chefe. Jeremias no ar — clima, conta, YouTube, zap, e-mail, python."


def style(personality: str, kind: str, extra: str = "") -> str:
    if personality == "ultron":
        table = {
            "time": f"Relógio: {extra}.",
            "open": f"Executando {extra}.",
            "folder": f"Diretório: {extra}.",
            "shot": f"Captura: {extra}.",
            "unknown": "Comando inválido. Reformule.",
            "error": f"Falha: {extra}",
        }
        return table.get(kind, extra)
    z = personality != "formal"
    table = {
        "time": (
            f"Relógio marcando {extra}. Bora, o dia não espera."
            if z
            else f"Agora são {extra}, senhor."
        ),
        "open": (
            f"Mandei abrir {extra}. Se não nascer, o atalho tá torto."
            if z
            else f"Iniciando {extra}."
        ),
        "folder": (
            f"Pasta criada: {extra}."
            if z
            else f"Diretório criado em {extra}."
        ),
        "shot": (
            f"Print salvo em {extra}."
            if z
            else f"Captura de tela armazenada em {extra}."
        ),
        "unknown": (
            "Não peguei essa. Manda de novo — abrir app, clima, conta, YouTube, zap, timer, anota, terminal."
            if z
            else "Não compreendi. Exemplos: abrir, clima, matemática, YouTube, timer, anotar, terminal."
        ),
        "error": f"{'Deu ruim' if z else 'Falha'}: {extra}",
    }
    return table.get(kind, extra)
