import os
import sys
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    print("ERRO: API Key nao encontrada. Verifique o arquivo .env")
    sys.exit(1)

VOICE       = "pt-BR-FranciscaNeural"
VOICE_RATE  = "+0%"
VOICE_PITCH = "+0Hz"

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
