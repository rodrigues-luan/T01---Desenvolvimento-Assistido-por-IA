# Revisão - Onda 3 - Iteração 1
**Data:** 2026-11-01 | **Revisor:** Tech Lead (agente revisor) | **Veredito:** APROVADO

## 1. Resumo executivo
A Onda 3 trouxe a aba "2. Explorar chunks e embeddings". Nela o usuário vê o total de chunks (49), escolhe um chunk pelo seletor ou pelos botões anterior/próximo e confere metadados, overlap com o chunk anterior e com o próximo (com o trecho destacado), dimensão e norma do vetor, similaridade de cosseno com os vizinhos, as 10 primeiras dimensões e um gráfico do vetor. Os vetores são lidos do Chroma em cache. Tudo foi conferido por execução: com embedding fake (valores conferidos com cálculo independente) e numa única rodada real (1 chamada, 49 textos, norma ~1,0). A Onda 2 continua igual (49 chunks, máximo de 350 caracteres, overlap de 23 a 39 com média 34,8). Não há achado bloqueante, alto ou médio. Ficam dois ajustes BAIXA de exibição e uma SUGESTÃO: quando a API de embedding falha, a nova aba dobra as chamadas repetidas a cada rerun (agrava o R2-05).

## 2. Escopo revisado
- Onda/objetivo segundo a SPEC: "3 - Quero visualizar os chunks lá no streamlit, tendo uma visão de quantos chunks geramos e conseguir selecionar esses chunks" (`SPEC.md`, Desenvolvimento, item 3).
- Critério adicional, a pedido do usuário: o pedido registrado na seção 10 de `revisoes/onda-2-revisao-2.md` (aba com total de embeddings, navegação um a um, overlap por chunk). O usuário reforçou nesta sessão: "pode seguir pra onda 3 e quero que crie uma aba pra testarmos no streamlit".
- Onda e iteração: informadas no pedido (Onda 3, iteração 1). Batem com `revisoes/`: não existia nenhum `onda-3-revisao-*.md`.
- Arquivos analisados: `app.py` (alterado), `src/ingest.py` (alterado: `same_page`, `pair_overlap`), `requirements.txt` (alterado: `numpy==2.5.4`), `src/vectorstore.py`, `src/config.py`, `.env.example`, `.gitignore`, `README.md`. Do `.env` foram lidos só os nomes das chaves (valores mascarados).
- Fora do escopo por decisão informada: as SUGESTÕES R1-04, R2-04 e R2-05 seguem sem implementação e aguardam aprovação. Gráfico 2D de vetores (PCA/t-SNE) não foi feito porque depende de aprovação.
- Revisão anterior considerada: `revisoes/onda-2-revisao-2.md` (e, por referência, `onda-2-revisao-1.md` e `onda-1-revisao-1.md`).

## 3. O que o revisor fez (rastreabilidade)
| # | Ação | Comando/arquivo | Resultado |
|---|---|---|---|
| 1 | Versão do Python do venv | `.venv/Scripts/python --version` | 3.13.1, OK (>= 3.11) |
| 2 | Consistência das dependências | `pip check` | "No broken requirements found." |
| 3 | numpy declarado e instalado | `pip show numpy` | 2.5.4, igual a `requirements.txt:11`; requerido por chromadb, streamlit, pymupdf, entre outros (já era transitiva) |
| 4 | Reprodutibilidade do requirements | `pip install -r requirements.txt --dry-run` | Nenhum "Would install" nem erro |
| 5 | Regressão da Onda 2 (chunking) | script: `load_documents` + `split_documents` + `overlaps` | 6 páginas, 0 puladas; 49 chunks; máximo 350; 43 pares; 0 sem overlap; mín. 23, máx. 39, média 34,8 (iguais à revisão anterior) |
| 6 | `pair_overlap` comparado com medição independente pelo texto | script do revisor (maior sufixo de A que é prefixo de B) | 0 divergências; `chunk_id == índice` em 49/49 (premissa usada para os ids do Chroma em `app.py:194`) |
| 7 | App sem chave OpenAI | AppTest com `OPENAI_API_KEY=` | 0 exceções; 5 abas: `0. Setup`, `1. Chunks (Retriever)`, `2. Explorar chunks e embeddings`, `3. Busca (Augmented)`, `4. Chat (Generation)`; seletor "Selecione um chunk (49 no total)" com 49 opções; botões "◀ Anterior"/"Próximo ▶"; métricas do #0: Aditivo / p.1 / 348 car. / overlap 0 e 35; metadados `{"source", "page", "start_index", "chunk_id"}`; seção Embedding mostra `st.error` "OPENAI_API_KEY ausente..." |
| 8 | Destaque do overlap no texto | AppTest + regex nas tags `<mark>` | Nos chunks #0, #1, #17, #18 e #48: o trecho azul é sufixo do chunk anterior e prefixo do atual; o trecho laranja é sufixo do atual e prefixo do próximo; tamanhos iguais às métricas; o texto sem tags é idêntico ao `page_content` |
| 9 | Embedding fake determinístico (hash do texto), Chroma real | AppTest com `OpenAIEmbeddings.embed_documents` substituído | 0 exceções; Dimensão 1536; Norma L2 e similaridades com anterior/próximo **iguais ao cálculo independente** (4 casas) nos índices 0, 1, 17, 18 e 48; "-" no primeiro e no último; prévia `st.code` igual a `vec[:10]`; 1 `vega_lite_chart` (gráfico do vetor) |
| 10 | Navegação | AppTest: Próximo, Próximo, Anterior, Anterior, Anterior | 0 → 1 → 2 → 1 → 0 → **48** (dá a volta); seletor acompanha o `session_state`; 0 exceções |
| 11 | Fronteiras de página/documento | AppTest nos índices 8, 16, 25, 34 e 41 | Overlap com anterior = 0 em todos (correto, a página muda); a similaridade com anterior **é calculada mesmo assim**, com o chunk de outra página/documento (ex.: #16 Contrato p.1 contra #15 Aditivo p.2). Ver R3-02 |
| 12 | Cache: chamadas de embedding com vários reruns | contador em `embed_documents` (fake) | `[49]`: 1 chamada em mais de 10 reruns |
| 13 | Falha da API de embedding | fake que lança erro | 0 exceções; `st.error` "Falha ao gerar embeddings..." (aba 1) e "Falha ao obter embeddings..." (aba 2); **2 chamadas por rerun** (`[49, 49]`), e mais 2 a cada clique em Próximo (`[49, 49, 49, 49]`). Ver R3-03 |
| 14 | **Única rodada real de embeddings** | AppTest com a chave do `.env`, contador em `embed_documents`, 8 reruns | 0 exceções; `st.success` "49 chunks vetorizados com `text-embedding-3-small` (dimensão 1536)..."; normas de 0,9997 a 1,0002; similaridade entre vizinhos de 0,44 a 0,63; **1 chamada** (49 textos, `text-embedding-3-small`) |
| 15 | Subida real do servidor | `streamlit run app.py --server.port 8599 --server.headless true` + `/_stcore/health` | `ok`; processo da 8599 (PID 41036) encerrado depois; Streamlit do usuário na 8501 continuou respondendo (HTTP 200) antes e depois |
| 16 | Segurança do HTML | `app.py:172-179` | Texto escapado com `html.escape` antes do `unsafe_allow_html=True` |
| 17 | Segredos | `.env` mascarado; código revisado | Chaves só lidas de env (`src/config.py:24-25`); UI só mostra configurada/ausente (`app.py:42-43`) |

## 4. Checklist da onda
| Critério (fonte) | Status | Evidência |
|---|---|---|
| Streamlit mostra o total de chunks gerados (SPEC onda 3) | OK | Aba 1: métrica "Chunks gerados" (`app.py:73`); aba 2: rótulo "Selecione um chunk (49 no total)" (`app.py:146`); ação #7 |
| Usuário seleciona um chunk e vê o conteúdo (SPEC onda 3) | OK | `app.py:139-153` (seletor + botões), `app.py:168-179` (texto); ações #7, #8 e #10 |
| Mostra origem/metadados do chunk (REVISOR onda 3, recomendado) | OK | `app.py:161-166` (documento, página, caracteres) e `app.py:185-186` (`st.json` com `source`, `page`, `start_index`, `chunk_id`); ação #7 |
| Pedido do usuário: aba própria para testar a onda | OK | Aba "2. Explorar chunks e embeddings" (`app.py:45-53`, `app.py:130-213`); ação #7 |
| Pedido do usuário: total de embeddings gerados | PARCIAL | O total de vetores aparece só na aba 1 (`app.py:107-110`); na aba 2 aparecem modelo e dimensão (`app.py:200`, `app.py:209`), mas não o total de embeddings. Ver R3-01 |
| Pedido do usuário: navegar um a um | OK | Botões anterior/próximo com `on_click` (`app.py:139-144`); ação #10 |
| Pedido do usuário: overlap por chunk, com destaque | OK | `src/ingest.py:56-65`, `app.py:158-183`; ações #6, #8 e #11 |
| Pedido do usuário/handoff: prévia do vetor e norma | OK | `app.py:199-211`; ações #9 e #14 |
| Vetores lidos do Chroma em cache, sem nova chamada à OpenAI (handoff R2) | OK | `app.py:193-195` usa `get_vectorstore()` (`@st.cache_resource`, `app.py:27-29`); ações #12 e #14: 1 chamada por processo |
| Parâmetros da SPEC inalterados (350/40, K=3, modelos) | OK | `src/config.py:30-43`, `.env.example`; ação #5 |
| A plataforma mostra a etapa atual (SPEC objetivo) | OK | Aba 2 dedicada à Onda 3 |
| Dependências declaradas e fixadas | OK | `requirements.txt:1-11`; ações #2 a #4 |
| `.env.example` com todas as variáveis usadas / `.env` fora do versionamento | OK | Nenhuma variável nova; `.gitignore:1` |
| App sobe sem erro | OK | Ações #7, #9, #14 e #15 |
| Sem regressão das Ondas 1 e 2 | OK | Setup e sidebar renderizam; aba 1 com as mesmas métricas e o `st.success` dos embeddings (ações #5, #7 e #14) |
| Nenhum dado inventado | OK | A aba só mostra dados derivados de `docs/`, do Chroma e da config |

## 5. Status dos achados anteriores (se re-revisão)
Primeira revisão da Onda 3. Pendências que vieram da Onda 2:
| ID | Status | Evidência |
|---|---|---|
| Pedido do usuário (seção 10 de `onda-2-revisao-2.md`) | ATENDIDO, com um ajuste BAIXA | Critério de aceite do handoff cumprido: total 49 visível na aba, conteúdo/origem/overlap mudam ao trocar o seletor (ações #7, #9 e #10), contador em 1 chamada por processo (ações #12 e #14). Falta o total de embeddings na própria aba (R3-01). Em vez de uma aba "Embeddings" separada, o Executor juntou chunks e embeddings numa aba só (ver seção 8, item 2) |
| Dúvida do overlap, opção (a) | PENDENTE (decisão do usuário) | Código sem mudança (`src/ingest.py:41-48`); ver seção 8, item 1 |
| R2-04 (SUGESTÃO) | NÃO IMPLEMENTADO (esperado) | Aguarda aprovação |
| R2-05 (SUGESTÃO) | NÃO IMPLEMENTADO (esperado), **agravado** | A nova aba chama `get_vectorstore()` de novo (`app.py:193`), então numa falha cada rerun faz 2 tentativas, e cada clique de navegação gera um rerun (ação #13). Ver R3-03 |
| R1-04 (SUGESTÃO, Onda 1) | NÃO IMPLEMENTADO (esperado) | Aguarda aprovação |

## 6. Achados (o que precisa mudar)
### [R3-01] Total de embeddings não aparece na aba de exploração - BAIXA
- **Onde:** `app.py:146` e `app.py:188-211`
- **Problema:** O pedido do usuário pedia, na aba de embeddings, "ver quantos foram gerados". O handoff da Onda 2 também pedia "Mostrar o total de embeddings gerados, o modelo e a dimensão". Na aba 2 aparecem o modelo e a dimensão (`app.py:200`, `app.py:209`), mas o único total é o de chunks, que vem de `len(load_chunks())` e não do Chroma. O total de vetores só aparece no `st.success` da aba 1 (`app.py:107-110`). Hoje os números são iguais (49), mas a aba 2 não comprova isso.
- **Regra violada:** pedido do usuário registrado em `revisoes/onda-2-revisao-2.md`, seção 10; objetivo da SPEC ("visualizar todas as informações na plataforma").
- **Ação para o Executor:** na seção "Embedding" da aba 2, adicionar uma métrica "Embeddings no Chroma" lida do store em cache (ex.: `len(store.get(include=[])["ids"])`), sem nova chamada à OpenAI.
- **Critério de aceite:** AppTest com embedding fake mostra a métrica "Embeddings no Chroma" = 49 na aba 2, e o contador de `embed_documents` continua em 1 chamada.

### [R3-02] Similaridade "com anterior/próximo" atravessa página e documento sem avisar - BAIXA
- **Onde:** `app.py:194` e `app.py:206-207`
- **Problema:** Nas fronteiras, o overlap mostra 0 e a legenda avisa que o "overlap só existe entre chunks da mesma página" (`app.py:180-183`). Já a similaridade é calculada contra o vizinho de índice, mesmo que ele seja de outra página ou outro documento, e nada indica isso. Exemplo (ação #11 e rodada real, ação #14): o chunk #16 (Contrato p.1) mostra "Similaridade c/ anterior 0.4397", calculada contra o #15, do **Aditivo** p.2. O mesmo vale para a navegação circular: do #0, "Anterior" vai para o #48 (Política p.2), o que está correto como navegação mas pode confundir na leitura dos vizinhos.
- **Regra violada:** nenhuma regra explícita. Dentro do escopo do pedido do usuário (ver os vizinhos para conferir o resultado), a informação pode levar a uma leitura errada.
- **Ação para o Executor:** identificar o vizinho usado em cada métrica de similaridade (ex.: `help`/`caption` "vs #15 · Aditivo p.2") **ou** marcar quando o vizinho é de outra página/documento (ex.: usar `ingest.same_page` e acrescentar "(outra página)"). Não mudar o cálculo.
- **Critério de aceite:** AppTest no índice 16 mostra a similaridade com anterior acompanhada da identificação do #15 ou de um aviso de outro documento/página; nos índices 1 e 17 (mesma página) não aparece o aviso.

### [R3-03] Em falha da API de embedding, a nova aba dobra as tentativas por rerun - SUGESTÃO
- **Onde:** `app.py:104` e `app.py:193` (duas chamadas a `get_vectorstore()` por rerun), `app.py:27-29`
- **Problema:** `st.cache_resource` não guarda exceções. Com a aba 2, uma falha (chave inválida, timeout, limite de taxa) gera 2 tentativas completas de embedding (49 textos) por rerun, e cada clique em Anterior/Próximo gera outro rerun. Ação #13: `[49, 49]` no primeiro carregamento e `[49, 49, 49, 49]` depois de um clique. É o mesmo tema da R2-05, agora pior.
- **Regra violada:** nenhuma (fora da SPEC/PRD); por isso é SUGESTÃO.
- **Ação para o Executor (só com aprovação do usuário, junto com a R2-05):** chamar `get_vectorstore()` uma vez por rerun (ex.: antes das abas, guardando o resultado ou o erro numa variável) e/ou guardar a falha no `st.session_state` com um botão "Tentar novamente".
- **Critério de aceite:** com o fake que falha, o contador fica em no máximo 1 tentativa por clique explícito em "Tentar novamente" (ou 1 por rerun, se o usuário só aprovar a unificação).

## 7. Pontos positivos
- `pair_overlap`/`same_page` reaproveitam o cálculo validado na Onda 2, e `overlaps` passou a usá-las sem mudar nenhum número (ações #5 e #6).
- O destaque do overlap está exato: os trechos marcados batem exatamente com o texto em comum com o vizinho, inclusive quando os dois destaques se encostam ou um deles fica vazio (ação #8). O HTML é escapado antes de renderizar.
- A busca no Chroma é feita por ids e o resultado é montado num dicionário (`app.py:194-196`), sem depender da ordem do retorno.
- A rodada real mostrou valores coerentes: norma ~1,0 (vetores normalizados do `text-embedding-3-small`) e similaridade maior entre vizinhos com overlap.
- A troca de chunk pelos botões usa `on_click`, o jeito certo de mudar o estado de um widget com `key` antes de renderizar. O índice volta a 0 se o número de chunks mudar (`app.py:136-137`).
- Sem chave OpenAI, a parte de chunks continua utilizável e só a seção de embedding mostra o erro (ação #7).

## 8. Dúvidas para o usuário (bloqueiam decisão, não inventar)
1. **Interpretação do overlap (continua pendente).** Desde a Onda 2 está aplicada a opção (a): corte entre palavras, overlap de até 40 (medido: 23 a 39, média 34,8, nenhum par sem overlap). O usuário ainda não confirmou de forma explícita. As alternativas eram (b) exatamente 40 caracteres, podendo cortar palavras, ou (c) separadores padrão (overlap médio de 4,6 na iteração 1 da Onda 2). A nova aba deixa isso fácil de conferir: os trechos destacados mostram o overlap real de cada chunk. Se a opção (a) for confirmada, nada muda.
2. **Uma aba só ou abas separadas para chunks e embeddings?** O handoff da Onda 2 sugeria uma aba "Embeddings" separada da de Chunks. O Executor fez uma aba única, "2. Explorar chunks e embeddings", que atende à Onda 3 e ao pedido de embeddings, e manteve o resumo de embeddings na aba 1. Isso combina com "quero que crie uma aba pra testarmos", mas se o usuário preferir uma aba por assunto (ex.: "Embeddings" separada), é uma mudança simples de layout.
3. **Gráfico 2D dos vetores (PCA/t-SNE):** não feito, depende de aprovação (pode exigir dependência nova, como scikit-learn). Só implementar se o usuário pedir.

## 9. Informações não encontradas / não verificadas
- Renderização visual no navegador (cores do destaque, layout dos botões, legibilidade do gráfico com 1536 barras): NÃO VERIFICADO visualmente. Foi verificada pela árvore de elementos do AppTest (ações #7 a #11) e pelo health check do servidor (ação #15).
- Falha real da API (chave inválida, timeout): NÃO VERIFICADO com chamada real, para não passar de uma rodada paga. Foi simulada com fake (ação #13).
- Instalação do zero em outra máquina: NÃO VERIFICADO (exigiria instalar pacotes); o `--dry-run` no venv atual está consistente (ação #4).

## 10. Handoff para o Agente Executor
Ordem de execução recomendada (BLOQUEANTE > ALTA > MÉDIA > BAIXA):
- [ ] Nenhuma correção obrigatória pendente na Onda 3. A Onda 4 pode começar.
- [ ] R3-01 - (BAIXA, opcional) métrica "Embeddings no Chroma" na aba 2, lida do store em cache
- [ ] R3-02 - (BAIXA, opcional) identificar o vizinho usado na similaridade, ou avisar quando ele é de outra página/documento
- [ ] (Decisão do usuário) Overlap: se o usuário não confirmar a opção (a), ajustar `src/ingest.py:43-48` para a opção escolhida
- [ ] (Decisão do usuário) Separar chunks e embeddings em abas diferentes, se o usuário preferir
- [ ] R3-03 / R2-05 - (SUGESTÃO, só com aprovação do usuário) uma chamada de `get_vectorstore()` por rerun e/ou "Tentar novamente" após falha
- [ ] R2-04 - (SUGESTÃO, só com aprovação do usuário) remover cabeçalho/rodapé antes do split
- [ ] R1-04 - (SUGESTÃO, só com aprovação do usuário) mostrar `contexto/` na aba Setup
- [ ] Gráfico 2D (PCA/t-SNE) - só com aprovação do usuário
- Para a Onda 4: a aba "3. Busca (Augmented)" já existe como placeholder (`app.py:215-216`). Reaproveitar o `get_vectorstore()` em cache, com K vindo de `config.TOP_K` (=3), e mostrar conteúdo + origem + score dos 3 chunks. Um link para abrir o chunk retornado na aba 2 ajudaria a conferir o resultado.

Restrições para o Executor:
- Não alterar parâmetros definidos na SPEC (chunk 350/40, K=3, modelos) sem aprovação do usuário.
- Não implementar itens marcados como SUGESTÃO sem aprovação do usuário.
- Ao terminar, solicitar nova revisão: `/revisar-onda <N>`.
