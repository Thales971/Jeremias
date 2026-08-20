# JEREMIAS

Assistente pessoal de **desktop** — não é site. Janela própria, HUD hi-tech (amarelo / preto / cinza / azul-escuro), voz, terminal, pesquisa, clima, matemática e interpretador.

Autor: **Thales Vitor Boehm**

Repositório: [github.com/Thales971/Jeremias](https://github.com/Thales971/Jeremias)

## O que ele faz

- Cumprimenta com **bom dia / boa tarde / boa noite** na hora que abre
- Fala e escuta em pt-BR (microfone + voz). Tem mic contínuo.
- Pesquisa (Wikipedia / DuckDuckGo)
- Temperatura (Open-Meteo, plano B: wttr.in) — padrão Valinhos
- Calculadora avançada: trig, raiz, log, fatorial, `2^10`, equação linear `2x+4=10`
- Piadas
- Abre YouTube (com busca), Gmail, WhatsApp (`wa.me`) e e-mail (`mailto:`)
- Abre apps do PC (Chrome, VS Code, Discord, Spotify, Bloco de notas…)
- Abre pastas (Área de Trabalho, Documentos, Downloads…)
- Cria pasta na Área de Trabalho
- Terminal: Python, Node/JS, PowerShell, CMD, bash, ruby, php, lua
- Volume, travar a tela, print da tela
- **Iniciar com o Windows** (atalho na pasta Inicializar)
- Duas personalidades: **zueira** (padrão) e **formal**
- Cérebro via OpenRouter (Llama 3.3) → xAI → Groq, se as chaves existirem no `config.json`

## Windows — passo a passo

1. Instala o [Python 3.11+](https://www.python.org/downloads/) e marca **Add Python to PATH**
2. Baixa o ZIP em [Thales971/Jeremias](https://github.com/Thales971/Jeremias) e extrai
3. Dá dois cliques em `start.bat`

Na primeira vez o `start.bat` cria o `.venv`, instala as libs e copia `config.example.json` → `config.json`.

Ou no terminal:

```bat
cd Jeremias
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy config.example.json config.json
notepad config.json
python main.py
```

### Colocar as chaves de IA (opcional, mas deixa ele conversar de verdade)

Abre o `config.json` e cola **só aí** (esse arquivo **não** vai pro GitHub):

```json
"openrouter_api_key": "sk-or-v1-...",
"groq_api_key": "gsk_..."
```

Ordem que ele tenta: OpenRouter → xAI → Groq.

### Microfone

Se o `pyaudio` brigar no Windows:

```bat
pip install pipwin
pipwin install pyaudio
```

Sem microfone ainda funciona — você digita. No HUD tem o botão **mic** e **mic contínuo**.

### Iniciar junto com o Windows

No app, clica **iniciar com o windows** (ou fala “iniciar automaticamente com o Windows”). Ele solta um `Jeremias.bat` na pasta Inicializar.

## Exemplos de fala

- `Qual a temperatura em Valinhos?`
- `Seno de 30` / `Raiz de 144` / `5 fatorial` / `Quanto é 2x+4=10`
- `Conta uma piada`
- `Abre o YouTube lofi`
- `Abre o Gmail`
- `WhatsApp 19999999999 e diz tô saindo`
- `Manda email pra fulano@gmail.com assunto prova corpo manda o PDF`
- `Abre o Chrome` / `Abre documentos`
- `Cria uma pasta chamada Provas`
- `Roda no terminal dir`
- `Roda em python: print(sum(range(10)))`
- `Roda em node: console.log(2+2)`
- `Tira um print`
- `Trava o PC` / `Aumenta o volume`

## Segurança

- `config.json` está no `.gitignore`. **Nunca** commita chave.
- Terminal bloqueia `format`, `rm -rf`, `shutdown` etc. sem confirmação.
- Interpretador Python rápido não deixa `open` / `subprocess`.
- O app roda **local** no seu PC.

## Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.json config.json
python main.py
```

No Linux, `portaudio` se quiser microfone (`sudo apt install portaudio19-dev`). Auto-start e volume/trava são Windows por enquanto.

## Arquitetura

```
main.py                  # sobe a janela
jeremias/hud.py          # HUD CustomTkinter
jeremias/brain.py        # intenções + LLM
jeremias/math.py         # trig / fatorial / equação
jeremias/voice.py        # fala / escuta
jeremias/tools.py        # PC, terminal, clima, busca, zap, e-mail
jeremias/personality.py  # zueira / formal
```

## Licença

MIT
