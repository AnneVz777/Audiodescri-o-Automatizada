import os
import sys

# ── API Key ─────────────────────────────
GOOGLE_API_KEY = "AQ.Ab8RN6KBdusqvBUOgRWY6ledfV0rusrdPJ-AT1x0D8XIRL_Jvw"

VOICE       = "pt-BR-FranciscaNeural"
VOICE_RATE  = "+0%"   # velocidade: -20% mais lento / +20% mais rápido
VOICE_PITCH = "+0Hz"  # tom: -10Hz mais grave / +10Hz mais agudo

# ── Configurações gerais ─────────────────────────────────────
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
