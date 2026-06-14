"""
srt_generator.py
Gera arquivo de legenda no formato SRT (SubRip) a partir
da audiodescrição gerada pelo Gemini.

O SRT é o formato padrão da indústria para legendas,
aceito por plataformas como YouTube, Vimeo, Netflix e
softwares de edição como Premiere e DaVinci Resolve.

Formato SRT:
    1
    00:00:00,000 --> 00:00:03,500
    Texto da legenda aqui.

    2
    00:00:03,500 --> 00:00:07,000
    Segunda linha de legenda.
"""

import os
import re
from config import OUTPUT_DIR


_WPS = 150 / 60  # 150 wpm → 2.5 palavras por segundo


def _segundos_para_srt(segundos: float) -> str:
    """Converte segundos em timestamp SRT: HH:MM:SS,mmm"""
    h  = int(segundos // 3600)
    m  = int((segundos % 3600) // 60)
    s  = int(segundos % 60)
    ms = int((segundos - int(segundos)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _dividir_em_frases(descricao: str) -> list[str]:
    """
    Divide a descrição em frases usando pontuação como separador.
    Remove linhas vazias e frases muito curtas (< 3 palavras).
    """
    frases = re.split(r'(?<=[.!?])\s+', descricao.strip())
    return [f.strip() for f in frases if len(f.split()) >= 3]


def gerar_srt(descricao: str, nome_arquivo: str, duracao_video: float) -> str:
    """
    Gera um arquivo .srt com timecodes estimados pela velocidade de leitura.

    A duração total da narração é distribuída proporcionalmente
    entre as frases, respeitando o tempo total do vídeo.

    Args:
        descricao:     Texto completo da audiodescrição
        nome_arquivo:  Nome base do arquivo (sem extensão)
        duracao_video: Duração real do vídeo em segundos

    Returns:
        Caminho absoluto do arquivo .srt gerado
    """
    frases = _dividir_em_frases(descricao)
    if not frases:
        frases = [descricao.strip()]

    srt_path = os.path.join(OUTPUT_DIR, f"{nome_arquivo}.srt")

    
    total_palavras = sum(len(f.split()) for f in frases)
    duracao_util   = min(duracao_video * 0.9, duracao_video)

    blocos = []
    tempo_atual = 0.0

    for i, frase in enumerate(frases, start=1):
        proporcao     = len(frase.split()) / max(total_palavras, 1)
        duracao_frase = proporcao * duracao_util
        duracao_frase = max(duracao_frase, 1.5) 

        inicio = tempo_atual
        fim    = inicio + duracao_frase

        # Garante que não ultrapasse a duração do vídeo
        if fim > duracao_video:
            fim = duracao_video

        blocos.append(
            f"{i}\n"
            f"{_segundos_para_srt(inicio)} --> {_segundos_para_srt(fim)}\n"
            f"{frase}\n"
        )

        tempo_atual = fim
        if tempo_atual >= duracao_video:
            break

    with open(srt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(blocos))

    return srt_path
