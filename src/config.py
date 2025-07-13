import os
from pathlib import Path
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

# Verifica a chave da API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("A chave da API do Google não foi encontrada. Verifique se o arquivo .env existe e contém a variável GOOGLE_API_KEY.")

# Caminhos do projeto
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUTS_DIR = PROJECT_ROOT / "output"
IMAGE_DIR = OUTPUTS_DIR / "extracted_images"
DB_DIR = OUTPUTS_DIR / "db"

print("Config carregada com sucesso.")
