# aqui onde vai rodar o chatbot

import chromadb
import google.generativeai as genai

from src.generating_responses import responder_pergunta
from src.config import GOOGLE_API_KEY, DB_DIR

def app():

    print("Iniciando o chatbot...")

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
    except Exception as e:
        return

    try:
        client = chromadb.PersistentClient(path=DB_DIR)
        collection = client.get_collection("manuals")
    except Exception as e:
        print(f"❌ Erro ao conectar ao ChromaDB: {e}")
        return

    print("\nDigite sua pergunta ou 'sair' para encerrar.\n")

    while True:
        pergunta_usuario = input("Você: ")
        if pergunta_usuario.lower() in ['sair']:
            break
        if not pergunta_usuario:
            continue

        print("Assistente está pensando...")
        resposta_assistente = responder_pergunta(pergunta_usuario, collection, model)
        print(f"\nAssistente:\n{resposta_assistente}\n")

if __name__ == "__main__":
    app()