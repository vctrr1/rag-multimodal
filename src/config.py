import os 
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not GOOGLE_API_KEY:
    raise ValueError("A chave da API do Google não foi encontrada. Verifique se o arquivo .env existe e contém a variável GOOGLE_API_KEY.")

#Paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)).parent

# Caminhos para os dados
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

# Caminhos para os arquivos de saída
OUTPUTS_DIR = os.path.join(PROJECT_ROOT, "output")
IMAGE_DIR = os.path.join(OUTPUTS_DIR, "extracted_images")
DB_DIR = os.path.join(OUTPUTS_DIR, "db")

print("config carregada com sucesso.")