"""Chat interno Xperiun - plataforma de visualização de cada etapa do RAG."""
import html

import numpy as np
import streamlit as st

st.set_page_config(page_title="Chat Interno Xperiun - RAG", page_icon="💬", layout="wide")

try:
    from src import config, generator, ingest, retriever, vectorstore
except ValueError as exc:  # configuração inválida no .env
    st.error(f"Configuração inválida no .env: {exc}")
    st.stop()


@st.cache_data
def load_pages():
    return ingest.load_documents()


@st.cache_data
def load_chunks():
    pages, _, _ = load_pages()
    return ingest.split_documents(pages)


@st.cache_resource(show_spinner="Gerando embeddings e carregando o Chroma em memória...")
def get_vectorstore():
    return vectorstore.build_vectorstore(load_chunks())


def get_store():
    """Chroma em cache. Se a geração falhar, guarda o erro na sessão e só tenta de novo
    quando o usuário clicar em "Tentar novamente" (st.cache_resource não guarda exceções)."""
    if not config.OPENAI_API_KEY:
        return None, "OPENAI_API_KEY ausente no .env: não é possível gerar os embeddings."
    if "embed_error" in st.session_state:
        return None, st.session_state.embed_error
    try:
        return get_vectorstore(), None
    except Exception as exc:
        st.session_state.embed_error = f"Falha ao gerar embeddings: {exc}"
        return None, st.session_state.embed_error


def _retry_embeddings():
    st.session_state.pop("embed_error", None)
    get_vectorstore.clear()


def show_store_error(error: str, key: str):
    st.error(error)
    if config.OPENAI_API_KEY:
        st.button("Tentar novamente", key=f"retry_{key}", on_click=_retry_embeddings)


def chunk_navigator(chunks, prefix: str) -> int:
    """Seletor + anterior/próximo. O índice é compartilhado entre as abas (st.session_state.idx)."""
    n = len(chunks)
    if st.session_state.get("idx", n) >= n:
        st.session_state.idx = 0
    sel_key = f"{prefix}_sel"
    st.session_state[sel_key] = st.session_state.idx

    def _move(step: int):
        st.session_state.idx = (st.session_state.idx + step) % n

    def _select():
        st.session_state.idx = st.session_state[sel_key]

    col_prev, col_sel, col_next = st.columns([1, 6, 1], vertical_alignment="bottom")
    col_prev.button("◀ Anterior", key=f"{prefix}_prev", on_click=_move, args=(-1,), width="stretch")
    col_next.button("Próximo ▶", key=f"{prefix}_next", on_click=_move, args=(1,), width="stretch")
    col_sel.selectbox(
        f"Selecione um chunk ({n} no total)",
        options=range(n),
        key=sel_key,
        on_change=_select,
        format_func=lambda i: (
            f"#{i} | {chunks[i].metadata['source']} p.{chunks[i].metadata['page']} | "
            f"{chunks[i].page_content[:60]}..."
        ),
    )
    return st.session_state.idx


st.title("Chat Interno Xperiun")
st.caption("PoC RAG: todos os usuários acessam todos os documentos de docs/ (sem gestão de acesso).")

with st.sidebar:
    st.header("Configuração")
    st.write(f"**Chunk size:** {config.CHUNK_SIZE}")
    st.write(f"**Chunk overlap:** {config.CHUNK_OVERLAP}")
    st.write(f"**Embedding:** `{config.EMBEDDING_MODEL}`")
    st.write(f"**Top K:** {config.TOP_K}")
    st.write(f"**LLM:** `{config.LLM_MODEL}` (effort {config.LLM_EFFORT}, max {config.LLM_MAX_TOKENS} tokens)")
    st.divider()
    st.write("OPENAI_API_KEY:", "✅ configurada" if config.OPENAI_API_KEY else "❌ ausente")
    st.write("ANTHROPIC_API_KEY:", "✅ configurada" if config.ANTHROPIC_API_KEY else "❌ ausente")

tab_setup, tab_chunks, tab_explorar, tab_embed, tab_busca, tab_chat = st.tabs(
    [
        "0. Setup",
        "1. Chunks (Retriever)",
        "2. Explorar chunks",
        "3. Embeddings",
        "4. Busca (Augmented)",
        "5. Chat (Generation)",
    ]
)

chunks = load_chunks()
n = len(chunks)

with tab_setup:
    st.subheader("Documentos encontrados em docs/ (base do RAG)")
    docs = config.list_documents()
    if not docs:
        st.warning(f"Nenhum PDF encontrado em {config.DOCS_DIR}")
    for doc in docs:
        st.write(f"📄 {doc.name} ({doc.stat().st_size / 1024:.1f} KB)")

    st.subheader("Contexto institucional em contexto/")
    st.caption("Não é indexado no RAG: será usado apenas como base do system prompt (Onda 5).")
    contexto_files = sorted(p for p in config.CONTEXTO_DIR.glob("*") if p.is_file())
    if not contexto_files:
        st.warning(f"Nenhum arquivo encontrado em {config.CONTEXTO_DIR}")
    for path in contexto_files:
        with st.expander(f"📝 {path.name} ({path.stat().st_size / 1024:.1f} KB)"):
            st.text(path.read_text(encoding="utf-8"))

with tab_chunks:
    pages, total_pages, skipped = load_pages()
    sizes = [len(c.page_content) for c in chunks]
    ovs = ingest.overlaps(chunks)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Documentos", len(config.list_documents()))
    c2.metric("Páginas totais", total_pages)
    c3.metric("Páginas com texto", len(pages))
    c4.metric("Chunks gerados", n)
    c5.metric("Maior chunk (caracteres)", max(sizes) if sizes else 0)
    c6.metric("Overlap médio (caracteres)", f"{sum(ovs) / len(ovs):.1f}" if ovs else "-")

    if skipped:
        st.warning(
            "Páginas sem texto extraível pelo PyMuPDF (candidatas a OCR): "
            + ", ".join(f"{s['source']} p.{s['page']}" for s in skipped)
        )
    if ovs:
        st.caption(
            f"Overlap entre chunks consecutivos da mesma página: mín {min(ovs)}, máx {max(ovs)}, "
            f"pares sem overlap: {sum(1 for o in ovs if o == 0)} de {len(ovs)} "
            f"(alvo até {config.CHUNK_OVERLAP}, corte sempre entre palavras). "
            "Rodapés (\"Página X de Y\" e a linha fixa do documento) são removidos antes do chunking."
        )

    st.subheader("Chunks por documento")
    per_doc = {}
    for c in chunks:
        per_doc[c.metadata["source"]] = per_doc.get(c.metadata["source"], 0) + 1
    st.dataframe(
        [{"Documento": doc, "Chunks": count} for doc, count in per_doc.items()],
        hide_index=True,
        width="stretch",
    )

    st.subheader("Todos os chunks")
    st.dataframe(
        [
            {
                "ID": c.metadata["chunk_id"],
                "Documento": c.metadata["source"],
                "Página": c.metadata["page"],
                "Caracteres": len(c.page_content),
                "Conteúdo": c.page_content,
            }
            for c in chunks
        ],
        hide_index=True,
        width="stretch",
    )

with tab_explorar:
    if not n:
        st.warning("Nenhum chunk gerado.")
    else:
        i = chunk_navigator(chunks, "explorar")
        chunk = chunks[i]
        text = chunk.page_content
        ov_prev = ingest.pair_overlap(chunks[i - 1], chunk) if i > 0 else 0
        ov_next = ingest.pair_overlap(chunk, chunks[i + 1]) if i < n - 1 else 0

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Documento", chunk.metadata["source"].removesuffix(".pdf"))
        m2.metric("Página", chunk.metadata["page"])
        m3.metric("Caracteres", len(text))
        m4.metric("Overlap c/ anterior", ov_prev)
        m5.metric("Overlap c/ próximo", ov_next)

        # Destaca o trecho repetido do chunk anterior (azul) e o que se repete no próximo (laranja)
        head = text[:ov_prev]
        tail_start = max(ov_prev, len(text) - ov_next)
        body, tail = text[ov_prev:tail_start], text[tail_start:]
        st.markdown(
            '<div style="white-space: pre-wrap; border: 1px solid #ccc; border-radius: 6px; '
            'padding: 12px; font-family: monospace;">'
            f'<mark style="background:#cfe2ff">{html.escape(head)}</mark>'
            f"{html.escape(body)}"
            f'<mark style="background:#ffe5b4">{html.escape(tail)}</mark></div>',
            unsafe_allow_html=True,
        )
        st.caption(
            "🟦 trecho repetido do chunk anterior · 🟧 trecho que se repete no próximo chunk "
            "(overlap só existe entre chunks da mesma página)"
        )

        with st.expander("Metadados"):
            st.json(chunk.metadata)

with tab_embed:
    store, error = get_store()
    if error:
        show_store_error(error, "embed")
    elif n:
        total_vectors = len(store.get()["ids"])
        t1, t2, t3 = st.columns(3)
        t1.metric("Embeddings no Chroma", total_vectors)
        t2.metric("Modelo", config.EMBEDDING_MODEL)

        i = chunk_navigator(chunks, "embed")
        ids = [str(j) for j in (i - 1, i, i + 1) if 0 <= j < n]
        data = store.get(ids=ids, include=["embeddings"])
        vecs = {int(k): np.array(v) for k, v in zip(data["ids"], data["embeddings"])}
        vec = vecs[i]
        t3.metric("Dimensão", len(vec))

        def _cos(a, b):
            return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))

        def _neighbor_sim(j: int) -> str:
            """Similaridade só com vizinho do mesmo documento."""
            if j not in vecs:
                return "-"
            if chunks[j].metadata["source"] != chunks[i].metadata["source"]:
                return "outro doc"
            return f"{_cos(vec, vecs[j]):.4f}"

        chunk = chunks[i]
        e1, e2, e3, e4 = st.columns(4)
        e1.metric("Chunk", f"#{i} - {chunk.metadata['source'].removesuffix('.pdf')} p.{chunk.metadata['page']}")
        e2.metric("Norma L2", f"{np.linalg.norm(vec):.4f}")
        e3.metric("Similaridade c/ anterior", _neighbor_sim(i - 1))
        e4.metric("Similaridade c/ próximo", _neighbor_sim(i + 1))
        st.caption("Similaridade de cosseno calculada apenas entre chunks vizinhos do mesmo documento.")

        with st.expander("Texto do chunk"):
            st.text(chunk.page_content)

        st.caption(f"Primeiras 10 de {len(vec)} dimensões:")
        st.code(np.array2string(vec[:10], precision=5, separator=", "))
        st.bar_chart(vec, height=200)

def md_safe(text: str) -> str:
    """Escapa `$` para o Streamlit não tratar "R$ ... R$" como fórmula LaTeX."""
    return text.replace("$", r"\$")


def show_retrieved(results):
    """Os K chunks retornados: posição, similaridade, origem e conteúdo."""
    for rank, (doc, score) in enumerate(results, start=1):
        meta = doc.metadata
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 2, 5])
            c1.metric("Posição", f"#{rank}")
            c2.metric("Similaridade", f"{score:.4f}")
            c3.metric("Origem", f"{meta['source'].removesuffix('.pdf')} p.{meta['page']} (chunk #{meta['chunk_id']})")
            st.text(doc.page_content)


with tab_busca:
    st.caption(
        "Busca semântica no Chroma em memória: a pergunta é vetorizada com o mesmo modelo "
        f"(`{config.EMBEDDING_MODEL}`) e são retornados os K chunks mais similares (cosseno). Sem IA nesta etapa."
    )
    store, error = get_store()
    if error:
        show_store_error(error, "busca")
    else:
        col_k, col_clear = st.columns([1, 5], vertical_alignment="bottom")
        k = col_k.number_input("K (chunks)", min_value=1, max_value=n, value=min(config.TOP_K, n), key="busca_k")
        if col_clear.button("Limpar histórico", key="busca_clear"):
            st.session_state.busca_hist = []

        hist = st.session_state.setdefault("busca_hist", [])
        query = (st.chat_input("Digite sua pergunta...", key="busca_input") or "").strip()
        if query:
            try:
                hist.append({"query": query, "k": k, "results": retriever.search(store, query, k)})
            except Exception as exc:
                st.error(f"Falha na busca: {exc}")

        for item in reversed(hist):
            with st.chat_message("user"):
                st.markdown(md_safe(item["query"]))
            with st.chat_message("assistant"):
                st.write(f"Top {item['k']} chunks mais similares:")
                show_retrieved(item["results"])

def show_answer_status(message):
    """Avisos sobre o fim da geração (recusa, truncamento, fallback)."""
    if message is None:
        return
    if message.stop_reason == "refusal":
        st.warning("O modelo recusou responder a esta pergunta.")
    elif message.stop_reason == "max_tokens":
        st.warning(f"Resposta cortada pelo limite de {config.LLM_MAX_TOKENS} tokens (LLM_MAX_TOKENS no .env).")
    if generator.used_fallback(message):
        st.caption(f"Respondido pelo modelo de fallback `{message.model}`.")
    st.caption(
        f"`{message.model}` · tokens de entrada {message.usage.input_tokens} · "
        f"tokens de saída {message.usage.output_tokens}"
    )


with tab_chat:
    st.caption(
        f"Generation: a pergunta, os K chunks da busca semântica e o system prompt são enviados ao "
        f"`{config.LLM_MODEL}`. Os chunks aparecem primeiro e a resposta logo abaixo."
    )
    store, error = get_store()
    if error:
        show_store_error(error, "chat")
    elif not config.ANTHROPIC_API_KEY:
        st.error("ANTHROPIC_API_KEY ausente no .env: não é possível gerar respostas.")
    else:
        col_k, col_clear = st.columns([1, 5], vertical_alignment="bottom")
        k_chat = col_k.number_input("K (chunks)", min_value=1, max_value=n, value=min(config.TOP_K, n), key="chat_k")
        if col_clear.button("Limpar conversa", key="chat_clear"):
            st.session_state.chat_hist = []

        with st.expander("System prompt enviado ao modelo"):
            st.text(generator.build_system_prompt())

        chat_hist = st.session_state.setdefault("chat_hist", [])
        for item in chat_hist:
            with st.chat_message("user"):
                st.markdown(md_safe(item["query"]))
            with st.chat_message("assistant"):
                if item["results"]:
                    with st.expander(f"Top {len(item['results'])} chunks recuperados", expanded=False):
                        show_retrieved(item["results"])
                if item["answer"]:
                    st.markdown(md_safe(item["answer"]))
                if item["error"]:
                    st.error(item["error"])
                else:
                    show_answer_status(item["message"])

        # strip(): pergunta só com espaços não gera busca nem chamada ao Claude
        question = (st.chat_input("Pergunte sobre contratos, preços, fornecedores...", key="chat_input") or "").strip()
        if question:
            with st.chat_message("user"):
                st.markdown(md_safe(question))
            with st.chat_message("assistant"):
                item = {"query": question, "results": [], "answer": "", "message": None, "error": None}
                try:
                    item["results"] = retriever.search(store, question, k_chat)
                except Exception as exc:
                    item["error"] = f"Falha na busca: {exc}"
                if item["results"]:
                    # PRD: primeiro os K chunks, para conferir a busca semântica; depois a resposta
                    st.write(f"Top {len(item['results'])} chunks recuperados:")
                    show_retrieved(item["results"])
                    st.divider()
                    final = {}

                    def _render(chunks):
                        # Guarda o texto cru (mesmo parcial, se a API falhar no meio) e exibe escapado
                        for piece in chunks:
                            item["answer"] += piece
                            yield md_safe(piece)

                    try:
                        client = generator.get_client()
                        with st.spinner(f"Gerando resposta com `{config.LLM_MODEL}`..."):
                            st.write_stream(_render(generator.stream_answer(client, question, item["results"], final)))
                        item["message"] = final.get("message")
                        show_answer_status(item["message"])
                    except Exception as exc:
                        item["error"] = generator.describe_api_error(exc)
                if item["error"]:
                    st.error(item["error"])
                chat_hist.append(item)
