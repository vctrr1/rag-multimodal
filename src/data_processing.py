from pypdf import PdfWriter, PdfReader
from unstructured.partition.pdf import partition_pdf

def limpar_pdf(caminho_original, caminho_saida, paginas_a_manter):
    reader = PdfReader(caminho_original)
    writer = PdfWriter()

    for i in paginas_a_manter:
        if i < len(reader.pages):
            writer.add_page(reader.pages[i])

    with open(caminho_saida, "wb") as f:
        writer.write(f)
    print(f"PDF limpo salvo em: {caminho_saida}")



