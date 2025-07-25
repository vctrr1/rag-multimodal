import chromadb
from sentence_transformers import SentenceTransformer
import time

from src.config import DB_DIR
from src.data_processing import gerar_resumo_com_gemini

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
client = chromadb.PersistentClient(path=DB_DIR)

collection = client.get_or_create_collection(name="manuals")

def popular_banco_vetorial(textos, tabelas, imagens, nome_manual):
    """Gera embeddings para todos os elementos e os armazena no ChromaDB."""
    print("\nIniciando a população do banco de dados vetorial...")
    
    documentos = []
    metadados = []
    ids = []
    
    # Processa textos
    for i, texto_el in enumerate(textos):
        documentos.append(texto_el.text)
        metadados.append({'tipo': 'texto', 'pagina': texto_el.metadata.page_number, 'fonte': nome_manual})
        ids.append(f'texto_{i}')
    
    # Processa tabelas
    print(f"Processando {len(tabelas)} tabelas...")
    for i, tabela_el in enumerate(tabelas):
        resumo = gerar_resumo_com_gemini(tabela_el.metadata.text_as_html, "tabela")
        documentos.append(resumo)
        metadados.append({'tipo': 'tabela', 'pagina': tabela_el.metadata.page_number, 'fonte': nome_manual, 'conteudo_original': tabela_el.metadata.text_as_html})
        ids.append(f'tabela_{i}')
        print(f"  - Tabela {i+1} resumida. Aguardando...")
        time.sleep(2) # 2. Adicione uma pausa de 1 segundo

    # Processa imagens
    print(f"Processando {len(imagens)} imagens...")
    for i, imagem_el in enumerate(imagens):
        resumo = gerar_resumo_com_gemini(imagem_el.metadata.image_path, "imagem")
        documentos.append(resumo)
        metadados.append({'tipo': 'imagem', 'pagina': imagem_el.metadata.page_number, 'fonte': nome_manual, 'conteudo_original': imagem_el.metadata.image_path})
        ids.append(f'imagem_{i}')
        print(f"  - Imagem {i+1} resumida. Aguardando...")
        time.sleep(2)

    # Gera os embeddings para todos os documentos de uma vez
    print("Gerando embeddings para todos os documentos...")
    embeddings = embedding_model.encode(documentos).tolist()

    # Adiciona tudo à coleção do ChromaDB
    print("Adicionando dados ao ChromaDB...")
    collection.add(embeddings=embeddings, documents=documentos, metadatas=metadados, ids=ids)
    print(f"Banco de dados vetorial populado com sucesso! Total de vetores: {collection.count()}")