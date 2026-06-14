"""
main.py
Ponto de entrada e orquestrador do sistema de audiodescrição.

Modos de uso:
    - Vídeo único:  python main.py
    - Batch:        python main.py --batch
    - Histórico:    python main.py --historico
    - Busca:        python main.py --buscar "termo"
"""

import os
import sys
import asyncio
import subprocess
import base64
import webbrowser
from config import VOICE, VOICE_RATE, VOICE_PITCH, OUTPUT_DIR
from gemini_client import enviar_e_descrever
from srt_generator import gerar_srt
from historico import registrar, listar_todos, buscar, exibir_historico
import edge_tts

BANNER = """
╔══════════════════════════════════════════════════════╗
║       AUDIODESCRIÇÃO AUTOMATIZADA — GROW UP          ║
║       Porto Digital × Globo · UNIT 2026.1            ║
╚══════════════════════════════════════════════════════╝"""


# ── Preparação do vídeo ──────────────────────────────────────

def converter_mxf(caminho_mxf: str) -> str:
    saida = os.path.abspath(caminho_mxf.replace(".mxf", "_convertido.mp4"))
    print("  Convertendo MXF para MP4...")
    result = subprocess.run(
        ["ffmpeg", "-y", "-i", os.path.abspath(caminho_mxf),
            "-c:v", "libx264", "-preset", "ultrafast", "-c:a", "aac", saida],
        capture_output=True,
        text=False,
    )
    if not os.path.exists(saida):
        print("  ERRO na conversão FFmpeg:")
        print(result.stderr.decode("utf-8", errors="replace")[-300:])
        sys.exit(1)
    print(f"  Convertido: {saida}")
    return saida


def baixar_youtube(url: str) -> str:
    saida = os.path.abspath("youtube_video.mp4")
    if os.path.exists(saida):
        os.remove(saida)
    print("  Baixando vídeo do YouTube...")
    result = subprocess.run(
        ["yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
            "--merge-output-format", "mp4", "-o", saida, url],
        capture_output=True,
        text=False,
    )
    if not os.path.exists(saida):
        print("  ERRO ao baixar YouTube:")
        print(result.stderr.decode("utf-8", errors="replace")[-300:])
        sys.exit(1)
    print(f"  Download concluído: {saida}")
    return saida


def preparar_video(fonte: str) -> str:
    fonte = fonte.strip()
    if "youtube.com" in fonte or "youtu.be" in fonte:
        print("  Tipo: YouTube")
        return baixar_youtube(fonte)
    caminho = os.path.abspath(fonte)
    if not os.path.exists(caminho):
        print(f"  ERRO: Arquivo não encontrado: {caminho}")
        print(f"  Pasta atual: {os.getcwd()}")
        sys.exit(1)
    if fonte.lower().endswith(".mxf"):
        print("  Tipo: MXF local")
        return converter_mxf(caminho)
    print("  Tipo: MP4/vídeo local")
    return caminho


# ── Geração de áudio ─────────────────────────────────────────

async def _gerar_audio_async(descricao: str, caminho_mp3: str):
    communicate = edge_tts.Communicate(
        text=descricao,
        voice=VOICE,
        rate=VOICE_RATE,
        pitch=VOICE_PITCH,
    )
    await communicate.save(caminho_mp3)


def gerar_audio(descricao: str, nome_arquivo: str) -> str:
    mp3 = os.path.join(OUTPUT_DIR, f"{nome_arquivo}.mp3")
    asyncio.run(_gerar_audio_async(descricao, mp3))
    return mp3


# ── Player HTML ──────────────────────────────────────────────

def abrir_player(caminho_video: str, descricao: str, caminho_audio: str,
                    nome: str, srt_path: str):
    print("  Gerando player com legenda...")

    with open(caminho_video, "rb") as f:
        video_b64 = base64.b64encode(f.read()).decode()
    with open(caminho_audio, "rb") as f:
        audio_b64 = base64.b64encode(f.read()).decode()

    # Lê o SRT e converte para JSON para uso no JS
    srt_entries = []
    with open(srt_path, "r", encoding="utf-8") as f:
        blocos_srt = f.read().strip().split("\n\n")
    for bloco in blocos_srt:
        linhas = bloco.strip().split("\n")
        if len(linhas) >= 3:
            tempos = linhas[1].split(" --> ")
            def srt_para_s(t):
                t = t.replace(",", ".")
                h, m, s = t.split(":")
                return float(h)*3600 + float(m)*60 + float(s)
            texto = " ".join(linhas[2:])
            srt_entries.append({
                "inicio": srt_para_s(tempos[0].strip()),
                "fim":    srt_para_s(tempos[1].strip()),
                "texto":  texto.replace('"', '\\"'),
            })

    srt_json = "[" + ",".join(
        [f'{{"s":{e["inicio"]},"e":{e["fim"]},"t":"{e["texto"]}"}}' for e in srt_entries]
    ) + "]"

    frases = [f.strip() for f in descricao.replace("\n", " ").split(".") if f.strip()]
    frases_html = "".join([
        f'<div class="frase"><span class="num">{i+1}</span><span>{f}.</span></div>'
        for i, f in enumerate(frases)
    ])

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audiodescrição — {nome}</title>
    <style>
        *, *::before, *::after {{ margin: 0; padding: 0; box-sizing: border-box; }}

        :root {{
            --bg:       #080c14;
            --surface:  #111827;
            --border:   #1e3a5f;
            --accent:   #3b82f6;
            --cyan:     #06b6d4;
            --red:      #e50914;
            --white:    #f1f5f9;
            --muted:    #64748b;
            --text:     #cbd5e1;
        }}

        body {{
            background: var(--bg);
            font-family: 'Segoe UI', system-ui, sans-serif;
            color: var(--text);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 28px 16px 48px;
        }}

        /* ── Header ── */
        header {{
            width: 100%;
            max-width: 880px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 20px;
        }}
        .header-left {{ display: flex; align-items: center; gap: 12px; }}
        .badge-ad {{
            background: var(--red);
            color: #fff;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 2px;
            padding: 4px 10px;
            border-radius: 4px;
            text-transform: uppercase;
        }}
        header h1 {{
            font-size: 17px;
            font-weight: 500;
            color: var(--white);
            max-width: 520px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .badge-nbr {{
            font-size: 10px;
            color: var(--muted);
            border: 1px solid var(--border);
            padding: 3px 8px;
            border-radius: 4px;
            letter-spacing: 0.5px;
        }}

        /* ── Player ── */
        .player-wrap {{
            position: relative;
            width: 100%;
            max-width: 880px;
            background: #000;
            border-radius: 14px;
            overflow: hidden;
            box-shadow: 0 20px 60px rgba(0,0,0,0.85);
            border: 1px solid var(--border);
        }}
        video {{ width: 100%; display: block; max-height: 495px; object-fit: contain; }}

        /* Legenda sincronizada */
        .legenda {{
            position: absolute;
            bottom: 52px;
            left: 0; right: 0;
            text-align: center;
            padding: 0 20px;
            pointer-events: none;
            min-height: 36px;
        }}
        .legenda span {{
            display: inline-block;
            background: rgba(0,0,0,0.85);
            color: #fff;
            font-size: 16px;
            font-weight: 400;
            line-height: 1.6;
            padding: 5px 16px;
            border-radius: 6px;
            max-width: 740px;
            backdrop-filter: blur(4px);
            border: 1px solid rgba(255,255,255,0.08);
            transition: opacity 0.2s;
        }}

        /* ── Controles extras ── */
        .controls-extra {{
            width: 100%;
            max-width: 880px;
            display: flex;
            gap: 10px;
            margin-top: 14px;
        }}
        .btn {{
            flex: 1;
            background: var(--surface);
            border: 1px solid var(--border);
            color: var(--text);
            font-size: 12px;
            padding: 10px;
            border-radius: 8px;
            cursor: pointer;
            text-align: center;
            transition: background 0.2s, border-color 0.2s;
        }}
        .btn:hover {{ background: #1e293b; border-color: var(--accent); color: var(--white); }}
        .btn-active {{ border-color: var(--accent); color: var(--accent); }}

        /* ── Narração ── */
        .audio-wrap {{
            width: 100%;
            max-width: 880px;
            margin-top: 14px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px 20px;
        }}
        .section-label {{
            font-size: 10px;
            letter-spacing: 1.5px;
            text-transform: uppercase;
            color: var(--muted);
            margin-bottom: 10px;
        }}
        audio {{ width: 100%; }}

        /* ── Transcrição ── */
        .transcricao {{
            width: 100%;
            max-width: 880px;
            margin-top: 14px;
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 20px 24px;
        }}
        .frase {{
            display: flex;
            gap: 12px;
            padding: 8px 0;
            border-bottom: 1px solid #1a2535;
            font-size: 13.5px;
            line-height: 1.75;
            color: var(--text);
            align-items: flex-start;
        }}
        .frase:last-child {{ border-bottom: none; }}
        .num {{
            min-width: 24px;
            color: var(--red);
            font-weight: 700;
            font-size: 12px;
            padding-top: 3px;
            font-variant-numeric: tabular-nums;
        }}

        /* ── Footer ── */
        footer {{
            margin-top: 32px;
            font-size: 11px;
            color: var(--muted);
            letter-spacing: 0.3px;
            text-align: center;
        }}
        footer a {{ color: var(--accent); text-decoration: none; }}

        /* ── Legenda visível/oculta ── */
        .legenda.oculta span {{ opacity: 0; }}
    </style>
</head>
<body>

<header>
    <div class="header-left">
        <span class="badge-ad">AD</span>
        <h1>{nome}</h1>
    </div>
    <span class="badge-nbr">NBR 15290</span>
</header>

<div class="player-wrap">
    <video id="vid" controls>
        <source src="data:video/mp4;base64,{video_b64}" type="video/mp4">
    </video>
    <div class="legenda" id="legenda">
        <span id="leg">▶ Pressione play para iniciar</span>
    </div>
</div>

<div class="controls-extra">
    <button class="btn" id="btn-leg" onclick="toggleLegenda()">
        💬 Legenda: <strong>Ativa</strong>
    </button>
    <button class="btn" onclick="reiniciar()">
        ↺ Reiniciar
    </button>
    <button class="btn" onclick="sincronizarAudio()">
        🔄 Sincronizar áudio
    </button>
</div>

<div class="audio-wrap">
    <div class="section-label">🎙 Narração — Audiodescrição</div>
    <audio id="aud" controls>
        <source src="data:audio/mpeg;base64,{audio_b64}" type="audio/mpeg">
    </audio>
</div>

<div class="transcricao">
    <div class="section-label">📄 Transcrição completa</div>
    {frases_html}
</div>

<footer>
    Gerado com Gemini 2.5 Flash + Edge TTS (pt-BR-FranciscaNeural) ·
    Legenda exportada em <strong>.SRT</strong> ·
    <a href="https://www.abntcatalogo.com.br/" target="_blank">ABNT NBR 15290</a> ·
    Porto Digital × Globo · 2026.1
</footer>

<script>
const entradas = {srt_json};
const vid = document.getElementById('vid');
const aud = document.getElementById('aud');
const leg = document.getElementById('leg');
const legWrap = document.getElementById('legenda');
let legendaAtiva = true;

// Sincroniza legenda com o SRT
vid.addEventListener('timeupdate', () => {{
    const t = vid.currentTime;
    const entrada = entradas.find(e => t >= e.s && t <= e.e);
    leg.textContent = entrada ? entrada.t : '';
}});

vid.addEventListener('play', () => {{
    aud.currentTime = vid.currentTime;
    aud.play().catch(() => {{}});
}});

vid.addEventListener('pause', () => {{ aud.pause(); }});

vid.addEventListener('seeked', () => {{
    aud.currentTime = vid.currentTime;
    if (!vid.paused) aud.play().catch(() => {{}});
}});

vid.addEventListener('ended', () => {{
    leg.textContent = '■ Fim do vídeo';
    aud.pause();
}});

function toggleLegenda() {{
    legendaAtiva = !legendaAtiva;
    legWrap.classList.toggle('oculta', !legendaAtiva);
    document.getElementById('btn-leg').innerHTML =
        '💬 Legenda: <strong>' + (legendaAtiva ? 'Ativa' : 'Oculta') + '</strong>';
}}

function reiniciar() {{
    vid.currentTime = 0;
    aud.currentTime = 0;
    vid.play();
}}

function sincronizarAudio() {{
    aud.currentTime = vid.currentTime;
    if (!vid.paused) aud.play().catch(() => {{}});
}}
</script>
</body>
</html>"""

    html_path = os.path.join(OUTPUT_DIR, f"{nome}_player.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    webbrowser.open(f"file:///{html_path}")
    print(f"  Player aberto: {html_path}")
    return html_path


# ── Processamento de um vídeo ────────────────────────────────

def processar(fonte: str) -> bool:
    """Processa um único vídeo. Retorna True se bem-sucedido."""
    print(f"\n{'═'*55}")
    print(f"  Fonte: {fonte}")
    print(f"{'═'*55}")

    caminho              = preparar_video(fonte)
    descricao, nome, dur = enviar_e_descrever(caminho)

    print(f"\n{'─'*55}")
    print(descricao)
    print(f"{'─'*55}\n")

    nome_arquivo = "".join(c for c in nome if c.isalnum() or c in " _-").strip()

    # 1. Salva transcrição em texto
    txt_path = os.path.join(OUTPUT_DIR, f"{nome_arquivo}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(descricao)
    print(f"  ✓ Texto salvo:   {nome_arquivo}.txt")

    # 2. Gera legenda SRT
    srt_path = gerar_srt(descricao, nome_arquivo, dur)
    print(f"  ✓ Legenda salva: {nome_arquivo}.srt")

    # 3. Gera áudio MP3
    print("  Gerando áudio com Edge TTS...")
    mp3_path = gerar_audio(descricao, nome_arquivo)
    print(f"  ✓ Áudio salvo:   {nome_arquivo}.mp3")

    # 4. Gera player HTML
    html_path = abrir_player(caminho, descricao, mp3_path, nome, srt_path)

    # 5. Registra no histórico
    registrar(
        nome=nome,
        fonte=fonte,
        duracao=dur,
        palavras=len(descricao.split()),
        arquivos={"txt": txt_path, "mp3": mp3_path, "srt": srt_path, "html": html_path},
    )

    print(f"\n  ✓ Concluído: {nome}")
    print(f"    Duração: {dur:.1f}s  |  Palavras: {len(descricao.split())}")
    return True


# ── Modo batch ───────────────────────────────────────────────

def modo_batch():
    print("\n  MODO BATCH — Cole os caminhos/URLs, um por linha.")
    print("  Deixe uma linha em branco para iniciar o processamento.\n")

    fontes = []
    while True:
        entrada = input(f"  [{len(fontes)+1}] Vídeo: ").strip()
        if not entrada:
            if fontes:
                break
            print("  Nenhum vídeo informado. Encerrando.")
            return
        fontes.append(entrada)

    print(f"\n  {len(fontes)} vídeo(s) na fila. Iniciando processamento...\n")
    ok = erro = 0
    for i, fonte in enumerate(fontes, 1):
        print(f"\n  ━━━ Vídeo {i}/{len(fontes)} ━━━")
        try:
            processar(fonte)
            ok += 1
        except Exception as e:
            print(f"  ✗ Erro ao processar '{fonte}': {e}")
            erro += 1

    print(f"\n{'═'*55}")
    print(f"  Batch concluído: {ok} ✓  |  {erro} ✗")
    print(f"{'═'*55}")


# ── Menu principal ───────────────────────────────────────────

def menu():
    print(BANNER)
    print("""
  [1] Processar um vídeo
  [2] Processar em batch (vários vídeos)
  [3] Ver histórico
  [4] Buscar no histórico
  [0] Sair
""")
    return input("  Escolha: ").strip()


def main():
    # Suporte a argumentos diretos na linha de comando
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--batch":
            print(BANNER)
            modo_batch()
            return
        if arg == "--historico":
            print(BANNER)
            exibir_historico()
            return
        if arg == "--buscar" and len(sys.argv) > 2:
            print(BANNER)
            termo = " ".join(sys.argv[2:])
            resultados = buscar(termo)
            print(f"\n  Resultados para '{termo}':")
            exibir_historico(resultados)
            return

    while True:
        opcao = menu()

        if opcao == "1":
            print("\n  Cole o caminho do arquivo (.mp4 / .mxf) ou link do YouTube:")
            fonte = input("  Vídeo: ").strip()
            if fonte:
                processar(fonte)

        elif opcao == "2":
            modo_batch()

        elif opcao == "3":
            exibir_historico()

        elif opcao == "4":
            termo = input("\n  Buscar por nome: ").strip()
            if termo:
                resultados = buscar(termo)
                print(f"\n  {len(resultados)} resultado(s) para '{termo}':")
                exibir_historico(resultados)

        elif opcao == "0":
            print("\n  Encerrando. Até mais!\n")
            break

        else:
            print("  Opção inválida.")


if __name__ == "__main__":
    main()
