"""Onda 2: embeddings OpenAI + Chroma em memória (existe só enquanto o app roda)."""
import uuid

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from src import config


def get_embeddings() -> OpenAIEmbeddings:
    if not config.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY não configurada no .env")
    return OpenAIEmbeddings(model=config.EMBEDDING_MODEL, api_key=config.OPENAI_API_KEY)


def build_vectorstore(chunks: list[Document]) -> Chroma:
    """Sem persist_directory: Chroma efêmero, em memória. Distância de cosseno, para que
    o score da busca seja a similaridade de cosseno (1 - distância)."""
    return Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        collection_name=f"xperiun-{uuid.uuid4().hex[:8]}",
        collection_metadata={"hnsw:space": "cosine"},
        ids=[str(c.metadata["chunk_id"]) for c in chunks],
    )
