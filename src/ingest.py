"""Onda 2: leitura dos PDFs de docs/ (PyMuPDF) e chunking."""
import re
from pathlib import Path

import pymupdf
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src import config


PAGE_NUMBER_RE = re.compile(r"^Página \d+ de \d+$")


def strip_footer(pages_lines: list[list[str]]) -> list[list[str]]:
    """Remove o rodapé: a linha "Página X de Y" e, antes dela, a linha que se repete
    no fim de todas as páginas do documento (ex.: "Xperiun Tecnologia S.A. - Confidencial")."""
    cleaned = [lines[:-1] if lines and PAGE_NUMBER_RE.match(lines[-1]) else lines for lines in pages_lines]
    last_lines = {lines[-1] for lines in cleaned if lines}
    if len(cleaned) > 1 and len(last_lines) == 1 and all(cleaned):
        cleaned = [lines[:-1] for lines in cleaned]
    return cleaned


def load_pdf(path: Path) -> tuple[list[Document], int, list[int]]:
    """Um Document por página. Retorna (páginas com texto, total de páginas, páginas puladas)."""
    with pymupdf.open(path) as pdf:
        total = pdf.page_count
        raw = [[line.strip() for line in page.get_text().splitlines() if line.strip()] for page in pdf]

    pages, skipped = [], []
    for number, lines in enumerate(strip_footer(raw), start=1):
        text = "\n".join(lines)
        if not text:
            skipped.append(number)  # sem texto extraível: candidata a OCR
            continue
        pages.append(Document(page_content=text, metadata={"source": path.name, "page": number}))
    return pages, total, skipped


def load_documents() -> tuple[list[Document], int, list[dict]]:
    """Retorna (páginas com texto, total de páginas, [{source, page}] das puladas)."""
    pages, total, skipped = [], 0, []
    for path in config.list_documents():
        doc_pages, doc_total, doc_skipped = load_pdf(path)
        pages.extend(doc_pages)
        total += doc_total
        skipped.extend({"source": path.name, "page": n} for n in doc_skipped)
    return pages, total, skipped


def split_documents(pages: list[Document]) -> list[Document]:
    # Corte em qualquer espaço em branco (espaço ou quebra de linha): o PDF vem quebrado em
    # linhas de ~90 caracteres e, com os separadores padrão ("\n"), o splitter não conseguia
    # reaproveitar 40 caracteres de overlap.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=config.CHUNK_SIZE,
        chunk_overlap=config.CHUNK_OVERLAP,
        separators=[r"\s", ""],
        is_separator_regex=True,
        add_start_index=True,
    )
    chunks = splitter.split_documents(pages)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
    return chunks


def same_page(a: Document, b: Document) -> bool:
    return (a.metadata["source"], a.metadata["page"]) == (b.metadata["source"], b.metadata["page"])


def pair_overlap(a: Document, b: Document) -> int:
    """Caracteres do fim de `a` repetidos no início de `b` (0 se páginas diferentes)."""
    if not same_page(a, b):
        return 0
    end_a = a.metadata["start_index"] + len(a.page_content)
    return max(0, end_a - b.metadata["start_index"])


def overlaps(chunks: list[Document]) -> list[int]:
    """Caracteres sobrepostos entre chunks consecutivos da mesma página."""
    return [pair_overlap(a, b) for a, b in zip(chunks, chunks[1:]) if same_page(a, b)]
