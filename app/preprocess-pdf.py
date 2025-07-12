from pypdf import PdfWriter, PdfReader

def limpar_pdf(caminho_original, caminho_saida, paginas_a_manter):
    reader = PdfReader(caminho_original)
    writer = PdfWriter()

    for i in paginas_a_manter:
        if i < len(reader.pages):
            writer.add_page(reader.pages[i])

    with open(caminho_saida, "wb") as f:
        writer.write(f)
    print(f"PDF limpo salvo em: {caminho_saida}")

# --- Exemplo de uso ---
# Supondo que o conteúdo útil do seu manual começa na página 6 e vai até a 58
paginas_a_manter = range(6, 75) # Em Python, o índice começa em 0, então a página 6 é o índice 5

caminho_do_manual_original = "..\\data\\pdfs\\E-Link_Lifemed.pdf"
caminho_do_manual_limpo = "..\\data\\clean-pdfs\\E-Link_Lifemed_clean.pdf"

limpar_pdf(caminho_do_manual_original, caminho_do_manual_limpo, paginas_a_manter)