# // VERSÃO 2: Modular, independente e reutilizável //

import chromadb
import google.generativeai as genai

def buscar_contexto_no_db(pergunta: str, collection: chromadb.Collection, n_results: int = 5) -> tuple[str, list]:
    """
    Recebe uma pergunta e uma coleção do ChromaDB, busca os documentos mais
    relevantes e retorna o contexto formatado e as fontes.
    """
    resultados = collection.query(
        query_texts=[pergunta],
        n_results=n_results
    )
    
    contexto_formatado = ""
    fontes = []
    
    # Itera sobre os resultados para montar o contexto e a lista de fontes
    for i, doc in enumerate(resultados['documents'][0]):
        metadado = resultados['metadatas'][0][i]
        fonte_str = f"Tipo: {metadado.get('tipo', 'N/A')}, Página: {metadado.get('pagina', 'N/A')}"
        
        contexto_formatado += f"--- Contexto {i+1} ({fonte_str}) ---\n"
        contexto_formatado += doc
        contexto_formatado += "\n\n"
        fontes.append(fonte_str)
        
    return contexto_formatado, fontes

def gerar_resposta_com_llm(pergunta: str, contexto: str, model: genai.GenerativeModel) -> str:

    prompt_final = f"""
    Você é um assistente especialista em dispositivos médicos, mais especificamente em bombas de infusão. 
    Sua tarefa é responder à pergunta do usuário de forma clara e concisa, baseando-se exclusivamente no contexto fornecido abaixo.
    O contexto foi extraído diretamente do manual do equipamento. Ao final da sua resposta, sempre liste as fontes que você utilizou.

    **CONTEXTO EXTRAÍDO DO MANUAL:**
    {contexto}

    **PERGUNTA DO USUÁRIO:**
    {pergunta}

    **SUA RESPOSTA:**
    """
    
    resposta_final = model.generate_content(prompt_final)
    return resposta_final.text

def responder_pergunta(pergunta: str, collection: chromadb.Collection, model: genai.GenerativeModel) -> str:

    print(f">>> Processando pergunta: {pergunta}")
    
    #Recuperação (Retrieval)
    contexto, fontes = buscar_contexto_no_db(pergunta, collection)
    
    #Geração (Generation)
    resposta = gerar_resposta_com_llm(pergunta, contexto, model)
    
    # esposta final com as fontes
    resposta_formatada = f"{resposta}\n\n--- \n**Fontes Consultadas:**\n- " + "\n- ".join(fontes)
    
    print("--- Resposta Gerada ---")
    print(resposta_formatada)
    return resposta_formatada