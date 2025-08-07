import os
import re
import hashlib
import time
from pypdf import PdfWriter, PdfReader
from unstructured.partition.pdf import partition_pdf
from PIL import Image
import google.generativeai as genai

# Importa as configurações
from src.config import RAW_DATA_DIR, PROCESSED_DATA_DIR, IMAGE_DIR, GOOGLE_API_KEY

# Configura a API do Gemini
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"Erro ao configurar a API do Google Generative AI: {e}")

model = genai.GenerativeModel('models/gemini-1.5-pro-latest')

def limpar_pdf(nome_arquivo_original, nome_arquivo_saida, paginas_a_manter):
    # (Esta função permanece inalterada)
    caminho_original = os.path.join(RAW_DATA_DIR, nome_arquivo_original)
    caminho_saida = os.path.join(PROCESSED_DATA_DIR, nome_arquivo_saida)
    os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
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
    # (Esta função permanece inalterada)
    print(f"Iniciando a extração do arquivo: {caminho_pdf_processado}")
    pasta_imagens = os.path.join(IMAGE_DIR, nome_projeto)
    os.makedirs(pasta_imagens, exist_ok=True)
    elementos = partition_pdf(
        filename=caminho_pdf_processado, 
        strategy="hi_res",
        chunking_strategy="by_title",
        extract_images_in_pdf=True, 
        infer_table_structure=True,
        languages=["por"], 
        extract_image_block_output_dir=pasta_imagens,
    )
    print(f"Extração concluída. {len(elementos)} elementos brutos encontrados.")
    return elementos

def gerar_resumo(conteudo, tipo_conteudo):
    prompt_base = {
        "imagem": """
        Você é um engenheiro biomédico especialista em equipamentos hospitalares. 
        Sua tarefa é analisar a imagem de um manual de bomba de infusão e descrevê-la em detalhes técnicos precisos.
        Descreva todos os componentes visíveis, como botões, tela, indicadores LED, conexões e símbolos. 
        Se houver texto na imagem, transcreva-o. 
        Seja minucioso para que esta descrição possa ser usada para responder a perguntas técnicas sobre o equipamento.
        """,
        "tabela": """
        Você é um analista de dados especialista em documentação técnica.
        Sua tarefa é analisar a seguinte tabela (em formato HTML) extraída de um manual de bomba de infusão.
        Não resuma nada, As tabelas são instruções tecnicas e exatas. O objetivo é que este resumo textual represente fielmente os dados da tabela para buscas futuras.
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

def calcular_hash_imagem(caminho_imagem):
    # (Esta função permanece inalterada)
    sha256_hash = hashlib.sha256()
    with open(caminho_imagem, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

# ==============================================================================
# FUNÇÃO DE AGRUPAMENTO SEMÂNTICO (VERSÃO ROBUSTA)
# ==============================================================================
def agrupar_elementos_por_secao(elementos):
    """
    Agrupa elementos extraídos em chunks semânticos baseados nos títulos das seções,
    de forma robusta e independente da categorização do 'unstructured'.
    """
    # Regex para identificar títulos de seção (ex: "1.2", "5.3.1", "Apêndice A")
    padrao_titulo = re.compile(r'^\d+(\.\d+)*\s|\bAPÊNDICE\s[A-Z]\b', re.IGNORECASE)
    
    secoes_agrupadas = []
    chunk_atual = None
    hashes_de_imagens_vistas = set()
    
    print("\n--- 🔄 Iniciando o agrupamento semântico por seções (Estratégia Robusta)... ---")
    
    total_elementos = len(elementos)
    for i, el in enumerate(elementos):
        
        # Ignora elementos sem texto, a menos que sejam imagens
        if not hasattr(el, 'text') or not el.text.strip():
            if el.category != "Image":
                continue

        texto_elemento = el.text if hasattr(el, 'text') else ''

        # ==========================================================
        # LÓGICA DE IDENTIFICAÇÃO DE TÍTULO CORRIGIDA E ROBUSTA
        # ==========================================================
        # Se o texto do elemento corresponde ao nosso padrão de título E é curto o suficiente,
        # nós o TRATAMOS como um título, não importa sua categoria.
        e_titulo = padrao_titulo.match(texto_elemento) and len(texto_elemento) < 150
        # ==========================================================

        if e_titulo:
            if chunk_atual:
                secoes_agrupadas.append(chunk_atual)
            
            print(f"\n[+] Nova Seção Encontrada: {texto_elemento.strip()}")
            chunk_atual = {
                "titulo_secao": texto_elemento.strip(),
                "conteudo_combinado": f"INÍCIO DA SEÇÃO: {texto_elemento.strip()}\n\n",
                "paginas": {el.metadata.page_number} if hasattr(el.metadata, 'page_number') else set()
            }
            # Se o título também for um texto narrativo, adiciona ao conteúdo
            if el.category == "NarrativeText":
                 chunk_atual["conteudo_combinado"] += texto_elemento + "\n"

        elif chunk_atual:
            conteudo_para_adicionar = ""
            
            if "Text" in el.category:
                conteudo_para_adicionar = texto_elemento
            
            elif el.category == "Table":
                pagina = el.metadata.page_number if hasattr(el.metadata, 'page_number') else 'N/A'
                print(f"    -> 📊 Tabela encontrada na pág. {pagina}. Gerando resumo via API...")
                resumo_tabela = gerar_resumo(el.metadata.text_as_html, "tabela")
                conteudo_para_adicionar = f"\n--- INÍCIO DA TABELA ---\n{resumo_tabela}\n--- FIM DA TABELA ---\n"
                print("       - Resumo da tabela concluído.")
                time.sleep(2)

            elif el.category == "Image":
                pagina = el.metadata.page_number if hasattr(el.metadata, 'page_number') else 'N/A'
                print(f"    -> 🖼️ Imagem encontrada na pág. {pagina}. Analisando...")
                caminho_imagem = el.metadata.image_path
                hash_atual = calcular_hash_imagem(caminho_imagem)
                
                if hash_atual in hashes_de_imagens_vistas:
                    print("       - Imagem duplicada. Ignorando.")
                else:
                    print("       - Imagem ÚNICA. Gerando resumo via API...")
                    hashes_de_imagens_vistas.add(hash_atual)
                    resumo_imagem = gerar_resumo(caminho_imagem, "imagem")
                    conteudo_para_adicionar = f"\n--- DESCRIÇÃO DA IMAGEM ---\n{resumo_imagem}\n--- FIM DA DESCRIÇÃO ---\n"
                    print("       - Resumo da imagem concluído.")
                    time.sleep(2)

            if conteudo_para_adicionar:
                chunk_atual["conteudo_combinado"] += conteudo_para_adicionar + "\n"
                if hasattr(el.metadata, 'page_number'):
                    chunk_atual["paginas"].add(el.metadata.page_number)

    if chunk_atual:
        secoes_agrupadas.append(chunk_atual)

    print(f"\n--- ✅ Agrupamento concluído. {len(secoes_agrupadas)} seções semânticas foram criadas. ---")
    return secoes_agrupadas