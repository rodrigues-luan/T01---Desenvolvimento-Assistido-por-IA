# Revisão - Onda 4 - Iteração 1
**Data:** 2026-11-02 | **Revisor:** Tech Lead (agente revisor) | **Veredito:** APROVADO

## 1. Resumo executivo
A Onda 4 entregou a busca semântica (Augmented) sem LLM. `src/retriever.py` faz `search()` com `similarity_search_with_relevance_scores` e usa `config.TOP_K` como K padrão. A coleção do Chroma em memória agora é criada com `hnsw:space = cosine`, e o score mostrado é a similaridade de cosseno. Isso foi conferido no código do LangChain e por execução: com embedding falso, a ordem e os scores bateram exatamente com o cálculo manual, inclusive com K=49. A aba "4. Busca (Augmented)" tem `st.chat_input`, K ajustável (padrão 3), histórico com a busca mais recente no topo (posição, similaridade, documento, página, chunk id e texto) e o botão "Limpar histórico". Na rodada real, a pergunta sobre congelamento de preço trouxe o chunk certo em 1º lugar (similaridade 0,6038). Não há achado bloqueante, alto ou médio. Ficam um item BAIXA novo (aviso do LangChain quando o score é negativo) e o R3-04 (BAIXA), que segue pendente e opcional.

## 2. Escopo revisado
- Onda/objetivo segundo a SPEC: "4 - ... eu digito uma pergunta no chat, e ele me trará os 3 chunks mais similares…ainda não usarei IA, apenas a busca semântica. Para o banco de dados, podemos usar o Chroma sem a necessidade de instalar um banco vetorial, que ele funcione apenas enquanto o meu projeto estiver rodando" (`SPEC.md`, Desenvolvimento, item 4). PRD: "precisa trazer sempre os K chunks para conferirmos se a busca semântica funcionou".
- Onda e iteração: informadas no pedido (Onda 4, iteração 1). Batem com `revisoes/`: não existia nenhuma revisão da Onda 4, e `onda-3-revisao-2.md` liberou a Onda 4.
- Decisões já aprovadas pelo usuário (repassadas no pedido): K=3 configurável pelo env e pela tela; Chroma em memória com cache do Streamlit; `contexto/` fora do RAG; venv; sem gestão de acesso; overlap opção (a); `git init` só no final.
- R3-04: o usuário respondeu apenas "siga para onda 4", sem aprovar o R3-04. Por isso ele continua pendente e opcional, com a severidade original (BAIXA).
- Arquivos analisados: `src/retriever.py` (novo), `src/vectorstore.py` (alterado), `app.py` (aba 4), `src/config.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`. Do `.env` foram lidos só os nomes das chaves, com os valores mascarados.
- Revisão anterior considerada: `revisoes/onda-3-revisao-2.md`.

## 3. O que o revisor fez (rastreabilidade)
| # | Ação | Comando/arquivo | Resultado |
|---|---|---|---|
| 1 | Versão do Python do venv | `.venv/Scripts/python --version` | 3.13.1, OK (>= 3.11) |
| 2 | Consistência das dependências | `pip check` | "No broken requirements found." `requirements.txt` sem mudança; nenhum pacote novo foi necessário |
| 3 | `.env` com valores mascarados | `sed 's/=.*/=<redacted>/' .env` | Mesmas chaves do `.env.example`; `TOP_K` já declarado; nenhuma variável nova no código |
| 4 | Como o LangChain transforma distância em score | leitura de `langchain_chroma/vectorstores.py:904-943` e `langchain_core/vectorstores/base.py:391-393` | `_select_relevance_score_fn` lê `collection.configuration["hnsw"]["space"]`; com `cosine`, o score é `1 - distância`, ou seja, a similaridade de cosseno |
| 5 | Configuração real da coleção | script com embedding falso (hash do texto, 64 dimensões, **sem normalizar**) | `configuration.hnsw.space = 'cosine'`, `metadata = {'hnsw:space': 'cosine'}`, função escolhida `_cosine_relevance_score_fn`, nenhum warning na criação. K padrão de `search` = `(3,)` |
| 6 | Score e ordem iguais ao cosseno calculado à parte | mesmo script, 3 consultas (uma delas é o texto exato do chunk #10) | Top 3 (id, score com 6 casas) **iguais** ao cálculo manual nas 3 consultas; o chunk #10 consultado com o próprio texto teve score 1.0; com K=49, a ordem completa dos 49 bateu com a ordem por força bruta |
| 7 | Score negativo | mesmo script, K=49 | Score mínimo de -0,36 com vetores falsos; o LangChain emite `UserWarning: Relevance scores must be between 0 and 1, got [...]` (ver R4-01) |
| 8 | Aba 4 com embedding falso | AppTest (`from_file` com caminho absoluto), chave falsa `sk-fake-revisor` | 0 exceções; 6 abas; legenda da aba 4 cita o modelo; `number_input` "K (chunks)" com valor 3, mín 1, máx 49; 1 `chat_input`; botão "Limpar histórico" |
| 9 | Fluxo da busca | mesmo AppTest: pergunta 1 com K=3, troca para K=5, pergunta 2 | 4 `chat_message`. No topo vem a pergunta 2 ("Top 5 chunks mais similares:", 5 textos, 15 métricas Posição/Similaridade/Origem) e abaixo a pergunta 1 ("Top 3", 3 textos). Origem no formato "Contrato de Trabalho Xperiun p.1 (chunk #18)". Os scores exibidos batem com a ação #6 |
| 10 | Chamadas repetidas e persistência | contadores em `embed_documents`/`embed_query` | Indexação `[49]`, só 1 vez em todo o teste; 1 `embed_query` por pergunta; rerun simples e clique em "Próximo" na aba 2 não geram consulta nova e o histórico continua com 4 mensagens |
| 11 | Limpar histórico | clique em `busca_clear` | 0 mensagens, 0 exceções. Depois, a mesma pergunta 2 vezes gera 2 entradas e 2 consultas, o que é esperado |
| 12 | Sem chave OpenAI | AppTest com `OPENAI_API_KEY=` | Aba 4 mostra `st.error` "OPENAI_API_KEY ausente..." sem botão de tentar de novo, sem `chat_input` e sem `number_input`; 0 chamadas; 0 exceções |
| 13 | Falha na indexação | falso que lança erro em `embed_documents` | Aba 4 mostra "Falha ao gerar embeddings: falha simulada" e o botão "Tentar novamente" (`retry_busca`); 2 reruns não fazem nova chamada (`[49]`); o clique faz `[49, 49]`; 0 exceções |
| 14 | Falha na consulta | falso que lança erro em `embed_query` | `st.error` "Falha na busca: query falhou simulada"; nada entra no histórico; o erro some no próximo rerun; 0 exceções |
| 15 | **Rodada real** (orçamento: 1 indexação + até 6 consultas) | AppTest com a chave do `.env` e wrappers de captura | 0 exceções; indexação: **1 chamada** com 49 textos; **6 consultas**, modelo `text-embedding-3-small` em todas (mesmo modelo na indexação e na consulta); histórico com as 6 perguntas, a mais recente no topo |
| 16 | Resultado real, pergunta "Qual o período de congelamento de preço dos fornecedores?" | saída da ação #15 | #1 = 0,6038, Aditivo p.1, chunk #1 ("Período de Congelamento: O valor de face mensal... fixo... 12 (doze) meses"), que é o chunk da resposta; #2 = 0,5069, chunk #3 (IPCA); #3 = 0,4941, chunk #5 (notificação do reajuste) |
| 17 | Resultado real das outras 5 perguntas | saída da ação #15 | **Perdido** por um erro no script do revisor: `OpenAIEmbeddings.embed_query` chama `embed_documents([text])` (`langchain_openai/embeddings/base.py:807`), e isso sobrescreveu a matriz capturada da indexação. O script quebrou depois de imprimir a 1ª pergunta. Não refiz a rodada para não passar do orçamento. Ver seção 9 |
| 18 | Subida real do servidor | `streamlit run app.py --server.port 8597 --server.headless true` + `/_stcore/health` | `ok`; processo (PID 26920) encerrado; porta 8597 livre. A porta 8501 do usuário (PID 11368) **não foi tocada** e continua escutando. Nenhuma sessão de navegador foi aberta, então não houve chamada paga |
| 19 | Sem LLM / segredos | `app.py`, `src/retriever.py` | Nenhum import nem chamada à Anthropic; a aba 5 continua placeholder (`app.py:305-306`). As chaves só vêm do env (`src/config.py:24-25`) |

## 4. Checklist da onda
| Critério (fonte) | Status | Evidência |
|---|---|---|
| Pergunta no chat retorna os 3 chunks mais similares, K=3 (SPEC onda 4) | OK | `st.chat_input` em `app.py:291`; K padrão `min(config.TOP_K, n)` em `app.py:286`; `TOP_K` padrão 3 em `src/config.py:39`; ações #8, #9 e #15 |
| K configurável pelo env e pela tela (decisão do usuário) | OK | `src/config.py:39-41`, `.env.example` (`TOP_K=3`), `app.py:286` (mín 1, máx = total de chunks); ação #9 (K=5 devolve 5) |
| Sem LLM nesta onda (SPEC onda 4) | OK | `src/retriever.py:11` só chama o Chroma; ação #19 |
| Chroma em memória, sem servidor e sem persistência (SPEC onda 4) | OK | `src/vectorstore.py:17-26`, sem `persist_directory`; `chroma/` está no `.gitignore` |
| Mesmo modelo de embedding na indexação e na consulta | OK | A coleção guarda a função de embedding de `get_embeddings()` (`src/vectorstore.py:11-14`, `:22`); ação #15: só `text-embedding-3-small` nas 49 + 6 chamadas |
| Exibe os chunks retornados: conteúdo, origem e score (REVISOR onda 4) | OK | `show_retrieved` em `app.py:264-273`: posição, similaridade com 4 casas, documento, página, chunk id e texto; ação #9 |
| Score é a similaridade de cosseno (entrega do Executor) | OK | `src/vectorstore.py:24`; ações #4, #5 e #6 |
| Índice não é recriado a cada interação (cache do Streamlit) | OK | `@st.cache_resource` em `app.py:27-29`; ações #10 e #15 (1 indexação para 6 perguntas) |
| Histórico, mais recente no topo, e botão limpar (entrega do Executor) | OK | `app.py:287-303`; ações #9 e #11 |
| PRD: "trazer sempre os K chunks para conferirmos" | OK | Cada resposta do histórico mostra os K chunks com origem e score; ação #16 |
| Tratamento de erro (sem chave, falha na indexação, falha na consulta) | OK | `app.py:281-283` (reaproveita `get_store`/`show_store_error`), `app.py:293-296`; ações #12, #13 e #14 |
| A plataforma mostra a etapa atual (SPEC objetivo) | OK | Aba "4. Busca (Augmented)" funcional |
| Parâmetros da SPEC inalterados (350/40, K=3, modelos) | OK | `src/config.py:30-43`; ação #8 (49 chunks, mesmo total da Onda 3) |
| Dependências / `.env.example` / `.env` fora do versionamento | OK | Ações #2 e #3; `.gitignore:1` |
| App sobe sem erro | OK | Ações #8 e #18 |
| Sem regressão das Ondas 1 a 3 | OK | 6 abas renderizam com 0 exceções; total de 49 chunks; navegação da aba 2 continua funcionando (ação #10); `get_store()` também é chamado na aba 3 (`app.py:222`) e o cache faz com que ele seja reaproveitado (indexação `[49]`, ação #10) |
| Nenhum dado inventado | OK | A aba 4 só mostra chunks de `docs/`, scores do Chroma e valores da config |

## 5. Status dos achados anteriores (se re-revisão)
| ID | Status | Evidência |
|---|---|---|
| R3-04 (BAIXA, opcional) | PENDENTE (não aprovado pelo usuário) | `src/ingest.py` não mudou nesta onda (o Executor não declarou mudança e o total continua 49 chunks, ação #8). O usuário respondeu só "siga para onda 4", sem aprovar. A severidade continua BAIXA e opcional. Aguarda decisão do usuário |
| Sugestão opcional do handoff da Onda 3 (botão no resultado que leva ao chunk nas abas 2 e 3) | NÃO IMPLEMENTADO (era opcional) | `app.py:264-273` não tem esse botão. Não afeta o veredito. Fica registrado como R4-02 (SUGESTÃO) |

## 6. Achados (o que precisa mudar)
### [R4-01] LangChain emite UserWarning quando a similaridade de cosseno é negativa - BAIXA
- **Onde:** `src/retriever.py:11`
- **Problema:** `similarity_search_with_relevance_scores` espera scores entre 0 e 1. Quando algum cosseno é negativo, ele emite `UserWarning: Relevance scores must be between 0 and 1, got [...]` (`langchain_core/vectorstores/base.py:537-540`), e a mensagem traz a lista inteira de `Document`. Isso foi reproduzido com vetores falsos e K=49 (ação #7). O valor exibido continua correto. É só ruído no console/log, que pode crescer com K alto ou perguntas fora do assunto. Com embeddings reais e K=3 isso não apareceu na pergunta conferida (ação #16).
- **Regra violada:** nenhuma regra explícita da SPEC/PRD. Classifiquei como limpeza (BAIXA).
- **Ação para o Executor (opcional):** escolha uma das opções: (a) usar `store.similarity_search_with_score(query, k=k)` e converter para `1 - distância` (cosseno) dentro de `search()`, sem o aviso; ou (b) manter a chamada atual e silenciar só esse aviso com `warnings.catch_warnings()` dentro de `search()`. Não mudar K nem o modelo.
- **Critério de aceite:** com embedding falso e K=49 (como na ação #7), não aparece nenhum `UserWarning`; a ordem e os scores continuam iguais ao cosseno calculado manualmente.

### [R4-02] Botão "ver nas abas 2/3" em cada chunk retornado - SUGESTÃO
- **Onde:** `app.py:264-273`
- **Problema:** isto não é falha. Foi proposto como opcional no handoff da Onda 3: em cada resultado, um botão que coloque `st.session_state.idx = chunk_id`, para conferir o chunk (overlap, embedding) nas abas 2 e 3.
- **Regra violada:** nenhuma (fora da SPEC).
- **Ação para o Executor:** só implementar se o usuário aprovar. Usar `on_click` (como em `chunk_navigator`) e uma key única por item do histórico e posição.
- **Critério de aceite:** depois do clique, as abas 2 e 3 mostram o chunk com o mesmo id do resultado.

## 7. Pontos positivos
- `search()` é pequeno, tem K padrão vindo da config e documenta que a consulta usa o mesmo modelo da indexação. A escolha de `hnsw:space = cosine` faz o score exibido ter um significado claro, e isso foi conferido contra o cálculo manual, com igualdade em 6 casas (ação #6).
- A aba 4 reaproveita `get_store()`/`show_store_error()`: sem chave, com falha e com "Tentar novamente", o comportamento é o mesmo da aba 3, sem nova chamada paga a cada rerun (ações #12 e #13).
- Cada item do histórico guarda o próprio K. Mudar o K na tela não altera as buscas antigas (ação #9).
- Uma falha na consulta não quebra o app nem entra no histórico (ação #14).
- Na rodada real: 1 indexação para 6 perguntas (ação #15), e a pergunta conferida trouxe o chunk da resposta em 1º lugar (ação #16).

## 8. Dúvidas para o usuário (bloqueiam decisão, não inventar)
- **R3-04 (BAIXA, opcional):** quer que o Executor ajuste `strip_footer` para documentos de 1 página e com páginas vazias? Isso importa só quando entrar em `docs/` um PDF assim. Hoje os 3 PDFs não têm o problema. Opções: (1) corrigir agora; (2) deixar para depois; (3) descartar.
- **R4-01 (BAIXA, opcional) e R4-02 (SUGESTÃO):** implementar? Nenhum dos dois bloqueia a Onda 5.

## 9. Informações não encontradas / não verificadas
- **Resultados reais das perguntas "cota AE Sênior", "SLA de uptime", "benefícios", "índice de reajuste" e "capital da França" (pergunta fora do assunto):** NÃO VERIFICADO pelo revisor. As 6 consultas foram feitas e exibidas sem exceção (ação #15), mas a saída se perdeu por um erro no script do revisor (ação #17), e refazer passaria do orçamento de chamadas. A afirmação do Executor de que as 4 perguntas trouxeram o chunk relevante foi confirmada só para a 1ª (ação #16). Pelos textos dos chunks, os chunks esperados existem: cota AE Sênior no chunk #36, uptime 99,98% nos #5/#6, benefícios no #24 e IPCA/IGP-M nos #2 a #4. A ordenação foi provada correta de forma independente com embedding falso (ação #6).
- **Igualdade entre o score real e o cosseno manual com vetores da OpenAI:** NÃO VERIFICADO com vetores reais, pelo mesmo motivo. Foi verificado com vetores falsos não normalizados (ação #6), o que cobre a matemática do Chroma e do LangChain.
- Renderização visual no navegador (layout do histórico e do chat_input dentro da aba): NÃO VERIFICADO visualmente. Foi conferida pela árvore de elementos do AppTest (ações #8 e #9) e pelo health check (ação #18).
- Pergunta só com espaços no `chat_input`: NÃO VERIFICADO.

## 10. Handoff para o Agente Executor
Ordem de execução recomendada (BLOQUEANTE > ALTA > MÉDIA > BAIXA):
- [ ] Nenhuma correção obrigatória pendente na Onda 4. **A Onda 5 pode começar.**
- [ ] R4-01 - (BAIXA, opcional) evitar o `UserWarning` de score negativo em `search()`
- [ ] R3-04 - (BAIXA, opcional, **aguarda aprovação do usuário**) `strip_footer`: ignorar páginas vazias e tratar documento de 1 página
- [ ] R4-02 - (SUGESTÃO, só com aprovação) botão "ver nas abas 2/3" em cada chunk retornado

Para a Onda 5 (SPEC item 5; checklist do REVISOR.md):
- Reaproveitar `retriever.search(store, query, k)` e mostrar **primeiro** os K chunks (o mesmo `show_retrieved`) e **só depois** a resposta (PRD).
- Modelo `config.LLM_MODEL` (`claude-opus-5-5`) e `config.LLM_MAX_TOKENS`, vindos do env. O system prompt deve mandar responder somente com base nos chunks e dizer explicitamente quando a informação não está nos documentos.
- Tratar erro de API (chave ausente, timeout) com mensagem clara, no mesmo padrão de `show_store_error`.

Restrições para o Executor:
- Não alterar parâmetros definidos na SPEC (chunk 350/40, K=3, modelos) sem aprovação do usuário.
- Não implementar itens marcados como SUGESTÃO sem aprovação do usuário.
- Ao terminar, solicitar nova revisão: `/revisar-onda <N>`.
