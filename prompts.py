
_WPM = 150


def build_prompt(duracao_segundos: float) -> str:
    """
    Gera o prompt de audiodescrição calibrado para a duração real do vídeo.
    Regra: narração deve caber em ~85% do tempo do vídeo (margem de respiro).
    """
    duracao_util = duracao_segundos * 0.85
    max_palavras  = int((duracao_util / 60) * _WPM)
    max_frases    = max(1, round(max_palavras / 12))

    return f"""Você é um locutor profissional de audiodescrição para pessoas com deficiência visual, seguindo as normas ABNT NBR 15290.

O vídeo tem {int(duracao_segundos)} segundos. Sua narração será lida em voz alta e deve caber dentro desse tempo.

LIMITES OBRIGATÓRIOS:
- Máximo de {max_palavras} palavras no total
- Máximo de {max_frases} frases
- Cada frase: curta, direta, sem subordinadas longas

Descreva em português do Brasil:
1. Cenário e ambiente
2. Personagens ou elementos visuais principais
3. Ações e eventos na ordem em que ocorrem
4. Textos na tela, grafismos ou transições relevantes

Sem introduções ("Neste vídeo", "Vemos que"). Sem repetições. Tempo presente. Só o essencial."""
