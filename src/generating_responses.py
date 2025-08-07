# Arquivo: src/generating_responses.py (Versão Final Corrigida)

import chromadb
import google.generativeai as genai

def buscar_contexto_no_db(pergunta: str, collection: chromadb.Collection, n_results: int = 3) -> tuple[str, list]:
    """
    Recebe uma pergunta e uma coleção do ChromaDB, busca as SEÇÕES mais
    relevantes e retorna o contexto formatado e as fontes.
    """
    # Como os chunks de seção são maiores, buscar 3 resultados já é suficiente.
    resultados = collection.query(
        query_texts=[pergunta],
        n_results=n_results
    )
    
    if not resultados.get('documents') or not resultados['documents'][0]:
        return "", []

    contexto_formatado = ""
    fontes = []
    
    # Itera sobre os resultados para montar o contexto e a lista de fontes
    for i, doc in enumerate(resultados['documents'][0]):
        metadado = resultados['metadatas'][0][i]
        
        # ===================================================================
        # ALTERAÇÃO PRINCIPAL AQUI: Lendo os novos metadados
        # ===================================================================
        titulo_secao = metadado.get('titulo_secao', 'Seção Desconhecida').strip()
        paginas = metadado.get('paginas', 'N/A')
        
        # Cria uma string de fonte muito mais informativa para o usuário
        fonte_str = f"Seção '{titulo_secao}' (Págs: {paginas})"
        # ===================================================================
        
        contexto_formatado += f"--- Trecho da {fonte_str} ---\n"
        contexto_formatado += doc
        contexto_formatado += "\n\n"
        fontes.append(fonte_str)
        
    return contexto_formatado, fontes

def gerar_resposta_com_llm(pergunta: str, contexto: str, model: genai.GenerativeModel) -> str:
    """
    Gera a resposta final com base no contexto das seções recuperadas.
    """
    prompt_final = f"""
    Você é um assistente especialista na bomba de infusão E-Link. 
    Sua tarefa é responder à pergunta do usuário de forma clara, precisa e segura, baseando-se exclusivamente no contexto fornecido abaixo.
    O contexto foi extraído de SEÇÕES COMPLETAS do manual do equipamento, garantindo a integridade das informações.

    **CONTEXTO EXTRAÍDO DO MANUAL:**
    {contexto}

    **PERGUNTA DO USUÁRIO:**
    {pergunta}

    **SUA RESPOSTA:**
    """
    
    try:
        resposta_final = model.generate_content(prompt_final)
        return resposta_final.text
    except Exception as e:
        return f"Ocorreu um erro ao gerar a resposta: {e}"

# Esta função orquestradora continua igual na sua estrutura
def responder_pergunta(pergunta: str, collection: chromadb.Collection, model: genai.GenerativeModel) -> str:
    """
    Orquestra o processo de RAG: busca e geração.
    """
    print(f">>> Processando pergunta: {pergunta}")
    
    # Recuperação (Retrieval)
    contexto, fontes = buscar_contexto_no_db(pergunta, collection)
    
    if not contexto:
        return "Desculpe, não consegui encontrar informações sobre isso no manual. Por favor, tente reformular sua pergunta."

    # Geração (Generation)
    resposta = gerar_resposta_com_llm(pergunta, contexto, model)
    
    # Formata a resposta final com as fontes
    fontes_unicas = sorted(list(set(fontes)))
    resposta_formatada = f"{resposta}\n\n---\n**Fontes Consultadas:**\n- " + "\n- ".join(fontes_unicas)
    
    return resposta_formatada