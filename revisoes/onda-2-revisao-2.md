# Revisão - Onda 2 - Iteração 2
**Data:** 2026-10-31 | **Revisor:** Tech Lead (agente revisor) | **Veredito:** APROVADO

## 1. Resumo executivo
Esta re-revisão confere as correções da iteração 1. Os três achados obrigatórios (R2-01, R2-02 e R2-03) e o que faltava do R1-02 foram resolvidos e comprovados por execução. O overlap agora existe de fato: 0 de 43 pares consecutivos sem sobreposição, overlap entre 23 e 39 caracteres (média 34,8), maior chunk com 350 caracteres e nenhum corte no meio de palavra. Erros de configuração aparecem como `st.error` em vez de traceback. Páginas sem texto são contadas e listadas na UI. Uma rodada real de embeddings, de ponta a ponta pelo app, gerou 49 vetores de dimensão 1536 com `text-embedding-3-small`, numa única chamada, que o cache reaproveitou no rerun. Não há achado novo. O único ponto em aberto é o usuário confirmar a interpretação do overlap (opção (a)), que o Executor aplicou sem escolha explícita do usuário (seção 8).

## 2. Escopo revisado
- Onda/objetivo segundo a SPEC: "2 - Fazer os chunks dos documentos da Xperiun que estão na pasta 'docs/' [...] Chunks de 350 caracteres com um Overlap de 40. Para fazer o embbeding, pode usar o modelo da Open AI text-embedding-3-small" (`SPEC.md`, Desenvolvimento, item 2).
- Onda e iteração: informadas no pedido (Onda 2, iteração 2). Batem com `revisoes/`: existe `onda-2-revisao-1.md` e não existia `onda-2-revisao-2.md`.
- Arquivos analisados: `src/config.py`, `src/ingest.py`, `app.py` (alterados nesta iteração), `src/vectorstore.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`; o `.env` foi lido só pelos nomes das chaves (valores mascarados).
- Fora do escopo por decisão informada: as SUGESTÕES R1-04, R2-04 e R2-05 ficaram sem implementação de propósito e aguardam aprovação do usuário. Não foram reclassificadas.
- Revisão anterior considerada: `revisoes/onda-2-revisao-1.md` (e `revisoes/onda-1-revisao-1.md` para o R1-02).

## 3. O que o revisor fez (rastreabilidade)
| # | Ação | Comando/arquivo | Resultado |
|---|---|---|---|
| 1 | Versão do Python do venv | `.venv/Scripts/python --version` | 3.13.1, OK (>= 3.11) |
| 2 | Consistência das dependências | `pip check` | "No broken requirements found." |
| 3 | Reprodutibilidade do requirements | `pip install -r requirements.txt --dry-run` | Nenhum "Would install" |
| 4 | Páginas, contagem e tamanho dos chunks | script temporário: `ingest.load_documents()` + `split_documents()` | 6 páginas totais, 6 com texto, 0 puladas; 49 chunks (Contrato 18, Aditivo 16, Política 15); máx. **350**, mín. 123, média 325,7 |
| 5 | Overlap real pelo `start_index` | `ingest.overlaps(chunks)` | 43 pares; **0 sem overlap**; mín. 23, máx. 39, média **34,8** |
| 6 | Overlap real pelo texto (maior sufixo de A que é prefixo de B), independente do `start_index` | script do revisor | Mesmos números (0 / 23 / 39 / 34,8); 0 divergências em relação ao #5 |
| 7 | `start_index` confere com o texto da página | `texto[start:start+len(chunk)] == chunk` | 49/49 corretos |
| 8 | Corte no meio de palavra | caractere antes do início e depois do fim de cada chunk | 0 cortes no meio de palavra |
| 9 | Exemplo do caso citado no R2-01 | chunks 0 e 1 | A termina em `"...1.1. Período de Congelamento: O valor de"`, B começa em `"Período de Congelamento: O valor de face mensal..."`: agora há contexto compartilhado |
| 10 | `chunk_id` único | script | 49 ids únicos |
| 11 | Validação de K | `TOP_K=0`, `TOP_K=-1`, `TOP_K=abc` | `ValueError: TOP_K (0) deve ser >= 1`; `TOP_K (-1) deve ser >= 1`; `TOP_K deve ser um inteiro, recebido: 'abc'` |
| 12 | Variáveis vazias caem no padrão | `TOP_K= CHUNK_SIZE= CHUNK_OVERLAP=` | `350 40 3` |
| 13 | Overlap >= size | `CHUNK_SIZE=30 CHUNK_OVERLAP=40` | `ValueError: CHUNK_OVERLAP (40) deve ser >= 0 e menor que CHUNK_SIZE (30)` |
| 14 | Erro de config no app | AppTest com `TOP_K=0` | 0 exceções; `st.error` "Configuração inválida no .env: TOP_K (0) deve ser >= 1" |
| 15 | Erro de config no app | AppTest com `CHUNK_SIZE=30 CHUNK_OVERLAP=40` | 0 exceções; `st.error` "Configuração inválida no .env: CHUNK_OVERLAP (40) deve ser >= 0 e menor que CHUNK_SIZE (30)" |
| 16 | App sem chave OpenAI | AppTest com `OPENAI_API_KEY=` | 0 exceções; 4 abas; métricas Documentos 3 / Páginas totais 6 / Páginas com texto 6 / Chunks 49 / Maior chunk 350 / Overlap médio 34.8; caption "mín 23, máx 39, pares sem overlap: 0 de 43 (alvo até 40, corte sempre entre palavras)"; sem `st.warning`; tabelas 3x2 e 49x5 |
| 17 | Página em branco, `load_pdf` | PDF de teste com 2 páginas (a 2ª em branco), criado no scratchpad, fora de `docs/` | `(1 página com texto, total 2, puladas [2])` |
| 18 | Página em branco, UI | AppTest com `DOCS_DIR=<scratchpad>` e `OPENAI_API_KEY=` | 0 exceções; Páginas totais 2 / com texto 1; `st.warning` "Páginas sem texto extraível pelo PyMuPDF (candidatas a OCR): teste.pdf p.2" |
| 19 | **Única rodada real de embeddings** (49 textos), de ponta a ponta pelo app | AppTest com a chave do `.env`, contador em `OpenAIEmbeddings.embed_documents`, 2 execuções | 0 exceções e 0 erros nas duas execuções; `st.success` "49 chunks vetorizados com `text-embedding-3-small` (dimensão 1536) e carregados no Chroma em memória."; **1 chamada** (49 textos, modelo `text-embedding-3-small`) em 2 execuções, o cache funcionou |
| 20 | Subida real do servidor | `streamlit run app.py --server.port 8599 --server.headless true` + `/_stcore/health` | `ok`; processo da porta 8599 encerrado depois; o Streamlit do usuário na 8501 continuou respondendo (HTTP 200) |
| 21 | Segredos | `.env` com valores mascarados; código revisado | Chaves só lidas de env (`src/config.py:24-25`); a UI só mostra configurada/ausente (`app.py:39-40`) |

## 4. Checklist da onda
| Critério (fonte) | Status | Evidência |
|---|---|---|
| Lê todos os documentos de `docs/` (3 PDFs) (REVISOR onda 2) | OK | `src/config.py:47-49`, `src/ingest.py:29-37`; ação #4: os 3 documentos geram chunks |
| chunk_size = 350 no código (SPEC onda 2) | OK | `src/config.py:30`, `src/ingest.py:44`, `.env.example` |
| chunk_size = 350 empiricamente | OK | Ação #4: maior chunk 350 (<= 350) |
| chunk_overlap = 40 no código (SPEC onda 2) | OK | `src/config.py:31`, `src/ingest.py:45` |
| chunk_overlap = 40 empiricamente | OK (interpretação "até 40", a confirmar, ver seção 8) | Ações #5 e #6: 0 de 43 pares sem overlap, 23 a 39 caracteres, média 34,8 |
| Embedding OpenAI `text-embedding-3-small` (SPEC onda 2) | OK | `src/vectorstore.py:11-14`, `src/config.py:37`; ação #19: dimensão 1536, modelo confirmado na chamada |
| Metadados para rastreabilidade (documento e página) (PRD "trazer o chunk") | OK | `src/ingest.py:23` (`source`, `page`), `src/ingest.py:51` (`chunk_id`), `start_index` correto (ação #7) |
| Texto legível, páginas vazias tratadas (REVISOR onda 2) | OK | Páginas puladas registradas (`src/ingest.py:17-19`) e mostradas na UI (`app.py:62-63`, `app.py:68-72`); ações #17 e #18 |
| Chroma em memória com cache do Streamlit (decisão aprovada) | OK | `src/vectorstore.py:17-24` sem `persist_directory`; `app.py:24-26`; ação #19: 1 build em 2 execuções |
| A plataforma mostra a etapa atual (SPEC objetivo) | OK | `app.py:54-119`: métricas (incluindo páginas totais e overlap médio), aviso de páginas puladas, chunks por documento, embeddings e tabela completa |
| Parâmetros vêm de config/env (REVISOR transversal) | OK | `src/config.py:27-44`; `src/ingest.py:44-45` lê de `config` |
| `.env.example` com todas as variáveis usadas | OK | As 10 chaves lidas em `src/config.py` estão no `.env.example` |
| `.env` não versionado, sem chave no código | OK | `.gitignore:1`; ação #21 |
| Dependências declaradas e fixadas | OK | `requirements.txt:1-10` com `==`; ações #2 e #3 |
| App sobe sem erro | OK | Ações #16, #19 e #20 |
| Sem regressão da Onda 1 | OK | Aba Setup e sidebar renderizam; 4 abas (ação #16) |
| Nenhum dado inventado | OK | A UI só mostra dados derivados de `docs/` e da config |

## 5. Status dos achados anteriores (se re-revisão)
| ID | Status | Evidência |
|---|---|---|
| R2-01 (ALTA) Overlap quase inexistente | RESOLVIDO | `src/ingest.py:43-48` usa `separators=[" ", ""]`, mantendo `config.CHUNK_SIZE`/`config.CHUNK_OVERLAP`. Critério de aceite cumprido: 0 pares sem overlap, média 34,8 (>= 20), maior chunk 350 (<= 350), padrões 350/40 (ações #4 a #6). A métrica recomendada também foi feita: "Overlap médio" e caption com mín/máx/pares sem overlap na aba (`app.py:66`, `app.py:73-78`; ação #16). A escolha da opção (a) ainda depende de confirmação do usuário (seção 8) |
| R2-02 (BAIXA) Restante do R1-02: `TOP_K` e traceback | RESOLVIDO | `src/config.py:40-41` valida `TOP_K >= 1` (ação #11); `app.py:6-10` captura `ValueError` no import e chama `st.error` + `st.stop()` (ações #14 e #15: 0 exceções, mensagem clara); padrões continuam 350/40/3 (ação #12) |
| R1-02 (BAIXA, Onda 1) Config robusta | RESOLVIDO | O que estava pendente (TOP_K e `st.error`) foi fechado pelo R2-02. As partes já resolvidas na iteração 1 continuam funcionando (ações #11 a #13) |
| R2-03 (BAIXA) Páginas sem texto descartadas em silêncio | RESOLVIDO | `src/ingest.py:10-26` e `29-37` devolvem o total e as páginas puladas `{source, page}`; `app.py:62-63` mostra "Páginas totais" e "Páginas com texto"; `app.py:68-72` mostra `st.warning` com documento e página. Critério cumprido: 6/6 sem aviso nos docs reais (ação #16); com PDF de página em branco aparece o aviso "teste.pdf p.2" (ações #17 e #18) |
| R2-04 (SUGESTÃO) Cabeçalho/rodapé nos chunks | NÃO IMPLEMENTADO (esperado) | Aguarda aprovação do usuário, como informado no pedido |
| R2-05 (SUGESTÃO) Rerun após falha de embedding | NÃO IMPLEMENTADO (esperado) | Aguarda aprovação do usuário; `app.py:24-26` e `app.py:94-103` sem mudança de comportamento nesse ponto |
| R1-04 (SUGESTÃO, Onda 1) Mostrar `contexto/` no Setup | NÃO IMPLEMENTADO (esperado) | Aguarda aprovação do usuário |

## 6. Achados (o que precisa mudar)
Nenhum achado novo nesta iteração. As SUGESTÕES pendentes (R1-04, R2-04, R2-05) continuam descritas em `revisoes/onda-1-revisao-1.md` e `revisoes/onda-2-revisao-1.md` e dependem da decisão do usuário.

## 7. Pontos positivos
- A correção do R2-01 é mínima e localizada (`src/ingest.py:43-48`), com um comentário explicando o motivo (`src/ingest.py:41-42`), e não mexe nos parâmetros da SPEC.
- O overlap ficou visível na plataforma (métrica e caption), como pede o objetivo da SPEC ("visualizar todas as informações na plataforma"). Assim o usuário pode conferir o parâmetro sem script.
- `ingest.overlaps` usa o `start_index` e dá exatamente o mesmo resultado que a medição independente por texto (ação #6). O `start_index` está correto em 49/49 chunks, o que ajuda as Ondas 3 e 4.
- Erros de configuração agora aparecem de forma amigável e cobrem `TOP_K`, overlap >= size e valores não inteiros.
- O registro de páginas puladas deixa pronto o gatilho para a decisão "PyMuPDF primeiro, OCR só se falhar".
- O caminho real (OpenAI + Chroma em memória + cache) funcionou de ponta a ponta pelo app, com uma única chamada de embedding em duas execuções.

## 8. Dúvidas para o usuário (bloqueiam decisão, não inventar)
1. **Confirmar a interpretação do overlap (decisão aplicada, aguardando confirmação).** Na iteração 1, a dúvida 1 perguntava se "Overlap de 40" significa exatamente 40 ou até 40. O Executor aplicou a opção (a), recomendada pelo revisor: corte em fronteira de palavra (`separators=[" ", ""]`), overlap de até 40 (medido: 23 a 39, média 34,8, nenhum par sem overlap). O usuário pediu "execute a onda 2" sem escolher uma opção, por isso isto fica registrado como **decisão a confirmar**, não como achado. Se preferir outra opção:
   - (b) exatamente 40 caracteres, cortando no caractere (pode partir palavras ao meio);
   - (c) voltar aos separadores padrão (respeita linhas, mas na iteração 1 o overlap médio era 4,6 e 77% dos pares não tinham overlap).
   Se a opção (a) for confirmada, nada muda no código.

## 9. Informações não encontradas / não verificadas
- Renderização visual no navegador: NÃO VERIFICADO visualmente. Foi verificada pela árvore de elementos do AppTest (ações #16, #18 e #19) e pelo health check do servidor (ação #20).
- Caminho de falha da API com chave inválida ou timeout: NÃO VERIFICADO com chamada real, para não gastar uma segunda rodada paga. Pelo código, cai no `st.error` de `app.py:102-103`.
- Instalação do zero em outra máquina: NÃO VERIFICADO (exigiria instalar pacotes); o `--dry-run` no venv atual está consistente (ação #3).
- Fallback de OCR: não implementado e não exercitado, porque nenhuma página real ficou sem texto (ação #4), o que está alinhado com a decisão aprovada.

## 10. Handoff para o Agente Executor
Ordem de execução recomendada (BLOQUEANTE > ALTA > MÉDIA > BAIXA):
- [ ] Nenhuma correção obrigatória pendente na Onda 2. A Onda 3 pode começar.
- [ ] **Pedido do usuário, recebido depois desta revisão (prioridade para a próxima iteração):** "para cada onda executada eu quero ver lá na plataforma uma aba mostrando visualmente o que foi feito [...] ex: ver embedding gerados, ver quantos foram gerados, conseguir navegar entre eles, ver quantos overlaps aquele embedding tem". Isso está alinhado com o objetivo da SPEC ("desde a etapa 0 eu quero visualizar todas as informações na plataforma") e se sobrepõe à Onda 3 ("visualizar os chunks [...] quantos chunks geramos e conseguir selecionar esses chunks"). Ação para o Executor:
  - Ter uma aba própria por onda executada. Para a Onda 2, criar uma aba **Embeddings** separada da aba de Chunks.
  - Mostrar o total de embeddings gerados, o modelo e a dimensão (hoje: 49, `text-embedding-3-small`, 1536).
  - Permitir navegar entre os embeddings, um por vez (seletor por `chunk_id` ou botões anterior/próximo). Para cada um, mostrar: o texto do chunk, a origem (documento/página/`start_index`), uma prévia do vetor (primeiros valores e norma) e o overlap em caracteres com o chunk anterior e com o próximo, destacando o trecho sobreposto (use `ingest.overlaps`/`start_index`, que o revisor validou como corretos).
  - Ler os vetores do Chroma já em cache (`store.get(include=["embeddings","documents","metadatas"])`), sem nova chamada à OpenAI.
  - Critério de aceite: AppTest com o embedding fake mostra a aba com o total 49; ao trocar o seletor, conteúdo, origem e overlap mudam; o contador de `embed_documents` continua em 1 chamada por processo.
  - Gráfico 2D dos vetores (PCA/t-SNE) é opcional e precisa de aprovação do usuário se exigir uma dependência nova.
- [ ] (Decisão do usuário) Se o usuário não confirmar a opção (a) do overlap (seção 8), ajustar `src/ingest.py:43-48` para a opção que ele escolher e pedir nova revisão.
- [ ] R2-04 - (SUGESTÃO, só com aprovação do usuário) remover cabeçalho/rodapé antes do split
- [ ] R2-05 - (SUGESTÃO, só com aprovação do usuário) evitar novas chamadas de embedding a cada rerun depois de uma falha
- [ ] R1-04 - (SUGESTÃO pendente da Onda 1, só com aprovação do usuário) mostrar `contexto/` na aba Setup

Restrições para o Executor:
- Não alterar parâmetros definidos na SPEC (chunk 350/40, K=3, modelos) sem aprovação do usuário.
- Não implementar itens marcados como SUGESTÃO sem aprovação do usuário.
- Ao terminar, solicitar nova revisão: `/revisar-onda <N>`.
