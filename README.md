# 🎬 Audiodescrição Automatizada

> **Projeto da Residência Tecnológica Porto Digital × Globo**  
> Grupo **Grow up** · Universidade Tiradentes (UNIT) · 2026.1

Sistema de geração automática de audiodescrição para conteúdos audiovisuais, desenvolvido como solução de acessibilidade para pessoas com deficiência visual, utilizando IA generativa multimodal.

---

## 📌 Contexto

Este projeto foi desenvolvido no âmbito da **Residência Tecnológica Porto Digital × TV Globo**, programa que conecta estudantes da UNIT a desafios reais da indústria de comunicação.

O desafio proposto pela Globo: automatizar a geração de audiodescrição — narração em áudio que descreve elementos visuais de um vídeo para pessoas cegas ou com baixa visão — processo que hoje é feito 100% manualmente por roteiristas especializados.

A solução foi **eleita o melhor projeto da turma** na etapa de validação técnica (Coday).

---

## ✨ Funcionalidades

| Funcionalidade | Descrição |
|---|---|
| 🎬 **Múltiplos formatos** | MP4, MXF (broadcast) e YouTube |
| 🤖 **IA generativa** | Gemini 2.5 Flash analisa o vídeo completo |
| ⏱️ **Calibração automática** | Duração detectada via ffprobe, prompt ajustado para caber no tempo |
| 🏷️ **Nome automático** | Título gerado pelo próprio Gemini com base no conteúdo |
| 🎙️ **Voz neural** | Edge TTS com `pt-BR-FranciscaNeural` |
| 📄 **Exportação SRT** | Legenda no padrão da indústria com timecodes reais |
| 🌐 **Player HTML** | Standalone com legenda sincronizada via SRT + controles |
| 📦 **Modo batch** | Processa vários vídeos em sequência |
| 🔍 **Histórico com busca** | JSON local com todos os vídeos processados |
| 🛡️ **Resiliência** | Fallback entre modelos + retry automático em erros 503/429 |

---

## 🏗️ Arquitetura

```
📁 projeto/
├── main.py            # Orquestrador: menu, batch, histórico
├── gemini_client.py   # Upload, nome automático, audiodescrição
├── srt_generator.py   # Exportação de legenda no formato SRT
├── historico.py       # Persistência e busca de registros em JSON
├── prompts.py         # build_prompt() calibrado pela duração real
├── config.py          # API Key, voz, diretório de saída
├── requirements.txt   # Dependências
└── .env               # GOOGLE_API_KEY (não versionar)
```

### Fluxo de processamento

```
python main.py
      │
      ▼ [menu interativo]
      │
      ├── preparar_video()
      │     ├── MP4/MKV local   → usa direto
      │     ├── MXF broadcast   → converte com FFmpeg (libx264 + aac)
      │     └── YouTube URL     → baixa com yt-dlp
      │
      ├── obter_duracao()       ← ffprobe
      ├── build_prompt()        ← calibra palavras/frases pelo tempo
      │
      ├── client.files.upload() ← envia vídeo para a API
      │
      ├── Gemini 2.5 Flash
      │     ├── Gera título automático (≤ 5 palavras)
      │     └── Gera audiodescrição (NBR 15290, calibrada)
      │
      ├── gerar_srt()           ← timecodes proporcionais
      ├── edge_tts.Communicate  ← MP3 com voz neural
      ├── abrir_player()        ← HTML standalone
      └── registrar()           ← salva no histórico JSON
```

---

## 📐 Calibração de Duração

O principal desafio foi fazer a narração **caber exatamente no vídeo**. A solução:

```python
tempo_util   = duracao_video * 0.85      # margem de 15%
max_palavras = (tempo_util / 60) * 150   # 150 wpm (locutor profissional)
max_frases   = max_palavras / 12         # ~12 palavras por frase de AD
```

Exemplo — vídeo de **34 segundos**:
- Tempo útil: `28.9s`
- Máximo de palavras: `72`
- Máximo de frases: `6`

Esses limites são passados diretamente no prompt ao Gemini.

---

## 🛡️ Resiliência a Falhas

| Erro | Comportamento |
|---|---|
| `503 UNAVAILABLE` | Retry automático: 3 tentativas (15s → 30s → 45s) |
| `429 QUOTA EXCEEDED` | Pula imediatamente para o próximo modelo |
| Fallback de modelos | `gemini-2.5-flash` → `gemini-2.0-flash` → `gemini-1.5-flash` |

---

## 🚀 Instalação e Uso

### Pré-requisitos

- Python 3.10+
- [FFmpeg](https://ffmpeg.org/download.html) instalado e no PATH
- API Key do Google Gemini ([obter aqui](https://aistudio.google.com/app/apikey))

### Instalação

```bash
git clone https://github.com/AnneVz777/Audiodescricao-Automatizada.git
cd Audiodescricao-Automatizada

python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac

python -m pip install -r requirements.txt
```

### Configuração

Crie o arquivo `.env` na raiz:

```env
GOOGLE_API_KEY=sua_chave_aqui
```

### Execução

```bash
# Menu interativo (recomendado)
python main.py

# Direto para batch
python main.py --batch

# Ver histórico
python main.py --historico

# Buscar no histórico
python main.py --buscar "jornal nacional"
```

### Exemplos de entrada aceitos

```
C:\Videos\reportagem.mp4
globopop.mxf
https://www.youtube.com/watch?v=XXXXXXXXXXX
```

---

## 📦 Saídas geradas

Para cada vídeo processado:

| Arquivo | Conteúdo |
|---|---|
| `Nome do Vídeo.txt` | Transcrição da audiodescrição |
| `Nome do Vídeo.mp3` | Narração com voz neural pt-BR |
| `Nome do Vídeo.srt` | Legenda com timecodes (padrão SRT) |
| `Nome do Vídeo_player.html` | Player standalone com legenda sincronizada |
| `historico.json` | Registro de todos os vídeos processados |

---

## 📋 Norma de referência

**ABNT NBR 15290:2005** — norma brasileira de acessibilidade em comunicação audiovisual.  
Princípios aplicados: tempo presente, objetividade, foco no tripé cenário → personagem → ação, sem introduções desnecessárias.

---

## 🔧 Dependências

```
google-genai      # API do Gemini (Google)
edge-tts          # Síntese de voz neural (Microsoft)
opencv-python     # Processamento de vídeo
Pillow            # Manipulação de imagens
python-dotenv     # Carregamento do .env
yt-dlp            # Download de vídeos do YouTube
pygame            # Reprodução de áudio
```

---

## 👥 Grupo Grow up

| Nome | Contribuição |
|---|---|
| **Anne Vitória** | Arquitetura do sistema, integração Gemini, SRT, player HTML, histórico, batch |
| **William Santos** | Código base (OpenCV + Gemini + gTTS), estrutura modular inicial |
| **Vitória** | Organização do conteúdo e apresentação |

---

## 📄 Licença

Projeto acadêmico desenvolvido para fins educacionais e de pesquisa aplicada.  
**Residência Tecnológica Porto Digital × TV Globo · UNIT 2026.1**
