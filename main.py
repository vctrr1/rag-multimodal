from src.data_processing import limpar_pdf, extrair_elementos_do_manual, agrupar_elementos_por_secao
from src.vector_db import popular_banco_com_secoes

NOME_ARQUIVO_ORIGINAL = "E-Link_Lifemed.pdf"
NOME_ARQUIVO_LIMPO = "E-Link_Lifemed_clean.pdf"
PAGINAS_PARA_MANTER = range(6, 75) # Manter da página 7 até a 75

def exec_pipeline():

    print("--- INICIANDO --- ")

    # remove páginas desnecessarias
    caminho_pdf_limpo = limpar_pdf(
        NOME_ARQUIVO_ORIGINAL,
        NOME_ARQUIVO_LIMPO,
        PAGINAS_PARA_MANTER
    )

    elementos_brutos = extrair_elementos_do_manual(caminho_pdf_limpo, NOME_ARQUIVO_ORIGINAL.split('.')[0])
    
    sessoes_semanticas = agrupar_elementos_por_secao(elementos_brutos)

    popular_banco_com_secoes(sessoes_semanticas, NOME_ARQUIVO_ORIGINAL)
    
    print("\n--- PIPELINE CONCLUÍDO COM SUCESSO! ---")
    print("O banco de dados vetorial está pronto para ser usado pela aplicação do chatbot.")


if __name__ == "__main__":
    exec_pipeline()