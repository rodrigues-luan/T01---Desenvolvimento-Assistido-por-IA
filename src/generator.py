"""Onda 5: Generation - system prompt + pergunta + K chunks enviados ao Claude (API Anthropic)."""
from collections.abc import Iterator

import anthropic
from langchain_core.documents import Document

from src import config

SYSTEM_PROMPT_TEMPLATE = """Você é o assistente interno da Xperiun Tecnologia S.A. Você atende os times de vendas, pós-vendas, compliance, compras e as lideranças técnicas e não técnicas.

Você responde sobre gestão de contratos e seus reajustes, políticas de preço e suas regras, política de fornecedores e demais temas do time de receita.

## Como responder
- Use SOMENTE as informações dos trechos de documentos enviados em <documentos> junto com a pergunta. Eles foram recuperados por busca semântica nos documentos oficiais da empresa.
- Nunca invente valores, prazos, percentuais, cláusulas ou regras. Se os trechos não contiverem a resposta, ou a contiverem só em parte, diga isso claramente e indique o que faltou, em vez de completar com conhecimento próprio.
- Não cite áreas, pessoas, cargos ou canais de contato que não apareçam nos trechos.
- Responda a qualquer pergunta cuja resposta esteja nos trechos, mesmo que fuja dos temas acima: todos os usuários têm acesso a todos os documentos.
- Cite a origem de cada informação no formato [documento, p. X].
- Se os trechos trouxerem informações conflitantes, aponte o conflito e cite as duas fontes.
- Responda em português do Brasil, de forma direta e objetiva, com valores e prazos exatamente como aparecem nos trechos.

## Contexto institucional
O texto abaixo descreve quem é a Xperiun. Ele serve apenas para você entender a empresa, seus produtos e o vocabulário usado. Não é fonte de respostas: não use dados dele para responder perguntas, e baseie as respostas apenas nos trechos de <documentos>.

<contexto_institucional>
{contexto}
</contexto_institucional>"""


def build_system_prompt() -> str:
    files = sorted(p for p in config.CONTEXTO_DIR.glob("*") if p.is_file())
    contexto = "\n\n".join(p.read_text(encoding="utf-8").strip() for p in files)
    return SYSTEM_PROMPT_TEMPLATE.format(contexto=contexto or "(nenhum contexto disponível)")


def build_user_message(question: str, results: list[tuple[Document, float]]) -> str:
    chunks = "\n".join(
        f'<trecho documento="{doc.metadata["source"].removesuffix(".pdf")}" '
        f'pagina="{doc.metadata["page"]}" chunk="{doc.metadata["chunk_id"]}">\n'
        f"{doc.page_content}\n</trecho>"
        for doc, _ in results
    )
    return f"<documentos>\n{chunks}\n</documentos>\n\n<pergunta>\n{question}\n</pergunta>"


def get_client() -> anthropic.Anthropic:
    if not config.ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY não configurada no .env")
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def stream_answer(
    client: anthropic.Anthropic,
    question: str,
    results: list[tuple[Document, float]],
    final: dict,
) -> Iterator[str]:
    """Gera o texto da resposta em streaming. Ao terminar, `final["message"]` recebe a
    mensagem completa (stop_reason, usage). Exceções da API sobem para quem chamou.
    Se o modelo recusar no meio da resposta e o fallback assumir, emite um separador
    entre o texto parcial e a resposta do modelo de fallback."""
    with client.beta.messages.stream(
        model=config.LLM_MODEL,
        max_tokens=config.LLM_MAX_TOKENS,
        output_config={"effort": config.LLM_EFFORT},
        system=build_system_prompt(),
        messages=[{"role": "user", "content": build_user_message(question, results)}],
        # Se o modelo recusar por política, a API refaz a chamada num modelo de fallback
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
    ) as stream:
        for event in stream:
            if event.type == "content_block_start" and event.content_block.type == "fallback":
                yield FALLBACK_SEPARATOR.format(model=event.content_block.to.model)
            elif event.type == "content_block_delta" and event.delta.type == "text_delta":
                yield event.delta.text
        final["message"] = stream.get_final_message()


FALLBACK_SEPARATOR = "\n\n---\n*O modelo principal recusou; resposta do modelo de fallback `{model}`:*\n\n"


def used_fallback(message) -> bool:
    """Sinal oficial de que um modelo de fallback respondeu: entrada `fallback_message` em usage.iterations."""
    return any(getattr(i, "type", None) == "fallback_message" for i in (message.usage.iterations or []))


def describe_api_error(exc: Exception) -> str:
    """Mensagem amigável para a UI, do erro mais específico para o mais genérico."""
    if isinstance(exc, anthropic.AuthenticationError):
        return "ANTHROPIC_API_KEY inválida: verifique a chave no .env."
    if isinstance(exc, anthropic.PermissionDeniedError):
        return "A chave da Anthropic não tem permissão para este modelo."
    if isinstance(exc, anthropic.NotFoundError):
        return f"Modelo `{config.LLM_MODEL}` não encontrado: verifique LLM_MODEL no .env."
    if isinstance(exc, anthropic.RateLimitError):
        return "Limite de requisições da Anthropic atingido. Tente novamente em instantes."
    if isinstance(exc, anthropic.BadRequestError):
        return f"Requisição inválida para a API da Anthropic: {exc.message}"
    if isinstance(exc, anthropic.APITimeoutError):
        return "A API da Anthropic demorou demais para responder. Tente novamente."
    if isinstance(exc, anthropic.APIConnectionError):
        return "Sem conexão com a API da Anthropic. Verifique a internet."
    if isinstance(exc, (anthropic.OverloadedError, anthropic.InternalServerError)):
        return UNSTABLE_MESSAGE
    if isinstance(exc, anthropic.APIStatusError):
        # Erro enviado no meio do stream chega com status 200 e o tipo no corpo
        body = exc.body if isinstance(exc.body, dict) else {}
        error = body.get("error") if isinstance(body.get("error"), dict) else {}
        if error.get("type") in {"overloaded_error", "api_error"}:
            return UNSTABLE_MESSAGE
        return f"Erro da API da Anthropic ({exc.status_code}): {error.get('message') or exc.message}"
    return f"Falha ao gerar a resposta: {exc}"


UNSTABLE_MESSAGE = "A API da Anthropic está sobrecarregada ou instável no momento. Tente novamente em instantes."
