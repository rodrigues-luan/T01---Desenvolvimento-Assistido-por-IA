"""Configuração central: todos os parâmetros vêm do .env (ver .env.example)."""
import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")


def _env_str(name: str, default: str) -> str:
    """Variável vazia no .env (ex.: `CHUNK_SIZE=`) cai no default."""
    return os.getenv(name, "").strip() or default


def _env_int(name: str, default: int) -> int:
    raw = _env_str(name, str(default))
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} deve ser um inteiro, recebido: {raw!r}") from exc


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()

DOCS_DIR = ROOT_DIR / _env_str("DOCS_DIR", "docs")
CONTEXTO_DIR = ROOT_DIR / _env_str("CONTEXTO_DIR", "contexto")

CHUNK_SIZE = _env_int("CHUNK_SIZE", 350)
CHUNK_OVERLAP = _env_int("CHUNK_OVERLAP", 40)
if not 0 <= CHUNK_OVERLAP < CHUNK_SIZE:
    raise ValueError(
        f"CHUNK_OVERLAP ({CHUNK_OVERLAP}) deve ser >= 0 e menor que CHUNK_SIZE ({CHUNK_SIZE})"
    )

EMBEDDING_MODEL = _env_str("EMBEDDING_MODEL", "text-embedding-3-small")

TOP_K = _env_int("TOP_K", 3)
if TOP_K < 1:
    raise ValueError(f"TOP_K ({TOP_K}) deve ser >= 1")

LLM_MODEL = _env_str("LLM_MODEL", "claude-opus-5-5")
LLM_MAX_TOKENS = _env_int("LLM_MAX_TOKENS", 16000)
LLM_EFFORT = _env_str("LLM_EFFORT", "medium")
if LLM_EFFORT not in {"low", "medium", "high", "xhigh", "max"}:
    raise ValueError(f"LLM_EFFORT ({LLM_EFFORT!r}) deve ser low, medium, high, xhigh ou max")


def list_documents() -> list[Path]:
    """Todos os PDFs de docs/ (PoC: todos os usuários acessam todos os documentos)."""
    return sorted(DOCS_DIR.glob("*.pdf"))
