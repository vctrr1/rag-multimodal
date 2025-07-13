import chromadb
from sentence_transformers import SentenceTransformer
import os

from src.config import DB_DIR
from src.data_processing import gerar_resumo_com_gemini

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path=DB_DIR)

