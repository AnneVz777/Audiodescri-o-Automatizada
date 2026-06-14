"""
historico.py
Gerencia o histórico de vídeos processados em JSON local.
Permite salvar, listar e buscar registros por nome ou data.
"""

import json
import os
from datetime import datetime
from config import OUTPUT_DIR

HISTORICO_PATH = os.path.join(OUTPUT_DIR, "historico.json")


def _carregar() -> list[dict]:
    if not os.path.exists(HISTORICO_PATH):
        return []
    with open(HISTORICO_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []


def _salvar(dados: list[dict]):
    with open(HISTORICO_PATH, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def registrar(nome: str, fonte: str, duracao: float, palavras: int, arquivos: dict):
    """
    Salva um novo registro no histórico.

    Args:
        nome:     Título gerado pelo Gemini
        fonte:    Caminho ou URL original do vídeo
        duracao:  Duração em segundos
        palavras: Total de palavras na audiodescrição
        arquivos: Dict com paths dos arquivos gerados {txt, mp3, srt, html}
    """
    dados = _carregar()
    registro = {
        "id":         len(dados) + 1,
        "nome":       nome,
        "fonte":      fonte,
        "duracao_s":  round(duracao, 1),
        "palavras":   palavras,
        "data":       datetime.now().strftime("%d/%m/%Y %H:%M"),
        "arquivos":   arquivos,
    }
    dados.append(registro)
    _salvar(dados)
    return registro


def buscar(termo: str) -> list[dict]:
    """
    Busca registros pelo nome do vídeo (case-insensitive).
    Retorna lista de registros que contêm o termo.
    """
    dados = _carregar()
    termo = termo.lower().strip()
    return [r for r in dados if termo in r["nome"].lower()]


def listar_todos() -> list[dict]:
    return _carregar()


def exibir_historico(registros: list[dict] | None = None):
    """Imprime o histórico formatado no terminal."""
    dados = registros if registros is not None else _carregar()

    if not dados:
        print("  Nenhum vídeo processado ainda.")
        return

    print(f"\n  {'ID':<4} {'DATA':<17} {'DURAÇÃO':<9} {'PALAVRAS':<10} NOME")
    print("  " + "─" * 65)
    for r in dados:
        dur = f"{r['duracao_s']}s"
        print(f"  {r['id']:<4} {r['data']:<17} {dur:<9} {r['palavras']:<10} {r['nome']}")
    print()
