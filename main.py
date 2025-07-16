from src.data_processing import limpar_pdf, extrair_elementos_do_manual
from src.vector_db import popular_banco_vetorial

NOME_ARQUIVO_ORIGINAL = "E-Link_Lifemed.pdf"
NOME_ARQUIVO_LIMPO = "E-Link_Lifemed_clean.pdf"
PAGINAS_PARA_MANTER = range(6, 75) # Manter da página 7 até a 75

def exec_pipeline():

    print("--- INICIANDO PIPELINE DE PROCESSAMENTO DE DADOS --- ")

    # remove páginas desnecessarias
    caminho_pdf_limpo = limpar_pdf(
        NOME_ARQUIVO_ORIGINAL,
        NOME_ARQUIVO_LIMPO,
        PAGINAS_PARA_MANTER
    )

    # extrair elementos do PDF que foi limpo
    textos, tabelas, imagens = extrair_elementos_do_manual(caminho_pdf_limpo, NOME_ARQUIVO_ORIGINAL.split('.')[0])
    
    # Popular o banco de dados com os elementos extraídos
    popular_banco_vetorial(textos, tabelas, imagens, NOME_ARQUIVO_ORIGINAL.split('.')[0])
    
    print("\n--- PIPELINE CONCLUÍDO COM SUCESSO! ---")
    print("O banco de dados vetorial está pronto para ser usado pela aplicação do chatbot.")


if __name__ == "__main__":
    exec_pipeline()