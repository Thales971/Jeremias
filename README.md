# JEREMIAS

Assistente pessoal de **desktop** — não é site. Janela própria, HUD hi-tech (amarelo / preto / cinza / azul-escuro), voz, terminal, pesquisa, clima e interpretador Python.

Inspirado em assistentes open source tipo [Jarvis Desktop Voice Assistant](https://github.com/kishanrajput23/Jarvis-Desktop-Voice-Assistant), reescrito do zero com cara de aplicativo e um cérebro opcional via API da xAI (Grok).

Autor: **Thales Vitor Boehm**

## O que ele faz

- Fala com você (microfone + voz em pt-BR)
- Pesquisa na internet (Wikipedia / DuckDuckGo; se não achar, abre o navegador)
- Temperatura atual (Open-Meteo, padrão: Valinhos)
- Abre apps do PC (Chrome, VS Code, Discord, Spotify, Bloco de notas, etc.)
- Cria pastas na Área de Trabalho
- Roda comando no terminal (com trava pra coisa destrutiva)
- Interpretador Python restrito (`print`, contas, loops)
- Print da tela
- Duas personalidades: **zueira** (padrão) e **formal**

## Windows — do zero

1. Instala [Python 3.11+](https://www.python.org/downloads/) e marca **Add Python to PATH**
2. Baixa este repositório
3. Dá dois cliques em `start.bat`

Ou no terminal:

```bat
cd Jeremias
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config.example.json config.json
python main.py
```

### Microfone (Windows)

`pyaudio` às vezes briga na hora do install. Se o mic falhar:

```bat
pip install pipwin
pipwin install pyaudio
```

Sem microfone o Jeremias ainda funciona: você digita.

### Deixar ele inteligente de verdade

1. Cria uma chave em [console.x.ai](https://console.x.ai)
2. Cola em `config.json` no campo `xai_api_key`

Sem chave ele já abre app, clima, pesquisa, pasta, terminal e Python — só conversa solta que fica mais limitada.

## Exemplos

- `Qual a temperatura em Valinhos?`
- `Abre o Chrome`
- `Cria uma pasta chamada Provas`
- `Pesquisa o que é interpretador`
- `Roda no terminal dir`
- `Roda python: print(sum(range(10)))`
- `Tira um print`

## Segurança

O terminal **não** é um cartão em branco. Comandos tipo `format`, `rm -rf /`, `shutdown` pedem confirmação. O interpretador Python não deixa `open` / `subprocess`. O app roda **local** no seu PC — não tem acesso remoto.

## Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

No Linux instala `portaudio` se quiser microfone (`sudo apt install portaudio19-dev` / equivalente).

## Arquitetura

```
main.py                  # sobe a janela
jeremias/hud.py          # HUD CustomTkinter
jeremias/brain.py        # intenções + Grok opcional
jeremias/voice.py        # fala / escuta
jeremias/tools.py        # PC, terminal, clima, busca, python
jeremias/personality.py  # zueira / formal
```

## Licença

MIT
