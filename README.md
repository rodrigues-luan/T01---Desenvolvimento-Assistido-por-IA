# Chat Interno Xperiun - RAG

PoC de chat interno com arquitetura RAG (LangChain + Streamlit + Chroma em memória + Claude). Ver `PRD.md` e `SPEC.md`.
Todos os usuários acessam todos os documentos de `docs/` (sem gestão de acesso).

## Como rodar (Windows)

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
copy .env.example .env   # preencha OPENAI_API_KEY e ANTHROPIC_API_KEY
.venv\Scripts\python -m streamlit run app.py
```

Requer Python 3.11+. O app abre em http://localhost:8501.

## Etapas na plataforma

| Aba | Etapa | O que mostra |
|---|---|---|
| 0. Setup | - | PDFs de `docs/` e o contexto institucional de `contexto/` (usado só no system prompt) |
| 1. Chunks | Retriever | Totais, chunks por documento, overlap médio e tabela com todos os chunks |
| 2. Explorar chunks | Retriever | Navegação chunk a chunk com o overlap destacado |
| 3. Embeddings | Retriever | Total no Chroma, vetor de cada chunk e similaridade com os vizinhos |
| 4. Busca | Augmented | Pergunta e os K chunks mais similares (sem IA) |
| 5. Chat | Generation | K chunks recuperados e, em seguida, a resposta do Claude com citações |

## Configuração (.env)

| Variável | Padrão | Uso |
|---|---|---|
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | 350 / 40 | Chunking (corte entre palavras, overlap de até 40) |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | Embeddings OpenAI |
| `TOP_K` | 3 | Chunks retornados (ajustável também na tela) |
| `LLM_MODEL` | `claude-opus-5-5` | Modelo da geração |
| `LLM_MAX_TOKENS` | 16000 | Limite de tokens da resposta (inclui o raciocínio do modelo) |
| `LLM_EFFORT` | `medium` | Esforço do modelo: low, medium, high, xhigh, max |

Os embeddings são gerados uma vez por execução do app (Chroma em memória, sem persistência).
