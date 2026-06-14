"""
gemini_client.py
Inicializa o cliente Google Gemini e expõe a função
principal de análise de vídeo: enviar_e_descrever().

Responsabilidades:
    - Upload do vídeo para a API
    - Geração do título automático
    - Geração da audiodescrição calibrada pela duração
    - Fallback entre modelos e retry em erros de servidor
"""

import sys
import time
import subprocess
from google import genai
from config import GOOGLE_API_KEY
from prompts import build_prompt

# ── Inicializa cliente ───────────────────────────────────────
client = genai.Client(api_key=str(GOOGLE_API_KEY))
print(f"  API Key carregada: {GOOGLE_API_KEY[:8]}...")

MODELOS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
]

PROMPT_NOME = """Assista ao vídeo e responda com um título curto em português do Brasil.

Regras:
- Máximo 5 palavras
- Sem pontuação, sem aspas, sem artigos no início
- Descreva o conteúdo principal (ex: "Dança no Palco", "Entrevista Jornal Nacional")
- Responda APENAS o título, nada mais"""


def obter_duracao(caminho_video: str) -> float:
    """Retorna a duração do vídeo em segundos via ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                caminho_video,
            ],
            capture_output=True,
            text=True,
        )
        duracao = float(result.stdout.strip())
        print(f"  Duração detectada: {duracao:.1f}s")
        return duracao
    except Exception as e:
        print(f"  Aviso: não foi possível detectar duração ({e}). Usando 60s.")
        return 60.0


def _chamar_gemini(video_file, prompt: str) -> str:
    """
    Chama o Gemini com fallback entre modelos e retry automático.

    - Erro 503 (servidor sobrecarregado): retry 3x com espera crescente
    - Erro 429 (cota esgotada): pula imediatamente para o próximo modelo
    - Outros erros: lança a exceção original
    """
    for modelo in MODELOS:
        for tentativa in range(1, 4):
            try:
                resposta = client.models.generate_content(
                    model=modelo,
                    contents=[video_file, prompt],
                )
                return resposta.text.strip()

            except Exception as e:
                erro = str(e)

                if "503" in erro or "unavailable" in erro.lower():
                    espera = 15 * tentativa
                    print(f"  [{modelo}] Sobrecarregado (503). Aguardando {espera}s... (tentativa {tentativa}/3)")
                    time.sleep(espera)
                    continue

                if "429" in erro or "quota" in erro.lower() or "exhausted" in erro.lower():
                    print(f"  [{modelo}] Cota esgotada. Tentando próximo modelo...")
                    time.sleep(5)
                    break

                raise

    print("  ERRO: Todos os modelos falharam. Aguarde alguns minutos e tente novamente.")
    sys.exit(1)


def enviar_e_descrever(caminho_video: str) -> tuple[str, str, float]:
    """
    Faz upload do vídeo e retorna (descricao, nome, duracao).

    O nome é gerado pelo próprio Gemini com base no conteúdo visual.
    A audiodescrição é calibrada para caber no tempo real do vídeo.
    """
    duracao    = obter_duracao(caminho_video)
    prompt_ad  = build_prompt(duracao)

    print("  Enviando para o Gemini...")
    video_file = client.files.upload(file=caminho_video)

    print("  Processando", end="", flush=True)
    while video_file.state.name == "PROCESSING":
        print(".", end="", flush=True)
        time.sleep(5)
        video_file = client.files.get(name=video_file.name)
    print(" pronto!")

    print("  Identificando o vídeo...")
    nome = _chamar_gemini(video_file, PROMPT_NOME)
    print(f"  Nome gerado: {nome}")

    print("  Gerando audiodescrição...")
    descricao = _chamar_gemini(video_file, prompt_ad)

    return descricao, nome, duracao
