"""Onda 4: busca semântica (Augmented) - retorna os K chunks mais similares, sem LLM."""
from langchain_chroma import Chroma
from langchain_core.documents import Document

from src import config


def search(store: Chroma, query: str, k: int = config.TOP_K) -> list[tuple[Document, float]]:
    """(chunk, similaridade de cosseno) ordenados do mais para o menos similar.
    A pergunta é vetorizada com o mesmo modelo de embedding da indexação."""
    return store.similarity_search_with_relevance_scores(query, k=k)
