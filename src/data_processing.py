import os
import re
import hashlib
from pypdf import PdfWriter, PdfReader
from unstructured.partition.pdf import partition_pdf
from PIL import Image
import google.generativeai as genai

from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, IMAGE_DIR, GOOGLE_API_KEY

try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"Erro ao configurar a API do Google Generative AI: {e}")

model = genai.GenerativeModel('models/gemini-1.5-pro-latest')

def limpar_pdf(nome_arquivo_original, nome_arquivo_saida, paginas_a_manter):

    caminho_original = os.path.join(RAW_DATA_DIR, nome_arquivo_original)
    caminho_saida = os.path.join(PROCESSED_DATA_DIR, nome_arquivo_saida)

    reader = PdfReader(caminho_original)
    writer = PdfWriter()

    for i in paginas_a_manter:
        if i < len(reader.pages):
            writer.add_page(reader.pages[i])

    with open(caminho_saida, "wb") as f:
        writer.write(f)
    print(f"PDF limpo salvo em: {caminho_saida}")
    return caminho_saida


def extrair_elementos_do_manual(caminho_pdf_processado, nome_projeto):

    print(f"Iniciando a extração do arquivo: {caminho_pdf_processado}")

    # Diretório para salvar as imagens extraídas
    pasta_imagens = IMAGE_DIR/nome_projeto
    pasta_imagens.mkdir(parents=True, exist_ok=True)

    elementos = partition_pdf(
        filename = caminho_pdf_processado,
        strategy = "hi_res",
        extract_images_in_pdf = True,
        infer_table_structure = True,
        languages = ["por"],
        extract_image_block_output_dir = pasta_imagens,
    )
    print(f"Extração concluída. {len(elementos)} elementos brutos encontrados.")
    return elementos

def gerar_resumo(conteudo, tipo_conteudo):
    prompt_base = {
        "imagem": """
        **Sua Tarefa:** Você é um Engenheiro de Documentação Técnica.
        **Objetivo:** Descrever a imagem de um componente da bomba de infusão E-Link de forma ultra detalhada para um banco de dados de RAG.
        **Instruções:**
        1.  **Descrição Física:** Descreva a cor, formato, material aparente, e quaisquer ícones ou símbolos presentes no componente. Ex: "Botão redondo, de plástico azul, com um ícone branco de 'play/pause' no centro".
        2.  **Texto na Imagem:** Transcreva literalmente qualquer texto visível na imagem, incluindo legendas ou indicadores.
        3.  **Contexto Funcional:** Com base na imagem e no seu conhecimento de equipamentos médicos, descreva a provável função deste componente. Ex: "Este é o botão principal de Iniciar/Parar a infusão".
        4.  **Localização:** Se possível, descreva onde este componente parece estar localizado no painel do equipamento.
        **Seja preciso e denso em informação. A qualidade da resposta do chatbot depende da qualidade desta descrição.**
        """,
        "tabela": """
        **Sua Tarefa:** Você é um Analista de Dados e Engenheiro Clínico.
        **Objetivo:** Extrair e estruturar TODAS as informações críticas da tabela em formato HTML para um banco de dados de RAG.
        **Instruções:**
        1.  **Extração Completa:** Não resuma. Liste cada parâmetro e seu valor/descrição correspondente da tabela. Ex: "Parâmetro: Vazão (Modo Gotas); Valor: 1 a 500 gotas/min".
        2.  **Preservar Unidades:** Sempre inclua as unidades de medida (mL/h, gotas/min, kg, mm, V, Hz).
        3.  **Formato Claro:** Use formatação de texto (como listas ou "Parâmetro: Valor") para tornar os dados fáceis de ler e interpretar pelo modelo de linguagem final.
        4.  **Propósito da Tabela:** Comece com uma frase que descreve o propósito geral da tabela. Ex: "Esta tabela detalha as especificações técnicas completas da bomba de infusão E-Link."
        **A precisão é crucial. Não omita nenhum dado técnico.**
        """
    }

    if tipo_conteudo == "imagem":
        prompt = prompt_base["imagem"]
        img = Image.open(conteudo)
        response = model.generate_content([prompt, img])
    elif tipo_conteudo == "tabela":
        prompt = prompt_base["tabela"]
        response = model.generate_content(f"{prompt}\n\nAqui está a tabela em HTML:\n{conteudo}")
    else:
        return ""

    return response.text

def agrupar_elementos_por_secao(elementos):

    # regex pra identificar títulos de seção
    padrao_titulo = re.compile(r'^\d+(\.\d+)*\s|\bApêndice\s[A-Z]\b')
    
    secoes_agrupadas = []
    chunk_atual = None
    hashes_de_imagens_vistas = set()

    print("Iniciando o agrupamento semântico por seções...")

    for el in elementos:
        # Verifica se o elemento é um título de seção
        e_titulo = (el.category == "Title" or el.category == "UncategorizedText") and padrao_titulo.match(el.text)

        if e_titulo:
            if chunk_atual:
                secoes_agrupadas.append(chunk_atual)
            
            chunk_atual = {
                "titulo_secao": el.text,
                "conteudo_combinado": f"INÍCIO DA SEÇÃO: {el.text}\n\n",
                "paginas": {el.metadata.page_number}
            }
        elif chunk_atual:
            conteudo_para_adicionar = ""
            
            if "Text" in el.category:
                conteudo_para_adicionar = el.text
            
            elif el.category == "Table":
                resumo_tabela = gerar_resumo(el.metadata.text_as_html, "tabela")
                conteudo_para_adicionar = f"\n--- TABELA ENCONTRADA ---\n{resumo_tabela}\n--- FIM DA TABELA ---\n"

            elif el.category == "Image":
                caminho_imagem = el.metadata.image_path
                hash_atual = calcular_hash_imagem(caminho_imagem)
                
                if hash_atual not in hashes_de_imagens_vistas:
                    hashes_de_imagens_vistas.add(hash_atual)
                    resumo_imagem = gerar_resumo(caminho_imagem, "imagem")
                    conteudo_para_adicionar = f"\n--- IMAGEM DESCRITA ---\n{resumo_imagem}\n--- FIM DA DESCRIÇÃO ---\n"

            if conteudo_para_adicionar:
                chunk_atual["conteudo_combinado"] += conteudo_para_adicionar + "\n"
                if hasattr(el.metadata, 'page_number'):
                    chunk_atual["paginas"].add(el.metadata.page_number)

    if chunk_atual:
        secoes_agrupadas.append(chunk_atual)

    print(f"Agrupamento concluído. {len(secoes_agrupadas)} seções semânticas foram criadas.")
    return secoes_agrupadas

def calcular_hash_imagem(caminho_imagem):
    """Calcula o hash SHA-256 de um arquivo de imagem."""
    sha256_hash = hashlib.sha256()
    with open(caminho_imagem, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()