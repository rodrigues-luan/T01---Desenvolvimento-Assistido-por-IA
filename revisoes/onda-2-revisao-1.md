# Revisão - Onda 2 - Iteração 1
**Data:** 2026-10-31 | **Revisor:** Tech Lead (agente revisor) | **Veredito:** APROVADO COM RESSALVAS

## 1. Resumo executivo
A Onda 2 lê os 3 PDFs de `docs/` com PyMuPDF (`import pymupdf`) e gera 49 chunks com `RecursiveCharacterTextSplitter(350, 40)`. Os metadados (`source`, `page`, `start_index`, `chunk_id`) seguem junto com cada chunk. Os embeddings são gerados com `text-embedding-3-small` (dimensão 1536) e guardados num Chroma em memória com `st.cache_resource`. O app sobe sem exceções e a aba "1. Chunks" mostra métricas, chunks por documento, status dos embeddings e a tabela completa. Os três achados da Onda 1 foram tratados (R1-01 e R1-03 resolvidos, R1-02 parcial). O principal risco é o overlap efetivo: no código ele é 40, mas na prática 33 dos 43 pares de chunks consecutivos da mesma página não têm nenhum caractere em comum (média de 4,6 caracteres). Frases são cortadas entre chunks sem a sobreposição que a SPEC pede (R2-01).

## 2. Escopo revisado
- Onda/objetivo segundo a SPEC: "2 - Fazer os chunks dos documentos da Xperiun que estão na pasta 'docs/' [...] Chunks de 350 caracteres com um Overlap de 40. Para fazer o embbeding, pode usar o modelo da Open AI text-embedding-3-small" (`SPEC.md`, seção Desenvolvimento, item 2).
- Onda identificada: informada no pedido (Onda 2, iteração 1). O código confirma: a aba "1. Chunks" está implementada e as abas das Ondas 4 e 5 continuam "Em construção" (`app.py:101-105`). Não havia revisão anterior da Onda 2 em `revisoes/`.
- Arquivos analisados: `src/config.py`, `src/ingest.py`, `src/vectorstore.py`, `app.py`, `requirements.txt`, `.env.example`, `.gitignore`, `README.md`; o `.env` foi lido só pelos nomes das chaves (valores mascarados); listagem de `docs/` e início de `contexto/contexto.txt`.
- Fora do escopo por decisão já informada: seleção individual de chunks (Onda 3), busca/consulta no Chroma (Onda 4), R1-04 (SUGESTÃO aguardando o usuário).
- Revisão anterior considerada: `revisoes/onda-1-revisao-1.md`.

## 3. O que o revisor fez (rastreabilidade)
| # | Ação | Comando/arquivo | Resultado |
|---|---|---|---|
| 1 | Versão do Python do venv | `.venv/Scripts/python --version` | 3.13.1, OK |
| 2 | Consistência das dependências | `pip check` | "No broken requirements found." |
| 3 | Reprodutibilidade do requirements | `pip install -r requirements.txt --dry-run` | Nenhum "Would install": o ambiente já bate com o arquivo |
| 4 | Pacotes LangChain instalados | `pip list \| grep langchain` | Sem `langchain-community` (removido também do venv) |
| 5 | Uso de `fitz` / `langchain_community` | `grep -rn "fitz\|langchain_community" app.py src/` | Nenhuma ocorrência |
| 6 | Config com variável vazia | `CHUNK_SIZE= python -c "from src import config; ..."` | `350 40 3` |
| 7 | Config com overlap >= size | `CHUNK_SIZE=30 CHUNK_OVERLAP=40` | `ValueError: CHUNK_OVERLAP (40) deve ser >= 0 e menor que CHUNK_SIZE (30)` |
| 8 | Config com valor não inteiro | `CHUNK_SIZE=abc` | `ValueError: CHUNK_SIZE deve ser um inteiro, recebido: 'abc'` |
| 9 | Validação de K | `TOP_K=0` e `TOP_K=-1` | Aceitos sem erro (imprime 0 e -1); ver R2-02 |
| 10 | Erro de config dentro do app | AppTest com `CHUNK_SIZE=30 CHUNK_OVERLAP=40` | O app cai com exceção (traceback), sem `st.error`; ver R2-02 |
| 11 | Páginas e texto por PDF | script temporário com `pymupdf` | Os 3 PDFs têm 2 páginas cada, todas com texto (2056 a 2723 caracteres por página) |
| 12 | Contagem e tamanho dos chunks | `ingest.split_documents(ingest.load_documents())` | 6 páginas, 49 chunks (Contrato 18, Aditivo 16, Política 15); máx. 341, mín. 71, média 298,5 caracteres |
| 13 | Overlap real entre chunks consecutivos da mesma página | script: maior sufixo de A que é prefixo de B | 43 pares; **33 com overlap 0**; mín. 0, máx. 39, média 4,6 caracteres |
| 14 | Exemplo de corte sem overlap | chunks 1 e 2 | A termina em `"...irreajustável pelo período inicial de"`, B começa em `"12 (doze) meses, contados..."` |
| 15 | Alternativa só para evidência (sem alterar código) | splitter com `separators=[" ", ""]`, 350/40 | 49 chunks, máx. 350, **0 pares sem overlap**, overlap de 23 a 39 (média 34,8) |
| 16 | Legibilidade do texto | busca por `�`, `Ã.`, `Â.` | Só falsos positivos (maiúsculas acentuadas legítimas: "SEGURANÇA", "NÃO", "CLÁUSULA"). Texto legível |
| 17 | Fronteiras de página | chunks consecutivos com páginas diferentes | O último chunk de cada página 1 traz o rodapé (ex.: `"Xperiun Tecnologia S.A. - Confidencial\nPágina 1 de 2"`); ver R2-04 |
| 18 | App sem chave OpenAI | AppTest com `OPENAI_API_KEY=` | 0 exceções; `st.error` "OPENAI_API_KEY ausente no .env..."; métricas 3 / 6 / 49 / 341; tabelas 3x2 e 49x5 |
| 19 | **Única rodada real de embeddings** (49 textos) | `vectorstore.build_vectorstore(chunks)` com contador em `embed_documents` | 1 chamada, 49 textos, 1,7 s; Chroma com 49 itens, dimensão 1536, modelo `text-embedding-3-small`; ids `'0','1','2'...`; metadados preservados; textos idênticos aos chunks; cliente não persistente |
| 20 | Caminho de sucesso da UI e cache | AppTest com embedding fake (`DeterministicFakeEmbedding(1536)`, chamadas OpenAI bloqueadas), 2 execuções | 0 exceções, 0 erros; `st.success` "49 chunks vetorizados com `text-embedding-3-small` (dimensão 1536)..."; `build_vectorstore` chamado **1 vez** em 2 execuções |
| 21 | Segredos | `.env` lido com valores mascarados; código revisado | Chaves só lidas de env (`src/config.py:24-25`); a UI só mostra configurada/ausente (`app.py:34-35`) |

Observação: a primeira tentativa de AppTest com a store real falhou por caminho relativo no script do revisor (`FileNotFoundError` do AppTest). Para não fazer uma segunda chamada paga, o caminho de UI foi validado com embedding fake (ação #20).

## 4. Checklist da onda
| Critério (fonte) | Status | Evidência |
|---|---|---|
| Lê todos os documentos de `docs/` (3 PDFs) (REVISOR onda 2) | OK | `src/config.py:45-47`, `src/ingest.py:28-32`; ação #12: os 3 documentos geram chunks |
| chunk_size = 350 no código (SPEC onda 2) | OK | `src/config.py:30`, `src/ingest.py:36-40`, `.env.example` |
| chunk_size = 350 empiricamente | OK | Ação #12: maior chunk 341 (<= 350) |
| chunk_overlap = 40 no código (SPEC onda 2) | OK | `src/config.py:31`, `src/ingest.py:38` |
| chunk_overlap = 40 empiricamente | FALHA | Ação #13: 33 de 43 pares sem overlap; média 4,6. Ver R2-01 |
| Embedding OpenAI `text-embedding-3-small` (SPEC onda 2) | OK | `src/vectorstore.py:11-14`, `src/config.py:37`; ação #19: dimensão 1536 |
| Metadados para rastreabilidade (documento e página) (PRD "trazer o chunk") | OK | `src/ingest.py:22` (`source`, `page`), `src/ingest.py:42-43` (`chunk_id`), `start_index`; preservados no Chroma (ação #19) |
| Texto legível, páginas vazias tratadas (REVISOR onda 2) | OK (ressalva R2-03) | Ação #16; páginas vazias são puladas (`src/ingest.py:17-18`), mas isso não aparece na UI |
| Chroma em memória com cache do Streamlit (decisão aprovada) | OK | `src/vectorstore.py:17-24` sem `persist_directory`; `app.py:19-21`; ações #19 e #20 |
| A plataforma mostra a etapa atual (SPEC objetivo) | OK | `app.py:49-99`: métricas, chunks por documento, status dos embeddings e tabela de chunks |
| Parâmetros vêm de config/env (REVISOR transversal) | OK | `src/config.py:27-42`; nada hardcoded em `ingest.py`/`vectorstore.py` |
| `.env.example` com todas as variáveis usadas | OK | As 10 chaves lidas em `src/config.py` estão no `.env.example` |
| `.env` não versionado, sem chave no código | OK | `.gitignore:1`; ação #21 |
| Dependências declaradas e fixadas | OK | `requirements.txt:1-10`, todas com `==`; ação #3 |
| App sobe sem erro | OK | Ações #18 e #20 |
| Sem regressão da Onda 1 | OK | A aba Setup e a sidebar continuam renderizando (ação #18; 4 abas) |
| Nenhum dado inventado | OK | A UI só mostra dados derivados de `docs/` e da config |

## 5. Status dos achados anteriores (se re-revisão)
| ID | Status | Evidência |
|---|---|---|
| R1-01 (MÉDIA) Fixar versões | RESOLVIDO | `requirements.txt:1-10` com `==`, nas versões listadas na revisão anterior; `--dry-run` sem "Would install"; `pip check` OK (ações #2 e #3) |
| R1-02 (BAIXA) Config robusta | PARCIAL | Feito: variável vazia cai no padrão (`src/config.py:11-13`, ação #6), mensagem clara para inteiro inválido (`src/config.py:16-21`, ação #8), validação `0 <= overlap < size` (`src/config.py:32-35`, ação #7). Falta: `TOP_K >= 1` não é validado (`src/config.py:39`, ação #9) e o erro aparece como traceback no app, não como `st.error` (ação #10). Ver R2-02 |
| R1-03 (BAIXA) `fitz` / `langchain-community` | RESOLVIDO | `src/ingest.py:4` usa `import pymupdf`; nenhum `fitz` ou `langchain_community` no código (ação #5); `langchain-community` saiu do `requirements.txt` e do venv (ação #4) |
| R1-04 (SUGESTÃO) Mostrar `contexto/` no Setup | NÃO IMPLEMENTADO (esperado) | Aguarda aprovação do usuário, como informado no pedido |

## 6. Achados (o que precisa mudar)

### [R2-01] Overlap de 40 configurado, mas quase inexistente nos chunks gerados - ALTA
- **Onde:** `src/ingest.py:36-40`
- **Problema:** o `RecursiveCharacterTextSplitter` usa os separadores padrão (`"\n\n"`, `"\n"`, `" "`, `""`). O texto do PyMuPDF vem quebrado em linhas de cerca de 90 caracteres, e o splitter só reaproveita como overlap as *unidades inteiras* (linhas) que cabem em 40 caracteres. Como quase nenhuma linha tem 40 caracteres ou menos, 33 dos 43 pares de chunks consecutivos da mesma página não têm sobreposição alguma. A média é 4,6 caracteres, contra os 40 pedidos (ação #13). Exemplo real: o chunk 1 termina em "...irreajustável pelo período inicial de" e o chunk 2 começa em "12 (doze) meses...". A regra de congelamento de preço de fornecedores (tema do PRD) fica partida em dois chunks sem contexto compartilhado, o que prejudica a busca semântica da Onda 4.
- **Regra violada:** SPEC onda 2: "Chunks de 350 caracteres com um Overlap de 40". REVISOR: "verificar no código E empiricamente nos chunks gerados"; "chunk sem overlap" é exemplo de severidade ALTA.
- **Ação para o Executor:** manter `chunk_size=350` e `chunk_overlap=40` e trocar a granularidade dos separadores para que o overlap aconteça de fato. Opção validada pelo revisor (ação #15): `RecursiveCharacterTextSplitter(chunk_size=config.CHUNK_SIZE, chunk_overlap=config.CHUNK_OVERLAP, separators=[" ", ""], add_start_index=True)`. Ela gera 49 chunks, máximo 350 caracteres, overlap entre 23 e 39 em todos os pares. Outra opção é normalizar as quebras de linha simples do PyMuPDF em espaço antes do split, mantendo `"\n\n"` como separador de parágrafo. Antes de escolher, ver a dúvida 1 da seção 8. Também é recomendado mostrar na aba "1. Chunks" uma métrica de overlap médio entre chunks consecutivos, para que isso fique visível na plataforma.
- **Critério de aceite:** um script (ou métrica na UI) que compare chunks consecutivos da mesma página mostra 0 pares sem overlap e overlap médio próximo de 40 (>= 20); o maior chunk continua <= 350; os padrões continuam 350/40.

### [R2-02] Restante do R1-02: `TOP_K` sem validação e erro de config aparece como traceback - BAIXA
- **Onde:** `src/config.py:39`; `app.py:4` (import de `config` sem tratamento)
- **Problema:** `TOP_K=0` e `TOP_K=-1` são aceitos (ação #9). Com `CHUNK_SIZE=30 CHUNK_OVERLAP=40`, o `ValueError` (com mensagem clara) quebra o app como exceção, sem um `st.error` amigável (ação #10). Os dois pontos estavam no critério de aceite do R1-02.
- **Regra violada:** critério de aceite de `revisoes/onda-1-revisao-1.md`, R1-02 ("Validar ... `TOP_K >= 1`, e mostrar o erro de forma amigável no Streamlit (`st.error`) em vez de traceback"). O K será usado na Onda 4 (SPEC: "3 chunks mais similares").
- **Ação para o Executor:** em `src/config.py`, validar `TOP_K >= 1` com mensagem clara. Em `app.py`, envolver o `from src import config` (ou a validação) num `try/except ValueError` que chame `st.error(str(exc))` e `st.stop()`.
- **Critério de aceite:** `TOP_K=0 python -c "from src import config"` gera `ValueError` com mensagem clara; o AppTest com `CHUNK_SIZE=30 CHUNK_OVERLAP=40` termina com `at.exception` vazio e `at.error` com a mensagem; os padrões continuam 350/40/3.

### [R2-03] Páginas sem texto são descartadas em silêncio - BAIXA
- **Onde:** `src/ingest.py:17-18`; `app.py:55-58`
- **Problema:** uma página sem texto extraível é pulada (`continue`) sem registro. A UI mostra "Páginas com texto", mas não o total de páginas nem quais foram ignoradas. Pela decisão aprovada ("PyMuPDF primeiro, OCR só se falhar"), é preciso saber *quando* a extração falhou para decidir pelo OCR. Hoje todas as 6 páginas têm texto (ação #11), então não há perda atual, só falta de visibilidade.
- **Regra violada:** REVISOR onda 2: "páginas vazias não tratadas"; SPEC objetivo: "visualizar todas as informações na plataforma".
- **Ação para o Executor:** fazer o ingest registrar as páginas puladas (documento e página) e mostrar na aba "1. Chunks" o total de páginas, as páginas com texto e um `st.warning` listando as puladas, se houver.
- **Critério de aceite:** a aba mostra "Páginas totais: 6" e "Páginas com texto: 6", sem aviso. Um teste com um PDF de página em branco (fora de `docs/`, ou por mock) gera o aviso com o nome do documento e o número da página.

### [R2-04] Cabeçalhos e rodapés dos PDFs entram nos chunks - SUGESTÃO
- **Onde:** `src/ingest.py:16` (texto bruto da página)
- **Problema:** linhas como "Gestão de Contratos de Fornecedores - Xperiun / Página 1 de 2" e "Xperiun Tecnologia S.A. - Confidencial / Página 1 de 2" ficam dentro dos chunks (ação #17). Isso gasta parte dos 350 caracteres e adiciona ruído aos embeddings.
- **Regra violada:** nenhuma (fora do escopo obrigatório).
- **Ação para o Executor:** só com aprovação do usuário: remover linhas no padrão `Página \d+ de \d+` e o rodapé repetido antes do split.
- **Critério de aceite:** nenhum chunk contém "Página 1 de 2"; a contagem de chunks é mostrada na UI.

### [R2-05] Falha na geração de embeddings é refeita a cada rerun - SUGESTÃO
- **Onde:** `app.py:19-21`, `app.py:73-83`
- **Problema:** `st.cache_resource` não guarda exceções. Se a chamada à OpenAI falhar (chave inválida, rate limit), cada interação do usuário com o app dispara uma nova chamada. O caminho de sucesso está correto: 1 build em 2 execuções (ação #20).
- **Regra violada:** nenhuma (fora do escopo obrigatório).
- **Ação para o Executor:** só com aprovação do usuário: adicionar um botão "Tentar novamente" (`get_vectorstore.clear()`) e não chamar o build automaticamente depois de uma falha na mesma sessão (ex.: flag em `st.session_state`).
- **Critério de aceite:** com uma chave inválida, uma segunda execução do AppTest não faz nova chamada de embedding sem a ação do usuário.

## 7. Pontos positivos
- R1-01 e R1-03 foram resolvidos exatamente como pedido: versões fixadas e reproduzíveis, `import pymupdf` e `langchain-community` removido também do venv.
- Separação clara de responsabilidades: `config` (parâmetros), `ingest` (leitura e split), `vectorstore` (embedding e Chroma); a UI só orquestra.
- Metadados completos para rastreabilidade (`source`, `page`, `start_index`, `chunk_id`), e os ids do Chroma são o próprio `chunk_id`, o que vai facilitar a Onda 3 (seleção) e a Onda 4 (exibir origem).
- Chroma efêmero de fato (sem `persist_directory`, cliente não persistente) e construído uma vez só por processo (ação #20), conforme a decisão aprovada.
- Sem chave OpenAI, o app não quebra e mostra um erro claro (ação #18). A UI comprova o embedding mostrando a contagem de vetores e a dimensão.
- `split_documents` por página garante que todo chunk tem página única nos metadados.

## 8. Dúvidas para o usuário (bloqueiam decisão, não inventar)
1. **Overlap "de 40" significa exatamente 40 caracteres ou até 40?** Isso define como corrigir o R2-01. Opções:
   (a) overlap próximo de 40 em todos os chunks, cortando em fronteira de palavra (`separators=[" ", ""]`, validado: overlap de 23 a 39); os chunks deixam de respeitar as quebras de linha/parágrafo;
   (b) overlap exatamente 40, cortando no caractere (`CharacterTextSplitter`/`separators=[""]`), o que pode cortar palavras no meio;
   (c) aceitar o comportamento atual (overlap de "até 40", hoje com média de 4,6 e 77% dos pares sem overlap), priorizando chunks que respeitam as linhas.
   A recomendação do revisor é (a), mas a decisão é sua, porque mexe na interpretação de um parâmetro da SPEC.

## 9. Informações não encontradas / não verificadas
- Renderização visual no navegador: NÃO VERIFICADO visualmente; verificada pela árvore de elementos do AppTest.
- AppTest com os embeddings reais da OpenAI: NÃO VERIFICADO de ponta a ponta, para respeitar o limite de uma única rodada paga. A geração real foi verificada direto em `build_vectorstore` (ação #19) e o caminho da UI com embedding fake (ação #20).
- Caminho de falha da API (chave inválida, timeout): NÃO VERIFICADO com chamada real; pelo código, cai no `st.error` de `app.py:82-83`.
- Instalação do zero em outra máquina: NÃO VERIFICADO (exigiria instalar pacotes); o `--dry-run` no venv atual está consistente.
- Fallback de OCR: não implementado e não exercitado, porque nenhuma página falhou na extração (ação #11), o que está alinhado com a decisão aprovada.

## 10. Handoff para o Agente Executor
Ordem de execução recomendada (BLOQUEANTE > ALTA > MÉDIA > BAIXA):
- [ ] R2-01 - Garantir overlap efetivo de cerca de 40 entre chunks consecutivos (depois da resposta do usuário à dúvida 1; padrão sugerido: `separators=[" ", ""]`) e, se possível, mostrar o overlap médio na aba "1. Chunks"
- [ ] R2-02 - Validar `TOP_K >= 1` e mostrar erros de config com `st.error` + `st.stop()` em vez de traceback
- [ ] R2-03 - Registrar e mostrar na UI as páginas totais e as páginas puladas por falta de texto
- [ ] R2-04 - (SUGESTÃO, só com aprovação do usuário) remover cabeçalho/rodapé antes do split
- [ ] R2-05 - (SUGESTÃO, só com aprovação do usuário) evitar novas chamadas de embedding a cada rerun depois de uma falha
- [ ] R1-04 - (SUGESTÃO pendente da Onda 1, só com aprovação do usuário) mostrar `contexto/` na aba Setup

Restrições para o Executor:
- Não alterar parâmetros definidos na SPEC (chunk 350/40, K=3, modelos) sem aprovação do usuário.
- Não implementar itens marcados como SUGESTÃO sem aprovação do usuário.
- Ao terminar, solicitar nova revisão: `/revisar-onda 2`.
