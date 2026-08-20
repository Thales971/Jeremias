# JEREMIAS

Assistente pessoal de **desktop** — não é site. Janela própria, HUD hi-tech (amarelo / preto / cinza / azul-escuro), voz grave, terminal, pesquisa, clima, matemática.

Autor: **Thales Vitor Boehm** · [github.com/Thales971/Jeremias](https://github.com/Thales971/Jeremias)

## O que ele faz

- Cumprimenta com **bom dia / boa tarde / boa noite**
- Fala **todas** as respostas em voz alta (Edge TTS grave, estilo Ultron) e escuta o mic
- Pesquisa, clima (Valinhos), calculadora (trig, raiz, fatorial, `2x+4=10`)
- Piadas, YouTube, Gmail, WhatsApp, e-mail
- Abre apps e pastas do PC, cria pasta, terminal (Python, Node, PowerShell, CMD, bash…)
- Volume, trava a tela, print, **iniciar com o Windows**
- **Timer** (`me avisa em 5 minutos`)
- **Notas** (`anota que prova é terça` / `minhas notas`)
- **Clipboard** e **status do PC** (CPU/RAM/disco)
- Três modos: **zueira**, **formal**, **ultron**
- Tela **Ajustes** pra colar a API key sem editar JSON na mão
- Sempre no topo, histórico de comandos (seta pra cima)

Cérebro: OpenRouter (Llama 3.3) → xAI → Groq.

## Windows

1. Python 3.11+ em [python.org](https://www.python.org/downloads/) com **Add python.exe to PATH**. No teu PC o comando é `py`.
2. `git clone https://github.com/Thales971/Jeremias.git`
3. `cd Jeremias` e dois cliques em `start.bat`

Ou:

```powershell
cd C:\Users\User\Jeremias
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

### API key

No app: **ajustes / api key** → cola OpenRouter → salvar.

Ou `config.json` (não vai pro GitHub).

## Exemplos

- `Qual a temperatura em Valinhos?`
- `Seno de 30` / `2x+4=10`
- `Me avisa em 1 minuto estudar`
- `Anota que a prova é terça`
- `Status do PC`
- `Abre o Chrome`
- `Conta uma piada`

## Licença

MIT
