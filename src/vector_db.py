import chromadb
from sentence_transformers import SentenceTransformer
import time

from src.config import DB_DIR

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path=DB_DIR)

collection = client.get_or_create_collection(name="manuals")

def popular_banco_com_secoes(secoes, nome_manual):

    if not secoes:
        print("Nenhuma seção para adicionar ao banco de dados.")
        return

    print(f"\nIniciando a população do banco de dados com {len(secoes)} seções...")
    
    documentos = [secao["conteudo_combinado"] for secao in secoes]
    metadados = [
        {
            'tipo': 'secao_semantica',
            'titulo_secao': secao["titulo_secao"],
            'paginas': ', '.join(map(str, sorted(secao["paginas"]))),
            'fonte': nome_manual
        } for secao in secoes
    ]
    ids = [f'secao_{i}' for i in range(len(secoes))]

    print("Gerando embeddings para todas as seções...")
    embeddings = embedding_model.encode(documentos, show_progress_bar=True).tolist()

    print("Adicionando dados ao ChromaDB...")
    collection.add(embeddings=embeddings, documents=documentos, metadatas=metadados, ids=ids)
    
    print(f"Banco de dados vetorial populado com sucesso! Total de vetores: {collection.count()}")