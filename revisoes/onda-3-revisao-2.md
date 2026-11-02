# Revisão - Onda 3 - Iteração 2
**Data:** 2026-11-02 | **Revisor:** Tech Lead (agente revisor) | **Veredito:** APROVADO

## 1. Resumo executivo
A iteração 2 aplicou tudo o que o usuário decidiu nesta sessão. As abas agora são seis: "2. Explorar chunks" e "3. Embeddings" ficaram separadas e usam o mesmo índice de navegação. A aba 3 mostra o total de embeddings lido do Chroma (R3-01). A similaridade só é calculada com vizinhos do mesmo documento e mostra "outro doc" nas fronteiras (R3-02). A aba Setup lista `contexto/` com o aviso de que não entra no RAG (R1-04). O rodapé é removido antes do chunking (R2-04). Uma falha de embedding fica guardada na sessão e só é refeita pelo botão "Tentar novamente" (R2-05/R3-03). Tudo foi conferido por execução: AppTest sem chave, com embedding falso, com embedding que falha e numa única rodada real (1 chamada, 49 textos). O chunking continua na opção (a), já confirmada: 49 chunks, máximo de 350, overlap de 28 a 39 (média 35,98), nenhum par sem overlap e nenhum corte no meio de palavra. Não há achado bloqueante, alto ou médio. Fica só um ajuste BAIXA, opcional: a remoção de rodapé não cobre documentos de uma página.

## 2. Escopo revisado
- Onda/objetivo segundo a SPEC: "3 - Quero visualizar os chunks lá no streamlit, tendo uma visão de quantos chunks geramos e conseguir selecionar esses chunks" (`SPEC.md`, Desenvolvimento, item 3).
- Onda e iteração: informadas no pedido (Onda 3, iteração 2). Batem com `revisoes/`: já existia `onda-3-revisao-1.md`.
- Decisões do usuário nesta sessão (respostas literais repassadas no pedido): corrigir R3-01 e R3-02 ("sim"); "separar as abas"; overlap opção (a) ("sim", dúvida encerrada); R1-04, R2-04 e R2-05/R3-03 ("corrija tudo", agora são escopo aprovado); gráfico 2D ("não precisa", fora do escopo).
- Arquivos analisados: `app.py` (alterado), `src/ingest.py` (alterado: `strip_footer`, `PAGE_NUMBER_RE`, separadores `[r"\s", ""]` como regex), `src/config.py`, `src/vectorstore.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `contexto/contexto.txt` (só o início). Do `.env` foram lidos só os nomes das chaves, com os valores mascarados.
- Revisão anterior considerada: `revisoes/onda-3-revisao-1.md` e, para as sugestões, `onda-2-revisao-1.md` (R2-04, R2-05) e `onda-1-revisao-1.md` (R1-04).

## 3. O que o revisor fez (rastreabilidade)
| # | Ação | Comando/arquivo | Resultado |
|---|---|---|---|
| 1 | Versão do Python do venv | `.venv/Scripts/python --version` | 3.13.1, OK (>= 3.11) |
| 2 | Consistência das dependências | `pip check` / `pip install -r requirements.txt --dry-run` | "No broken requirements found."; nenhum "Would install" nem erro (`requirements.txt` sem mudança) |
| 3 | `.env` com valores mascarados | `sed 's/=.*/=<mascarado>/' .env` | Mesmas chaves do `.env.example`, nenhuma variável nova no código |
| 4 | Rodapé bruto dos PDFs | script PyMuPDF: primeiras e últimas linhas de cada página | As 6 páginas terminam em "<linha fixa do documento>" + "Página X de Y" (Aditivo: "Gestão de Contratos de Fornecedores - Xperiun"; Contrato: "Xperiun Tecnologia S.A. - Contrato de Trabalho"; Política: "Xperiun Tecnologia S.A. - Confidencial") |
| 5 | Chunking depois da mudança (Onda 2) | script: `load_documents` + `split_documents` + `overlaps` | 6 páginas, 0 puladas; **49 chunks**; máx. 350, mín. 51; 43 pares na mesma página; **0 sem overlap**; mín. 28, máx. 39, média 35,98 |
| 6 | Rodapé nos chunks (critério R2-04) | busca nos 49 chunks | 0 chunks com `Página \d+ de \d+`; 0 com cada uma das 3 linhas fixas |
| 7 | Integridade dos chunks | script do revisor | `page_content` igual a `página[start_index:start_index+len]` em 49/49; `pair_overlap` igual à medição independente (maior sufixo/prefixo comum) em 43/43; `chunk_id == índice` em 49/49; **0 cortes no meio de palavra** nas bordas dos chunks; 0 chunks com espaço nas bordas |
| 8 | Casos de borda do `strip_footer` | entradas sintéticas | 2+ páginas com rodapé igual: remove as 2 linhas; últimas linhas diferentes: só remove "Página X de Y"; **documento de 1 página: a linha fixa fica**; página vazia no meio: a linha fixa fica em todas; última linha igual sem "Página X de Y": é removida. Ver R3-04 |
| 9 | App sem chave OpenAI | AppTest com `OPENAI_API_KEY=` | 0 exceções; 6 abas: `0. Setup`, `1. Chunks (Retriever)`, `2. Explorar chunks`, `3. Embeddings`, `4. Busca (Augmented)`, `5. Chat (Generation)`; Setup com o subheader "Contexto institucional em contexto/", a legenda "Não é indexado no RAG..." e o expander "contexto.txt (4.9 KB)"; aba 1: 3 docs / 6 páginas / 49 chunks / maior 350 / overlap médio 36.0, com legenda sobre a remoção de rodapés; aba 3: `st.error` "OPENAI_API_KEY ausente..." **sem** o botão "Tentar novamente" (correto, porque sem chave não adianta tentar) |
| 10 | Destaque do overlap (aba 2) | AppTest, **todos os 49 chunks** | 0 divergências: o texto sem tags é igual ao `page_content`, o trecho azul é sufixo do anterior e o laranja é prefixo do próximo, e a métrica de overlap é igual ao tamanho do destaque |
| 11 | Embedding falso (hash do texto), Chroma real | AppTest com `OpenAIEmbeddings.embed_documents` substituído e chave falsa `sk-fake-revisor` | 0 exceções; aba 3: **"Embeddings no Chroma" = 49**, Modelo `text-embedding-3-small`, Dimensão 1536; norma e similaridades **iguais ao cálculo independente** (4 casas) nos índices 0, 1, 7, 8, 15, 16, 17, 24, 25, 33, 34 e 48; `st.code` igual a `vec[:10]` em todos; 1 `vega_lite_chart` |
| 12 | Fronteiras de documento (R3-02) | mesmo AppTest | #15 próximo, #16 anterior, #33 próximo e #34 anterior = **"outro doc"**; #1 e #17 mostram valor numérico; #0 anterior e #48 próximo = "-" |
| 13 | Índice compartilhado entre as abas 2 e 3 | AppTest: Próximo (aba 2) x2, Anterior (aba 3) x3, Próximo (aba 2) | `(aba2, aba3, idx)`: 1,1,1 → 2,2,2 → 1,1,1 → 0,0,0 → 48,48,48 → 0,0,0; trocar o seletor da aba 3 também muda a aba 2 (ação #11, coluna "explorar sel"); 0 exceções |
| 14 | Cache no sucesso | contador em `embed_documents` (falso) | `[49]`: 1 chamada em mais de 20 reruns e cliques |
| 15 | Falha da API (R2-05/R3-03) | falso que lança erro | Carga inicial `[49]`; depois de 3 reruns, `[49]`; depois de 2 cliques em Próximo, `[49]`; clique em "Tentar novamente": `[49, 49]`; mais 2 reruns, `[49, 49]`. Aba 3 mostra "Falha ao gerar embeddings: ..." e o botão; abas 1 e 2 seguem funcionando; 0 exceções |
| 16 | **Única rodada real de embeddings** | AppTest com a chave do `.env` e contador | 0 exceções; **1 chamada** (49 textos, modelo `text-embedding-3-small`); "Embeddings no Chroma" = 49; Dimensão 1536; normas de 0,9997 a 1,0003; similaridade entre vizinhos de 0,31 a 0,67; "outro doc" em #15, #16, #33 e #34 |
| 17 | Subida real do servidor | `streamlit run app.py --server.port 8598 --server.headless true` + `/_stcore/health` | `ok`; processo (PID 25832) encerrado; porta 8598 livre e nenhum processo python/streamlit restante. A porta 8501 não foi usada |
| 18 | Segredos e HTML | código revisado | Chaves só lidas de env (`src/config.py:24-25`); a UI só mostra configurada/ausente (`app.py:98-99`); texto escapado com `html.escape` antes do `unsafe_allow_html` (`app.py:205-212`) |

## 4. Checklist da onda
| Critério (fonte) | Status | Evidência |
|---|---|---|
| Streamlit mostra o total de chunks gerados (SPEC onda 3) | OK | Aba 1: métrica "Chunks gerados" (`app.py:141`); abas 2 e 3: "Selecione um chunk (49 no total)" (`app.py:75`); ação #9 |
| Usuário seleciona um chunk e vê o conteúdo (SPEC onda 3) | OK | `app.py:57-84` (seletor + anterior/próximo), `app.py:205-212` (texto); ações #10 e #13 |
| Mostra origem/metadados do chunk (REVISOR onda 3, recomendado) | OK | `app.py:194-199` e `app.py:218-219`; aba 3: métrica "Chunk" com documento e página (`app.py:251`) |
| Decisão do usuário: abas separadas | OK | `app.py:101-110`: "2. Explorar chunks" e "3. Embeddings"; ação #9 |
| R3-01: total de embeddings na aba de embeddings | OK | `app.py:226-228`, lido do Chroma em cache; ações #11 e #16 (49) |
| R3-02: similaridade não atravessa documento sem aviso | OK | `app.py:241-247`, legenda em `app.py:255`; ações #12 e #16 |
| R1-04: `contexto/` na aba Setup, marcado como fora do RAG | OK | `app.py:123-130`; ação #9 |
| R2-04: rodapé removido antes do split | OK (com ressalva BAIXA) | `src/ingest.py:12-22`, `src/ingest.py:32`; ações #4, #6 e #8 (R3-04) |
| R2-05/R3-03: falha não é refeita sem ação do usuário | OK | `app.py:32-54`; `get_store()` só é chamado na aba 3 (`app.py:222`); ação #15 |
| Overlap opção (a), confirmada pelo usuário: corte entre palavras, até 40 | OK | `src/ingest.py:56-62`; ações #5 e #7 (28 a 39, 0 pares sem overlap, 0 cortes no meio de palavra) |
| Parâmetros da SPEC inalterados (350/40, K=3, modelos) | OK | `src/config.py:30-43`, `.env.example`; ações #5 e #16 |
| Vetores lidos do Chroma em cache, sem nova chamada à OpenAI | OK | `app.py:27-29`, `app.py:226-234`; ações #14 e #16 |
| A plataforma mostra a etapa atual (SPEC objetivo) | OK | Abas 2 e 3 dedicadas à Onda 3 e aos embeddings |
| Dependências declaradas e fixadas | OK | `requirements.txt:1-11`; ação #2 |
| `.env.example` com todas as variáveis / `.env` fora do versionamento | OK | Nenhuma variável nova; `.gitignore:1`; ação #3 |
| App sobe sem erro | OK | Ações #9, #11, #15, #16 e #17 |
| Sem regressão das Ondas 1 e 2 | OK | Sidebar e Setup renderizam; a aba 1 tem as mesmas métricas (o resumo de embeddings mudou da aba 1 para a aba 3); 3 PDFs e 6 páginas lidas; máx. 350; ações #5, #9 e #16 |
| Nenhum dado inventado | OK | As abas só mostram dados de `docs/`, `contexto/`, do Chroma e da config |

## 5. Status dos achados anteriores (se re-revisão)
| ID | Status | Evidência |
|---|---|---|
| R3-01 (BAIXA) | RESOLVIDO | Métrica "Embeddings no Chroma" = `len(store.get()["ids"])` (`app.py:226-228`); 49 com falso e com real; contador em 1 chamada (ações #11, #14 e #16). Critério de aceite cumprido |
| R3-02 (BAIXA) | RESOLVIDO | `_neighbor_sim` devolve "outro doc" quando o vizinho é de outro documento (`app.py:241-247`); #16 anterior = "outro doc"; #1 e #17 sem aviso (ação #12). Critério de aceite cumprido. O Executor escolheu o critério "mesmo documento" e não "mesma página": entre páginas do mesmo documento (#7/#8, #24/#25) a similaridade é calculada, e a legenda `app.py:255` deixa isso explícito. Bate com a ação proposta, que aceitava as duas formas |
| R3-03 (SUGESTÃO, aprovada) | RESOLVIDO | Erro guardado em `st.session_state.embed_error` (`app.py:37-43`); "Tentar novamente" limpa o erro e o cache (`app.py:46-54`); `get_store()` é chamado uma vez por rerun (só na aba 3). Ação #15: 1 tentativa na carga e 1 por clique em "Tentar novamente", 0 em reruns e cliques de navegação |
| R2-05 (SUGESTÃO, aprovada) | RESOLVIDO | Mesma correção da R3-03. Critério ("uma segunda execução não faz nova chamada sem ação do usuário") cumprido (ação #15) |
| R2-04 (SUGESTÃO, aprovada) | RESOLVIDO (ressalva BAIXA) | Critério de aceite cumprido: nenhum chunk contém "Página X de Y" nem a linha fixa, e a contagem aparece na UI (ações #6 e #9). Limitação genérica registrada em R3-04 |
| R1-04 (SUGESTÃO, aprovada) | RESOLVIDO | A aba Setup lista `contexto.txt` com a legenda "Não é indexado no RAG: será usado apenas como base do system prompt (Onda 5)." (`app.py:123-130`; ação #9) |
| Dúvida 1: overlap | ENCERRADA | O usuário confirmou a opção (a). O código continua na opção (a) com o separador `\s` por regex (`src/ingest.py:56-62`); os números estão na ação #5 |
| Dúvida 2: abas | ENCERRADA, ATENDIDA | "separar as abas": `app.py:101-110` |
| Dúvida 3: gráfico 2D | ENCERRADA | "não precisa": não foi implementado, o que está correto |

## 6. Achados (o que precisa mudar)
### [R3-04] Remoção de rodapé não cobre documento de uma página nem documento com página vazia - BAIXA
- **Onde:** `src/ingest.py:15-22`
- **Problema:** `strip_footer` só remove a linha fixa do rodapé se o documento tiver mais de uma página **e** todas as páginas tiverem texto (`len(cleaned) > 1 and ... and all(cleaned)`, linha 20). Teste com entradas sintéticas (ação #8): num PDF de uma página, "Página 1 de 1" sai, mas a linha fixa (ex.: "Xperiun Tecnologia S.A. - Confidencial") fica no chunk. Num PDF com uma página sem texto (ex.: escaneada), a linha fixa fica em todas as páginas. Os 3 PDFs de hoje não têm esse problema (ação #6), mas a SPEC manda indexar "tudo que estará ali" em `docs/`, então isso aparece assim que entrar um documento de uma página. O efeito é só ruído no chunk e no embedding, sem resultado errado. Por isso é BAIXA.
- **Regra violada:** escopo aprovado R2-04 ("remover linhas no padrão `Página \d+ de \d+` e o rodapé repetido antes do split"), que hoje vale só em parte para casos genéricos.
- **Ação para o Executor (opcional):** (1) calcular a linha repetida só entre as páginas com texto (ignorar páginas vazias no `set` e no `all`); (2) opcionalmente, quando o documento tem uma página só, remover a linha logo antes de "Página X de Y" apenas se a página tinha esse marcador. Não mudar chunk_size/overlap.
- **Critério de aceite:** com as entradas sintéticas `[["a","R","Página 1 de 3"], [], ["c","R","Página 3 de 3"]]` o resultado é `[["a"], [], ["c"]]`; nos 3 PDFs atuais continuam 49 chunks, 0 chunks com rodapé, overlap de 28 a 39.

## 7. Pontos positivos
- Todas as decisões do usuário foram aplicadas sem mexer nos parâmetros da SPEC (350/40, K=3, modelos).
- O índice compartilhado entre as abas (`st.session_state.idx`, `app.py:57-84`) não depende de chave de widget. Por isso ele continua valendo mesmo quando a aba 3 está em erro e o seletor dela não é renderizado. Os botões usam `on_click`, e a sincronização foi conferida nos dois sentidos (ação #13).
- `get_store()` resolve de uma vez a R2-05 e a R3-03: guarda o erro na sessão, só tenta de novo com ação explícita e não mostra o botão quando falta a chave, caso em que tentar de novo não adiantaria (ações #9 e #15).
- `strip_footer` é genérico: não tem nenhum texto de rodapé fixo no código. Ele detecta a linha repetida e o padrão "Página X de Y".
- A troca para `separators=[r"\s", ""]` mantém o corte sempre entre palavras e subiu o overlap mínimo de 23 (iteração 1) para 28. `page_content` continua sendo um recorte exato da página (ação #7).
- O destaque do overlap foi conferido nos 49 chunks, não só numa amostra (ação #10).

## 8. Dúvidas para o usuário (bloqueiam decisão, não inventar)
- Nenhuma dúvida pendente. As três dúvidas da iteração 1 foram encerradas pelas respostas do usuário nesta sessão (seção 5).

## 9. Informações não encontradas / não verificadas
- Renderização visual no navegador (cores do destaque, layout das colunas e botões, gráfico de 1536 barras): NÃO VERIFICADO visualmente. Foi conferida pela árvore de elementos do AppTest (ações #9 a #13) e pelo health check do servidor (ação #17).
- Falha real da API (chave inválida, timeout): NÃO VERIFICADO com chamada real, para não passar da única rodada paga permitida. Foi simulada com falso (ação #15).
- O valor de overlap mínimo "11" que o Executor citou para a variante anterior do separador: NÃO VERIFICADO, porque o código dessa variante não existe mais. Não afeta o veredito: o código atual foi medido (ação #5).
- Instalação do zero em outra máquina: NÃO VERIFICADO (exigiria instalar pacotes). O `--dry-run` no venv atual está consistente (ação #2).

## 10. Handoff para o Agente Executor
Ordem de execução recomendada (BLOQUEANTE > ALTA > MÉDIA > BAIXA):
- [ ] Nenhuma correção obrigatória pendente na Onda 3. **A Onda 4 pode começar.**
- [ ] R3-04 - (BAIXA, opcional) `strip_footer`: ignorar páginas vazias ao detectar a linha repetida e tratar documento de uma página

Para a Onda 4 (SPEC item 4; checklist do REVISOR.md):
- A aba "4. Busca (Augmented)" ainda é placeholder (`app.py:264-265`). Usar `get_store()` (que já trata erro e "Tentar novamente") com `k=config.TOP_K` (=3). Mostrar conteúdo, documento, página e score dos 3 chunks. Sem LLM nesta onda.
- Usar o mesmo `OpenAIEmbeddings` (`vectorstore.get_embeddings()`, modelo `config.EMBEDDING_MODEL`) na consulta. O Chroma já foi criado com ele, e `similarity_search_with_score` usa a função de embedding da coleção.
- Opcional: um botão no resultado que coloque `st.session_state.idx` no `chunk_id` retornado, para conferir o chunk nas abas 2 e 3.

Restrições para o Executor:
- Não alterar parâmetros definidos na SPEC (chunk 350/40, K=3, modelos) sem aprovação do usuário.
- Não implementar itens marcados como SUGESTÃO sem aprovação do usuário.
- Ao terminar, solicitar nova revisão: `/revisar-onda <N>`.
