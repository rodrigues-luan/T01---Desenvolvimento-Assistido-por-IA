# Revisão - Onda 5 - Iteração 1
**Data:** 2026-11-02 | **Revisor:** Tech Lead (agente revisor) | **Veredito:** APROVADO COM RESSALVAS

## 1. Resumo executivo
A Onda 5 (Generation, a última) entregou `src/generator.py`, que usa o SDK oficial `anthropic` 2.3.0 com `client.beta.messages.stream`. A chamada usa `claude-opus-5-5`, `max_tokens` e `effort` vindos do env e fallback de recusa feito pelo servidor. Não envia `temperature` nem `thinking`. A aba "5. Chat (Generation)" mostra **primeiro os K chunks** e **depois** a resposta em streaming, com avisos de recusa, truncamento e fallback, tokens usados e histórico. Rodei 4 perguntas reais, uma por tema do PRD. As 4 terminaram em `end_turn` e citaram `[documento, p. X]`. Nenhuma inventou dado: quando o chunk não tinha a informação (faixas de crédito do SLA, periodicidade da cota do Sênior), o modelo disse isso. Os 13 caminhos de erro simulados com mock deram 0 exceções, os chunks continuaram na tela e apareceu uma mensagem na UI. As Ondas 1 a 4 não regrediram. Não há achado bloqueante nem alto. O principal risco é **R5-01 (MÉDIA)**: o `st.markdown` do Streamlit trata `$` como início de fórmula LaTeX, e as respostas trazem valores em `R$`. Sobre o `.env`: no início da revisão ele tinha `LLM_MAX_TOKENS=1024`. Às 09:47:15, durante a revisão, o arquivo foi alterado (não fui eu) e hoje tem `16000` (R5-05).

## 2. Escopo revisado
- Onda/objetivo segundo a SPEC: "5 - Finalizando, faremos o Generation, onde usarei exatamente a API do claude na versão opus 5.5 para enviar tanto o system prompt que você criará, a pergunta do usuário e os K chunks retornados na etapa anterior." PRD: "precisa trazer sempre os K chunks para conferirmos se a busca semântica funcionou e so depois trazer a resposta".
- Onda e iteração: informadas no pedido (Onda 5, iteração 1). Batem com `revisoes/`: não existia revisão da Onda 5, e `onda-4-revisao-1.md` liberou a Onda 5. Como é a onda final, também fiz uma checagem de regressão de ponta a ponta das Ondas 1 a 4 (ações #13 a #16).
- Decisões já aprovadas pelo usuário (repassadas no pedido): K=3 configurável; Chroma em memória com cache; `contexto/` fora do RAG, usado só no system prompt; venv; sem gestão de acesso; overlap opção (a); `git init` só no final.
- R3-04, R4-01 e R4-02: o usuário só disse "execute a onda final" e não aprovou nenhum dos três. Continuam pendentes e opcionais, com a severidade original.
- Arquivos analisados: `src/generator.py` (novo), `app.py` (aba 5 e sidebar), `src/config.py`, `requirements.txt`, `.env.example`, `README.md`, `.gitignore`. Para checar regressão: `src/ingest.py`, `src/retriever.py`, `src/vectorstore.py`. Do `.env` li só os nomes das chaves (valores mascarados) e os valores não secretos `LLM_MODEL` e `LLM_MAX_TOKENS`.
- Revisão anterior considerada: `revisoes/onda-4-revisao-1.md`.

## 3. O que o revisor fez (rastreabilidade)
| # | Ação | Comando/arquivo | Resultado |
|---|---|---|---|
| 1 | Versão do Python e dependências | `.venv/Scripts/python --version`; `pip check`; `pip list` | 3.13.1, OK (>= 3.11). "No broken requirements found." `anthropic 2.3.0` instalado. `langchain-anthropic` não está mais instalado nem em `requirements.txt`. `langchain`, `langchain-openai`, `langchain-chroma` e `langchain-text-splitters` continuam |
| 2 | `.env` (valores mascarados) | `sed 's/=.*/=<redacted>/' .env`; `grep LLM .env` | No início da revisão: `LLM_MODEL=claude-opus-5-5`, `LLM_MAX_TOKENS=1024`, sem `LLM_EFFORT` (o código usa o default `medium`). Às 09:47:15 o `.env` foi alterado por outra pessoa (não pelo revisor, que só leu o arquivo) e hoje tem `LLM_MAX_TOKENS=16000` (`ls --time-style=full-iso`; `config.LLM_MAX_TOKENS` = 16000). Ver R5-05 |
| 3 | Assinatura do SDK | `anthropic/resources/beta/messages/messages.py:1717` (`stream`), `:137`/`:141`/`:303-310`; `types/beta/beta_fallbacks_param.py` | `stream()` aceita `fallbacks` (`Iterable[...]` ou `"default"`), `output_config` e `betas`. Docstring: "The string "default" requests the requested model's server-defined default fallback configuration" |
| 4 | Como o SDK indica o fallback | `types/beta/beta_fallback_block.py:13-21`, `beta_fallback_message_iteration_usage.py:11-19`, `lib/streaming/_beta_messages.py:528-531` | No streaming, o `model` do snapshot é trocado pelo `to.model` do bloco `fallback`. Pela documentação do SDK, o sinal oficial de que um fallback respondeu é a entrada `fallback_message` em `usage.iterations` (ver R5-03) |
| 5 | **Requisição montada pelo app** | AppTest + `anthropic.Anthropic(http_client=httpx2.Client(transport=MockTransport))` para capturar o corpo e os headers, **sem rede** | `POST /v1/messages`, header `anthropic-beta: server-side-fallback-2026-07-01`. Corpo com `model=claude-opus-5-5`, `max_tokens=16000` (valor do `.env` atual), `output_config={'effort': 'medium'}`, `fallbacks='default'`, `stream=True`. **Sem `temperature` e sem `thinking`**. `system` igual a `build_system_prompt()`. Mensagem do usuário: `<documentos>` com 3 `<trecho documento=".." pagina=".." chunk="..">` e depois `<pergunta>` |
| 6 | System prompt | aba 5, expander "System prompt enviado ao modelo" | 6.458 caracteres. Contém o texto de `contexto/contexto.txt` ("DOCUMENTO MESTRE...") dentro de `<contexto_institucional>`, com a instrução "Não é fonte de respostas" |
| 7 | Ordem na tela (PRD) | árvore de elementos da mensagem ativa (AppTest + mock) | "Top 3 chunks recuperados:" → 3 blocos (posição, similaridade, origem, texto) → divisor → resposta → legenda de tokens. **Chunks antes da resposta** |
| 8 | Avisos de fim de geração (mock SSE) | `stop_reason` `max_tokens`, `refusal` e bloco `fallback` | `max_tokens`: aviso "Resposta cortada pelo limite de 16000 tokens (LLM_MAX_TOKENS...)". `refusal`: aviso "O modelo recusou responder a esta pergunta.". Fallback: legenda "Respondido pelo modelo de fallback `modelo-fallback-teste`", **mas o texto exibido foi "PARCIAL-DO-MODELO-QUE-RECUSOU RESPOSTA-DO-FALLBACK"** (R5-03). 0 exceções |
| 9 | Caminhos de erro (mock, sem rede) | 401, 403, 404, 429, 400, 500, 529, `ReadTimeout`, `ConnectError` e erro SSE no meio do stream | Em todos: 0 exceções, os 3 chunks continuam na tela e aparece `st.error`. 401 → "ANTHROPIC_API_KEY inválida...", 403 → "...não tem permissão...", 404 → "Modelo `claude-opus-5-5` não encontrado...", 429 → "Limite de requisições...", timeout → "...demorou demais...", conexão → "Sem conexão...". 400/500/529 mostram o texto bruto `Error code: 500 - {'type': ...}`. O erro no meio do stream mostra `Erro da API da Anthropic (200): {'type': 'error', ...}`, e o texto parcial some no histórico (R5-02) |
| 10 | Histórico após rerun | AppTest, 14 perguntas acumuladas | 28 mensagens, 0 exceções. Cada item mostra o expander "Top 3 chunks recuperados" (fechado) antes da resposta, do aviso ou do erro |
| 11 | K na tela, pergunta vazia, falha da busca, sem chave | mock | K=5 → 5 `<trecho>` no request e 5 chunks na tela. Pergunta `"   "` → **1 chamada ao Claude** (R5-04). Falha simulada da busca → "Falha na busca: ..." e 0 chamadas ao Claude. `ANTHROPIC_API_KEY=""` → `st.error` "ANTHROPIC_API_KEY ausente..." sem `chat_input`, enquanto a aba 4 continua com o `chat_input` dela |
| 12 | Validação de `LLM_EFFORT` | `LLM_EFFORT=foo` + `import src.config` | `ValueError: LLM_EFFORT ('foo') deve ser low, medium, high, xhigh ou max` (o `app.py:9-13` transforma isso em `st.error`) |
| 13 | **Rodada real** (orçamento: 1 indexação + até 6 buscas + até 4 Claude) | AppTest com as chaves do `.env` e wrappers de contagem | **Usado:** indexação 1x (49 textos, `text-embedding-3-small`), **4 buscas**, **4 chamadas ao Claude**. Resultado na tabela abaixo |
| 14 | Regressão das Ondas 1 a 4 (sem custo) | script com `ingest` + AppTest com embedding falso | 3 PDFs, 6 páginas, 0 puladas, **49 chunks**, maior chunk **350**, overlap mín 28 / máx 39 / média 36,0, 0 pares sem overlap em 43. Aba 1: métricas 3/6/6/49/350/36.0, tabelas 3x2 e 49x5. Aba 2: "Próximo" leva `idx` para 1. Aba 3: 49 embeddings. Aba 4: 1 busca → 2 mensagens com 9 métricas. Indexação **1x** em todo o teste; a pergunta da aba 5 não altera o histórico da aba 4. Sidebar mostra 350/40/modelo/K=3/LLM com effort e max tokens |
| 15 | Subida real do servidor | `streamlit run app.py --server.port 8598 --server.headless true` + `/_stcore/health` | `ok`. Processo (PID 18312) encerrado com `taskkill`. A porta 8501 do usuário (PID 9692) **não foi tocada** e continua escutando. Nenhuma sessão de navegador aberta |
| 16 | Segredos | `grep -rn "sk-..."` fora do `.venv` | Só aparecem as chaves **falsas** citadas nas revisões anteriores (`sk-fake-revisor`). As chaves reais só vêm do env (`src/config.py:24-25`) |
| 17 | Tabela do SLA no PDF | `pymupdf` renderizado (página 1, rodapé; página 2, topo) | O próprio PDF `Aditivo Fornecedores Xperiun.pdf` corta a tabela de créditos de SLA no fim da página 1: só a 1ª faixa ("Até 8 minutos e 38 segundos... 0%") existe. Isso é limitação da fonte, não do código (seção 9) |
| 18 | `$` no Markdown do Streamlit | `streamlit/elements/markdown.py:131`; `static/js/StreamlitMarkdown.*.js` (`singleDollarTextMath ??= !0`); chunks com `R$` | Docstring: "LaTeX expressions, by wrapping them in "$"". `$` simples ativa LaTeX por padrão. 6 chunks têm `R$` (#22, #23, #24, #36, #37, #42) e 2 das 4 respostas reais trazem `R$` (R5-01) |

**Resultado da rodada real (ação #13)**: K=3, `effort=medium`. Não consegui confirmar se o `max_tokens` em vigor era 1024 ou 16000 (ver seção 9).

| Tema PRD | Pergunta | Chunks recuperados | stop_reason | tokens entrada / saída (raciocínio) | Avaliação |
|---|---|---|---|---|---|
| Contratos e reajustes | Índice permitido, índice vedado e antecedência do aviso | #4, #2, #3 | end_turn | 3454 / 803 (79) | Chunks certos (IPCA, IGP-M vedado, 60 dias). **Texto da resposta não capturado**: um `tail` do meu script cortou essa parte da saída. Só tenho as métricas |
| Políticas de preço / comissão | Multiplicadores e bônus para 24 e 36 meses | #42, #41, #40 | end_turn | 3371 / 543 (72) | Correta: 1.15x; 1.25x + kicker R$ 2.500,00; "lock-in superior a 12 meses". Diz que não há kicker para 24 meses e aponta o que não veio nos trechos. Cita `[Política de Vendas Xperiun, p. 2]` |
| Fornecedores | SLA de uptime e crédito/penalidade | #8, #5, #6 | end_turn | 3458 / 747 (112) | 99,98% correto. Diz explicitamente que as faixas de crédito **não estão** nos trechos e manda consultar a Cláusula 2. **Não inventou** percentuais |
| Time de receita | Cota trimestral AE Sênior e AE Pleno | #36, #42, #24 | end_turn | 3388 / 659 (347) | R$ 450.000,00 e R$ 280.000,00 corretos. Aponta que "trimestral" aparece no trecho só junto ao Pleno, sem completar por conta própria |

## 4. Checklist da onda
| Critério (fonte) | Status | Evidência |
|---|---|---|
| API da Anthropic com Opus 5.5, `claude-opus-5-5`, via env (SPEC onda 5) | OK | `src/config.py:43`; `src/generator.py:60-61`; ação #5; rodada real: `model=claude-opus-5-5` nas 4 respostas |
| Envia system prompt + pergunta + K chunks (SPEC onda 5) | OK | `src/generator.py:36-43`, `:64-65`; ação #5 (3 trechos; com K=5, 5 trechos, ação #11) |
| System prompt manda responder só com os chunks e dizer quando não está nos documentos (REVISOR / AGENTS "NUNCA INVENTE") | OK | `src/generator.py:14-16` ("Use SOMENTE...", "Nunca invente... diga isso claramente"), `:18` (citação), `:23` (contexto NÃO é fonte). Rodada real: SLA e cota com ressalvas explícitas, sem dado inventado |
| `contexto/` só no system prompt, fora do RAG (decisão aprovada) | OK | `src/generator.py:30-33`; ação #6; `ingest.load_documents` lê só `docs/*.pdf` (`src/config.py:50-52`) |
| PRD: primeiro os K chunks, depois a resposta | OK | `app.py:363-374`; ação #7. No histórico os chunks ficam num expander fechado antes da resposta (`app.py:345`); ver Dúvidas |
| Erro de API (chave ausente, timeout) com mensagem clara | OK (com ressalva R5-02) | `app.py:329-330`, `:377-380`; `src/generator.py:74-92`; ações #9 e #11 |
| Responde aos 4 temas do PRD, 1 pergunta por tema | OK | Tabela da ação #13 (Q1 sem texto capturado, mas com chunks certos e `end_turn`) |
| Sem `temperature` e sem `thinking` explícito (entrega do Executor) | OK | `src/generator.py:60-69`; ação #5 |
| Fallback de recusa feito no servidor | OK (com ressalva R5-03) | `src/generator.py:67-68`; ações #3, #4 e #8 |
| `LLM_EFFORT` validado, `LLM_MAX_TOKENS` com default 16000 | OK | `src/config.py:44-47`; ação #12 |
| `.env.example` com todas as variáveis, sem valores reais | OK | `.env.example`: as 11 variáveis lidas em `src/config.py` estão presentes, com as chaves vazias |
| Stack LangChain (RAG) + Streamlit | OK | LangChain no splitter, nos embeddings e no Chroma (`src/ingest.py:7`, `src/vectorstore.py:3-5`). A geração usa o SDK oficial, como a SPEC pede ("usarei exatamente a API do claude"). Ver Dúvidas |
| A plataforma mostra a etapa atual (SPEC objetivo) | OK | Aba "5. Chat (Generation)" com chunks, system prompt (expander), resposta e tokens |
| Parâmetros da SPEC inalterados (350/40, K=3, modelos) | OK | `src/config.py:30-43`; ação #14 |
| Sem regressão das Ondas 1 a 4 | OK | Ação #14; ação #15 (health `ok`) |
| App sobe e há instrução de execução | OK | Ação #15; `README.md` ("Como rodar", tabela de abas e de variáveis, incluindo `LLM_EFFORT`) |
| Segredos fora do código / `.env` no `.gitignore` | OK | Ação #16; `.gitignore:1` |
| Nenhum dado inventado | OK | Respostas reais (ação #13). Os textos da UI vêm de `docs/`, `contexto/` ou da config |

## 5. Status dos achados anteriores (se re-revisão)
| ID | Status | Evidência |
|---|---|---|
| R3-04 (BAIXA, opcional) | PENDENTE (não aprovado pelo usuário) | `src/ingest.py` não muda desde 2026-11-02 02:19 (`strip_footer` em `src/ingest.py:15-22` igual ao revisado). O usuário só disse "execute a onda final" |
| R4-01 (BAIXA, opcional) | PENDENTE (não aprovado pelo usuário) | `src/retriever.py:11` continua com `similarity_search_with_relevance_scores`. A aba 5 reaproveita essa busca (`app.py:360`), então o aviso pode aparecer também ali |
| R4-02 (SUGESTÃO) | PENDENTE (não aprovado pelo usuário) | `show_retrieved` (`app.py:264-273`) continua sem o botão |
| Handoff da Onda 4 (reaproveitar `search`/`show_retrieved`, modelo e max_tokens do env, tratar erro como em `show_store_error`) | ATENDIDO | `app.py:360`, `:366`, `:328`; `src/generator.py:61-62` |

## 6. Achados (o que precisa mudar)
### [R5-01] `$` de "R$" na resposta é interpretado como fórmula LaTeX pelo Streamlit - MÉDIA
- **Onde:** `app.py:372` (`st.write_stream`, que usa `st.markdown`) e `app.py:350` (`st.markdown(item["answer"])` no histórico)
- **Problema:** o Streamlit renderiza como LaTeX o que estiver entre dois `$` (`streamlit/elements/markdown.py:131`: "LaTeX expressions, by wrapping them in "$""). No frontend, `singleDollarTextMath` vem ligado por padrão (ação #18). Os documentos usam `R$` (6 chunks), e o system prompt pede "valores e prazos exatamente como aparecem nos trechos" (`src/generator.py:20`). Se uma linha da resposta tiver dois valores, por exemplo "R$ 450.000,00 (Sênior) e R$ 280.000,00 (Pleno)", o trecho entre os dois `$` vira fórmula: os `$` somem e o texto aparece em fonte matemática, sem espaços. Nas 4 respostas reais isso não aconteceu porque os valores ficaram em itens de lista separados (ação #13). A renderização no navegador está NÃO VERIFICADA visualmente (seção 9).
- **Regra violada:** PRD/SPEC (a resposta precisa mostrar o valor do documento corretamente) e o próprio system prompt (valores "exatamente como aparecem").
- **Ação para o Executor:** escapar `$` antes de renderizar, tanto no streaming quanto no histórico. Exemplo: um helper `def _md_safe(t): return t.replace("$", r"\$")`; no streaming, `st.write_stream(_md_safe(t) for t in generator.stream_answer(...))`; no histórico, `st.markdown(_md_safe(item["answer"]))`. Guardar o texto **cru** em `item["answer"]` para não escapar duas vezes. Não mudar o prompt.
- **Critério de aceite:** com um stream falso que devolve `"Cotas: R$ 450.000,00 e R$ 280.000,00."`, o AppTest mostra o markdown com `\$` na mensagem ativa e no histórico. Num teste visual no navegador (porta diferente da 8501), aparece "R$ 450.000,00 e R$ 280.000,00" literal.

### [R5-02] Erros 400/500/529 e erro no meio do stream mostram mensagem bruta, e o texto parcial some do histórico - BAIXA
- **Onde:** `src/generator.py:84-91`; `app.py:371-378`
- **Problema:** (a) um erro SSE no meio do stream (ex.: `overloaded_error`) aparece como `Erro da API da Anthropic (200): {'type': 'error', 'error': {...}}` (ação #9), com status 200 e dicionário cru. (b) 500 e 529 aparecem como `Error code: 500 - {'type': ...}`. O SDK tem `anthropic.OverloadedError` e `anthropic.InternalServerError` (`dir(anthropic)`), mas eles caem no ramo genérico. (c) No erro no meio do stream, o texto parcial aparece na hora, mas depois de um rerun o histórico mostra só o erro (`item["answer"]` fica vazio porque `st.write_stream` lança a exceção antes de retornar). O checklist pede "mensagem clara na UI".
- **Regra violada:** REVISOR, Onda 5: "Tratamento de erro de API (chave ausente, timeout) com mensagem clara na UI". Os casos pedidos (chave ausente, timeout) estão OK. Isto é refinamento, por isso BAIXA.
- **Ação para o Executor:** em `describe_api_error`, antes de `APIStatusError`, tratar `anthropic.OverloadedError` / `InternalServerError` ("A API da Anthropic está sobrecarregada/instável. Tente novamente em instantes."). Para `APIStatusError` com corpo `{"type": "error", "error": {"type": "overloaded_error"...}}`, usar `exc.body["error"]["type"]` para escolher a mesma mensagem amigável. Opcional: acumular os pedaços do stream num buffer no `app.py` e guardar a parte parcial no histórico junto com o erro.
- **Critério de aceite:** com o mock da ação #9, os cenários 529 e "erro SSE overloaded" mostram uma mensagem em português sem `{'type': ...}`, e os demais cenários continuam iguais. 0 exceções.

### [R5-03] Fallback no meio da resposta junta o texto do modelo que recusou com o do fallback - BAIXA
- **Onde:** `src/generator.py:70` (`yield from stream.text_stream`); `app.py:313-314`
- **Problema:** `text_stream` entrega o texto de todos os blocos de texto. Num fallback no meio da geração, a UI mostra a parte do modelo que recusou e logo em seguida, sem separação, a resposta do fallback. Isso foi reproduzido com SSE simulado (ação #8): "PARCIAL-DO-MODELO-QUE-RECUSOU RESPOSTA-DO-FALLBACK". Além disso, o app detecta o fallback comparando `message.model != config.LLM_MODEL`. A documentação do SDK diz que o sinal oficial é a entrada `fallback_message` em `usage.iterations` (`beta_fallback_message_iteration_usage.py:15-19`, ação #4). Recusa é rara nos temas desta PoC, por isso BAIXA. O comportamento da API real está NÃO VERIFICADO (seção 9).
- **Regra violada:** nenhuma regra explícita. É qualidade da resposta mostrada (PRD: resposta confiável depois dos chunks).
- **Ação para o Executor:** em `stream_answer`, iterar os eventos (`for event in stream`). Num `content_block_start` com `content_block.type == "fallback"`, emitir um separador (ex.: `"\n\n---\n*Resposta do modelo de fallback:*\n\n"`) ou descartar o texto anterior. Detectar o fallback por `any(getattr(i, "type", None) == "fallback_message" for i in (message.usage.iterations or []))`, mantendo o `message.model` só para exibir o nome.
- **Critério de aceite:** com o SSE simulado da ação #8, a resposta mostra as duas partes separadas (ou só a do fallback) e a legenda de fallback aparece. Com SSE sem fallback, nada muda.

### [R5-04] Pergunta só com espaços faz busca e chamada paga ao Claude - BAIXA
- **Onde:** `app.py:353-354`
- **Problema:** `"   "` passa pelo `if question:`, gera uma busca e **1 chamada ao Claude** (ação #11). É custo sem utilidade.
- **Regra violada:** nenhuma regra explícita. É limpeza.
- **Ação para o Executor:** `question = (st.chat_input(...) or "").strip()` antes do `if`. Opcional: fazer o mesmo na aba 4 (`app.py:291`).
- **Critério de aceite:** com mock, `"   "` gera 0 buscas e 0 chamadas ao Claude, sem item novo no histórico.

### [R5-05] `LLM_MAX_TOKENS` do `.env` do usuário: 1024 era arriscado com o raciocínio sempre ligado; hoje está em 16000 - BAIXA (ação do usuário, não do Executor)
- **Onde:** `.env` do usuário (linha 21). O código e o `.env.example` estão corretos (`src/config.py:44`, default 16000).
- **Problema:** no Opus 5.5 o raciocínio adaptativo vem ligado por padrão, e os tokens de raciocínio contam dentro de `max_tokens` (`usage.output_tokens_details.thinking_tokens` "Always ≤ output_tokens", `types/beta/beta_output_tokens_details.py`). Na rodada real, com `effort=medium` e K=3, a saída foi de **543 a 803 tokens**, e só o raciocínio chegou a **347 tokens** numa pergunta simples (ação #13). Com 1024, a resposta mais longa usaria **78% do limite**. Perguntas que comparam várias cláusulas, K maior ou `effort` alto passariam de 1024 e seriam cortadas (o app avisa: ação #8). Quando a revisão começou, o `.env` tinha `LLM_MAX_TOKENS=1024` (ação #2). Às 09:47:15 o arquivo foi alterado, não pelo revisor, e hoje tem `16000`. O risco está mitigado se essa alteração foi intencional.
- **Regra violada:** nenhuma regra do código. É risco de resposta incompleta no ambiente real do usuário (PRD: responder às perguntas do time).
- **Ação para o usuário:** confirmar que a troca para `LLM_MAX_TOKENS=16000` foi intencional e manter um valor >= 16000. Opcional: incluir `LLM_EFFORT=medium` no `.env` (hoje ausente; o default do código já é `medium`). **Ação para o Executor:** nenhuma. Não editar o `.env`.
- **Critério de aceite:** `config.LLM_MAX_TOKENS >= 16000` com o `.env` do usuário, e a sidebar mostrando "max 16000 tokens" (já é o caso na ação #14).

### [R5-06] Mostrar os tokens de raciocínio na legenda - SUGESTÃO
- **Onde:** `app.py:315-318`
- **Problema:** isto não é falha. A legenda mostra só o total de saída. O SDK expõe `message.usage.output_tokens_details.thinking_tokens` (ação #13: 72 a 347 tokens), e isso ajudaria a calibrar `LLM_MAX_TOKENS` e `LLM_EFFORT`.
- **Regra violada:** nenhuma (fora da SPEC).
- **Ação para o Executor:** só com aprovação do usuário. Acrescentar "(raciocínio N)" quando `output_tokens_details` existir.
- **Critério de aceite:** a legenda mostra o número de tokens de raciocínio, e não quebra quando o campo vem `None`.

## 7. Pontos positivos
- A requisição sai exatamente como o Executor descreveu e foi conferida byte a byte com transporte simulado (ação #5): modelo, `max_tokens` e `effort` vindos do env, beta e `fallbacks="default"`, sem `temperature`/`thinking`, e system prompt idêntico ao exibido no expander.
- O system prompt é bem desenhado para "NUNCA INVENTE": proíbe completar com conhecimento próprio, exige citação `[documento, p. X]` e declara o `contexto/` explicitamente como não-fonte. Na prática, o modelo recusou completar as faixas de SLA ausentes e a periodicidade da cota não escrita (ação #13).
- A ordem do PRD está garantida pelo código: os chunks são renderizados antes de abrir o stream (`app.py:363-374`). Em qualquer erro da Anthropic, os chunks continuam visíveis para conferência (ação #9).
- `describe_api_error` testa do mais específico para o mais genérico, na ordem certa (`APITimeoutError` é subclasse de `APIConnectionError` e vem antes). Os casos de chave inválida, modelo inexistente, limite e timeout têm mensagem clara.
- A Onda 5 não gerou nova indexação nem regressão: 1 indexação para todas as abas, 49 chunks, 350/40 e o histórico da aba 4 isolado do da aba 5 (ação #14).
- Dependências mais enxutas: `langchain-anthropic` foi removido porque não era usado, e `anthropic==2.3.0` está fixado direto no `requirements.txt`.

## 8. Dúvidas para o usuário (bloqueiam decisão, não inventar)
- **Histórico com os chunks recolhidos:** na pergunta atual, os K chunks aparecem abertos antes da resposta. Nas perguntas anteriores, eles ficam num expander **fechado** (ainda antes da resposta) (`app.py:345`). O PRD diz "precisa trazer sempre os K chunks... e so depois trazer a resposta". Isso atende ao PRD? Opções: (1) manter como está (menos poluição visual); (2) deixar o expander aberto (`expanded=True`); (3) mostrar os chunks sempre abertos, como na aba 4.
- **Geração fora do LangChain:** a SPEC diz "Langchain para o RAG" e, na Onda 5, "usarei exatamente a API do claude". O Executor usou o SDK oficial `anthropic` direto na geração e removeu `langchain-anthropic`. Considerei OK, porque o LangChain continua no chunking, nos embeddings e no Chroma. Confirma que está de acordo?
- **`LLM_MAX_TOKENS` do `.env`:** a mudança de 1024 para 16000 às 09:47:15 foi sua (R5-05)?
- **Pendentes opcionais:** R3-04 (BAIXA), R4-01 (BAIXA), R4-02 (SUGESTÃO) e R5-06 (SUGESTÃO). Implementar algum? Nenhum bloqueia a entrega.

## 9. Informações não encontradas / não verificadas
- **`max_tokens` em vigor na rodada real (ação #13):** NÃO VERIFICADO. O `.env` mudou de 1024 para 16000 às 09:47:15, e a linha que imprimia a config se perdeu no `tail` do meu script. As 4 respostas terminaram em `end_turn` com no máximo 803 tokens, então o resultado vale para os dois valores.
- **Texto da resposta real da pergunta de contratos/reajustes:** NÃO CAPTURADO (corte de saída no meu script). Chunks, `stop_reason` e tokens foram registrados. Não repeti a chamada para não passar do orçamento de 4 chamadas ao Claude.
- **Renderização do `$` como LaTeX no navegador (R5-01):** NÃO VERIFICADA visualmente. A evidência vem do código e da documentação do Streamlit (ação #18). Nenhuma das 4 respostas reais tinha dois `R$` na mesma linha.
- **Fallback e recusa reais (R5-03):** NÃO VERIFICADOS com a API real (não há como provocar uma recusa legítima dentro do escopo e do orçamento). Testados só com SSE simulado no formato dos tipos do SDK 2.3.0.
- **Penalidades de SLA:** a tabela de créditos do `Aditivo Fornecedores Xperiun.pdf` vem cortada **no próprio PDF** (ação #17). Só a faixa "Até 8 minutos e 38 segundos → 0%" existe na fonte. Nenhum RAG consegue responder às demais faixas sem um documento completo. Se a área de compras precisar disso, o PDF precisa ser corrigido na origem.
- Timeout real (sem mock) e comportamento com `max_retries` padrão do SDK: NÃO VERIFICADOS com rede. O caminho foi coberto com `ReadTimeout` simulado e `max_retries=0` (ação #9).

## 10. Handoff para o Agente Executor
Ordem de execução recomendada (BLOQUEANTE > ALTA > MÉDIA > BAIXA):
- [ ] R5-01 - (MÉDIA) escapar `$` antes de `st.write_stream`/`st.markdown` da resposta (stream e histórico), guardando o texto cru
- [ ] R5-02 - (BAIXA) mensagens amigáveis para `OverloadedError`/`InternalServerError` e erro SSE no meio do stream; opcional: guardar o texto parcial no histórico
- [ ] R5-03 - (BAIXA) separar ou descartar o texto anterior ao bloco `fallback`; detectar fallback por `usage.iterations`
- [ ] R5-04 - (BAIXA) ignorar pergunta vazia ou só com espaços (`.strip()`)
- [ ] R5-05 - (usuário, não o Executor) manter `LLM_MAX_TOKENS >= 16000` no `.env`
- [ ] R4-01 - (BAIXA, opcional, **aguarda aprovação do usuário**) evitar o `UserWarning` de score negativo em `search()`
- [ ] R3-04 - (BAIXA, opcional, **aguarda aprovação do usuário**) `strip_footer`: páginas vazias e documento de 1 página
- [ ] R4-02 / R5-06 - (SUGESTÃO, só com aprovação) botão "ver nas abas 2/3"; tokens de raciocínio na legenda

Restrições para o Executor:
- Não alterar parâmetros definidos na SPEC (chunk 350/40, K=3, modelos) sem aprovação do usuário.
- Não implementar itens marcados como SUGESTÃO sem aprovação do usuário.
- Não editar o `.env` do usuário (R5-05 é ação do usuário).
- Para validar, usar mock para os caminhos de erro e no máximo poucas chamadas reais. Não usar a porta 8501.
- Ao terminar, solicitar nova revisão: `/revisar-onda 5`.
