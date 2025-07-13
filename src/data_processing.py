import os
from pypdf import PdfWriter, PdfReader
from unstructured.partition.pdf import partition_pdf
from PIL import Image
import google.generativeai as genai

from config import RAW_DATA_DIR, PROCESSED_DATA_DIR, IMAGE_DIR, GOOGLE_API_KEY

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
        # Estratégia "hi_res" para PDFs com leiaute complexo
        strategy = "hi_res",
        # Extrai imagens contidas no PDF
        extract_images_in_pdf = True,
        # Usa o modelo de detecção de leiaute para entender tabelas
        infer_table_structure = True,
        # Idioma para melhorar a extração de texto
        languages = ["por"],
        # Diretório para salvar os arquivos de imagem
        extract_image_block_output_dir = pasta_imagens,
    )
    
    # Separa os elementos por tipo para facilitar o processamento
    textos = [el for el in elementos if el.category == "NarrativeText" or el.category == "Title"]
    tabelas_html = [el for el in elementos if el.category == "Table"]
    imagens = [el for el in elementos if el.category == "Image"]

    print(f"Extração concluída. Encontrados:")
    print(f"- {len(textos)} blocos de texto")
    print(f"- {len(tabelas_html)} tabelas")
    print(f"- {len(imagens)} imagens")

    return textos, tabelas_html, imagens


def gerar_resumo_com_gemini(conteudo, tipo_conteudo):

    try:
        genai.configure(api_key=GOOGLE_API_KEY)
    except Exception as e:
        print(f"Erro ao configurar a API do Google Generative AI: {e}")

    """Usa o Gemini 1.5 Pro para gerar um resumo textual de uma imagem ou tabela."""
    model = genai.GenerativeModel('models/gemini-1.5-pro-latest')

    # Prompts que definimos anteriormente...
    prompt_imagem = """
        Você é um engenheiro biomédico especialista em equipamentos hospitalares. 
        Sua tarefa é analisar a imagem de um manual de bomba de infusão e descrevê-la em detalhes técnicos precisos.
        Descreva todos os componentes visíveis, como botões, tela, indicadores LED, conexões e símbolos. 
        Se houver texto na imagem, transcreva-o. Seja minucioso para que esta descrição possa ser usada para responder a perguntas técnicas sobre o equipamento.
        """,
    prompt_tabela = """
        Você é um analista de dados especialista em documentação técnica.
        Sua tarefa é analisar a seguinte tabela (em formato HTML) extraída de um manual de bomba de infusão.
        Resuma o propósito da tabela e extraia as informações mais críticas contidas nela em um formato de texto claro e legível.
        Preserve os valores e unidades exatas. O objetivo é que este resumo textual represente fielmente os dados da tabela para buscas futuras.
        """
    
    prompt_base = {"imagem": prompt_imagem, "tabela": prompt_tabela}

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