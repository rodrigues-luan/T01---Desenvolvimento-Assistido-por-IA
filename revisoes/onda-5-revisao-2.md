# Revisão - Onda 5 - Iteração 2
**Data:** 2026-11-02 | **Revisor:** Tech Lead (agente revisor) | **Veredito:** APROVADO

## 1. Resumo executivo
Esta é a re-revisão da Onda 5 (Generation), a última onda. O Executor corrigiu os 4 achados aprovados pelo usuário (R5-01 a R5-04) mexendo só em `app.py` e `src/generator.py` (`git diff --stat`: 52 linhas incluídas, 15 removidas). Testei com mock (16 cenários, 0 exceções) e com 1 chamada real ao Claude. Os 4 achados estão resolvidos. A resposta real trouxe "R$ 450.000,00 ... R$ 280.000,00" na mesma linha, e o texto foi para a tela escapado (`R\$`), tanto na mensagem atual quanto no histórico. Fallback, erros 500/503/529 e erro SSE no meio do stream agora mostram mensagens amigáveis, e o texto parcial continua no histórico. Pergunta só com espaços não faz busca nem chamada nas abas 4 e 5. R5-05 foi encerrado pelo usuário. R3-04, R4-01, R4-02 e R5-06 foram descartados por decisão do usuário. Não há achado novo. O único ponto em aberto é a confirmação visual no navegador, que não consegui fazer (seção 9).

## 2. Escopo revisado
- Onda/objetivo segundo a SPEC: "5 - Finalizando, faremos o Generation, onde usarei exatamente a API do claude na versão opus 5.5 para enviar tanto o system prompt que você criará, a pergunta do usuário e os K chunks retornados na etapa anterior." PRD: "precisa trazer sempre os K chunks para conferirmos se a busca semântica funcionou e so depois trazer a resposta".
- Onda e iteração: informadas no pedido (Onda 5, iteração 2). Batem com `revisoes/`, onde só existia `onda-5-revisao-1.md`.
- Respostas do usuário às dúvidas da iteração 1 (literais, repassadas no pedido):
  1. Chunks do histórico em expander fechado atendem ao PRD: "SIM".
  2. SDK `anthropic` direto na geração: "SIM".
  3. A troca de `LLM_MAX_TOKENS` para 16000 no `.env` foi dele: "SIM" (R5-05 encerrado).
  4. Implementar os opcionais R3-04, R4-01, R4-02 e R5-06: "NÃO". Ficam fora do escopo.
  5. Correção de R5-01 a R5-04: "PODE CORRIGIR".
- Arquivos analisados: `app.py` (linhas 264-394), `src/generator.py` (inteiro), `src/config.py`, `.env.example`, `requirements.txt`, `.gitignore`, `README.md` e `git diff` de `app.py` e `src/generator.py`. Do `.env` só conferi `LLM_*` pela config carregada; nenhum segredo foi lido ou copiado.
- Revisão anterior considerada: `revisoes/onda-5-revisao-1.md`.

## 3. O que o revisor fez (rastreabilidade)
| # | Ação | Comando/arquivo | Resultado |
|---|---|---|---|
| 1 | Escopo da mudança | `git status --short`; `git diff --stat`; `ls --time-style=full-iso` | Só `app.py` (10:19:15) e `src/generator.py` (10:18:44) mudaram desde o commit `8ed0062`. `src/ingest.py`, `src/retriever.py`, `src/vectorstore.py` e `src/config.py` estão iguais aos da iteração 1. As correções **ainda não foram commitadas** |
| 2 | Dependências | `.venv/Scripts/python -m pip check` | "No broken requirements found." `requirements.txt` não mudou (`anthropic==2.3.0`) |
| 3 | Tipos do SDK para R5-03 | `anthropic/types/beta/beta_fallback_block.py`, `beta_iterations_usage.py`, `beta_fallback_message_iteration_usage.py`, `beta_usage.py:38`, `lib/streaming/_beta_messages.py:528-531`, `:610-611` | `content_block.to.model` existe. `usage.iterations` é uma lista discriminada por `type`, que inclui `fallback_message`. O acumulador do stream copia `iterations` do `message_delta`. A docstring confirma: "the signal for whether a fallback model served the response is the presence of a `fallback_message` entry in `usage.iterations`" |
| 4 | Erros SSE no SDK para R5-02 | `anthropic/_streaming.py:99-111`; `_client.py:568-602` | Um evento `error` no meio do stream gera `_make_status_error` com o status HTTP da resposta (200). Por isso cai em `APIStatusError` genérico, com `body` = dict do evento. 529 → `OverloadedError`; >= 500 → `InternalServerError` |
| 5 | **AppTest com mock (sem rede)**, 16 cenários | script em scratchpad: `anthropic.Anthropic(max_retries=0, http_client=httpx2.Client(transport=MockTransport))` e `DeterministicFakeEmbedding` no lugar do OpenAI | **0 exceções** em todos os cenários. 16 buscas e 16 chamadas, 1 de cada por pergunta. Detalhes nas linhas #6 a #10 |
| 6 | R5-01 com mock | SSE com `"Cotas: R$ 450.000,00 e R$ 280.000,00."`; pergunta com `"R$ 1 e R$ 2"` | `item["answer"]` guarda o texto cru, com `R$`. O markdown na mensagem atual sai `Cotas: R\$ 450.000,00 e R\$ 280.000,00.`. Depois do rerun, o histórico também mostra `R\$`. As perguntas aparecem como `pergunta ... R\$ 1 e R\$ 2` na aba 5 e na aba 4 (`app.py:305`, `:348`, `:364`) |
| 7 | R5-03 com mock | SSE: texto "PARCIAL-RECUSOU", bloco `fallback` (`to.model=modelo-fallback-teste`), texto "RESPOSTA-FALLBACK", `iterations=[message, fallback_message]` | A tela mostra `PARCIAL-RECUSOU\n\n---\n*O modelo principal recusou; resposta do modelo de fallback \`modelo-fallback-teste\`:*\n\nRESPOSTA-FALLBACK`. A legenda "Respondido pelo modelo de fallback" aparece 1 vez. **Cenário de controle**: `message.model="claude-opus-5-5-20261001"`, diferente de `LLM_MODEL`, mas com `iterations=[message]`. Aqui a legenda de fallback **não** aparece. Ou seja, o sinal deixou de ser a comparação de `model` |
| 8 | R5-02 com mock: erro no meio do stream | SSE com texto parcial + evento `error` do tipo `overloaded_error`, `api_error` ou `invalid_request_error` | `overloaded_error` e `api_error` → "A API da Anthropic está sobrecarregada ou instável no momento. Tente novamente em instantes.", e o texto parcial fica em `item["answer"]` ("TEXTO-PARCIAL ", "PARCIAL2 "). `invalid_request_error` → "Erro da API da Anthropic (200): algo invalido": usa a mensagem do corpo, não o dict cru. Depois do rerun, o histórico mostra o texto parcial e, abaixo, o erro |
| 9 | R5-02 com mock: erros HTTP | 500, 503, 529 | Os três → mensagem amigável de API instável, sem `{'type': ...}` |
| 10 | Regressão dos outros erros (mock) | 401, 403, 404, 429, 400, `ReadTimeout`, `ConnectError` | Mesmas mensagens da iteração 1 (chave inválida, sem permissão, modelo não encontrado, limite, timeout, sem conexão). 400 continua como "Requisição inválida...: Error code: 400 - {...}", igual à iteração 1, porque o 400 não fazia parte do R5-02. Os 3 chunks continuam na tela em todos os casos |
| 11 | R5-04 com mock | `"   "` em `chat_input` (aba 5) e em `busca_input` (aba 4) | As duas abas: **+0 buscas, +0 chamadas ao Claude**, `chat_hist` e `busca_hist` sem item novo, 0 exceções |
| 12 | **Rodada real** (orçamento: 1 indexação + até 3 buscas + até 2 Claude) | AppTest com as chaves do `.env` e contadores em `build_vectorstore`, `search` e `stream_answer` | **Usado: 1 indexação (49 chunks), 1 busca, 1 chamada ao Claude.** Config: `claude-opus-5-5`, max_tokens 16000, effort medium, K=3 |
| 13 | Resultado real | pergunta "cotas AE Sênior e Pleno em uma frase" | Chunks #36, #34 (Política de Vendas p.1) e #33 (Contrato de Trabalho p.2). `stop_reason=end_turn`, `model=claude-opus-5-5`, 3334 tokens de entrada, 322 de saída (193 de raciocínio). `iterations` = `['message']`, `used_fallback=False`. Resposta crua: "A cota mínima em novo ARR é de **R$ 450.000,00 para AE Sênior** e de **R$ 280.000,00 trimestrais para AE Pleno** [Política de Vendas Xperiun, p. 1]." Os dois `R$` estão na **mesma linha**, exatamente o cenário de risco do R5-01. Na tela saiu `**R\$ 450.000,00 ...** e de **R\$ 280.000,00 ...**`, e no histórico depois do rerun também. A resposta ainda avisa que o trecho só chama de trimestral a cota do Pleno. Valores iguais aos conferidos na iteração 1. Não inventou nada |
| 14 | Subida real do servidor | `streamlit run app.py --server.port 8597 --server.headless true` + `/_stcore/health` | `ok`. Processo (PID 7612) encerrado com `taskkill /T`, e a porta 8597 ficou livre. A porta 8501 do usuário (PID 31080) **não foi tocada** e continua escutando |
| 15 | Segredos / versionamento | `grep -rn "sk-[A-Za-z0-9_-]{20,}"` fora do `.venv`; `git ls-files`; `git check-ignore -v .env` | Nenhuma chave no código. `.env` ignorado (`.gitignore:1`) e fora do índice do git. `.env.example` sem valores secretos |
| 16 | Regressão das Ondas 1 a 4 | AppTest (#5) com as abas 1 a 4 renderizadas; timestamps (#1) | 0 exceções no primeiro run, com as 6 abas. A aba 4 continua buscando, e sua única mudança é `.strip()` + `md_safe` na pergunta. Ingestão, chunking (350/40), embedding e retriever não mudaram desde a iteração 1, que já tinha verificado 49 chunks, máximo de 350 e overlap médio de 36,0 |

## 4. Checklist da onda
| Critério (fonte) | Status | Evidência |
|---|---|---|
| API da Anthropic com Opus 5.5, `claude-opus-5-5`, via env (SPEC onda 5) | OK | `src/config.py:43`; `src/generator.py:62-63`; ação #13 (`model=claude-opus-5-5`) |
| Envia system prompt + pergunta + K chunks (SPEC onda 5) | OK | `src/generator.py:36-43`, `:66-67` (sem mudança desde a iteração 1) |
| System prompt manda responder só com os chunks e dizer quando não está nos documentos | OK | `src/generator.py:14-16`; ação #13 (aponta que o período da cota do Sênior não está no trecho) |
| PRD: primeiro os K chunks, depois a resposta | OK | `app.py:371-387`. Histórico: expander fechado antes da resposta (`app.py:350-354`), aprovado pelo usuário ("SIM") |
| Erro de API (chave ausente, timeout) com mensagem clara | OK | `src/generator.py:88-113`; ações #8 a #10 |
| Responde aos 4 temas do PRD | OK | Verificado na iteração 1 (4 perguntas reais). Nesta iteração, 1 pergunta real do tema time de receita (ação #13) |
| Valores `R$` exibidos corretamente (R5-01) | OK (visual NÃO VERIFICADO) | `app.py:264-266`, `:305`, `:348`, `:354`, `:364`, `:378-382`; ações #6 e #13 |
| Fallback: separação e sinal oficial (R5-03) | OK | `src/generator.py:72-85`; `app.py:318`; ação #7 |
| Pergunta vazia não gera custo (R5-04) | OK | `app.py:296`, `:361`; ação #11 |
| Geração com SDK `anthropic` direto (decisão do usuário) | OK | Usuário: "SIM". LangChain continua no chunking, nos embeddings e no Chroma |
| `.env.example` com todas as variáveis, sem valores reais | OK | `.env.example` (11 variáveis, chaves vazias). Nenhuma variável nova nesta iteração |
| Parâmetros da SPEC inalterados (350/40, K=3, modelos) | OK | `src/config.py` sem mudança (ação #1); ação #12 (K=3, `claude-opus-5-5`) |
| Sem regressão das Ondas 1 a 4 | OK | Ação #16 |
| App sobe e há instrução de execução | OK | Ação #14; `README.md` ("Como rodar (Windows)") |
| Segredos fora do código / `.env` no `.gitignore` | OK | Ação #15 |
| Nenhum dado inventado | OK | Ação #13 |

## 5. Status dos achados anteriores (se re-revisão)
| ID | Status | Evidência |
|---|---|---|
| R5-01 (MÉDIA) `$` vira LaTeX | RESOLVIDO | `md_safe` em `app.py:264-266`. Aplicado à resposta em streaming: o gerador `_render` acumula o texto cru e emite o texto escapado (`app.py:378-382`, `:387`). Também aplicado ao histórico (`:354`) e às perguntas das abas 4 e 5 (`:305`, `:348`, `:364`). `item["answer"]` guarda o texto cru, então nada é escapado duas vezes. Mock (#6) e chamada real com dois `R$` na mesma linha (#13): `R\$` na mensagem atual e no histórico |
| R5-02 (BAIXA) erros brutos e parcial perdido | RESOLVIDO | `src/generator.py:104-112` (`OverloadedError`/`InternalServerError` e `APIStatusError` com `body.error.type` igual a `overloaded_error` ou `api_error`) e `:116` (`UNSTABLE_MESSAGE`). O texto parcial fica no histórico (`app.py:381`, `:353-356`). Ações #8 e #9 cumprem o critério de aceite: 529 e "SSE overloaded" mostram a mensagem em português, os outros cenários continuam iguais e há 0 exceções |
| R5-03 (BAIXA) fallback junta textos | RESOLVIDO | `src/generator.py:72-76` itera os eventos e emite `FALLBACK_SEPARATOR` (`:80`) no `content_block_start` do tipo `fallback`. `used_fallback` (`:83-85`) olha `usage.iterations`, e `app.py:318` o usa. Ação #7, com cenário de controle |
| R5-04 (BAIXA) pergunta só com espaços | RESOLVIDO | `app.py:296` (aba 4) e `:361` (aba 5). Ação #11 |
| R5-05 (BAIXA, usuário) `LLM_MAX_TOKENS` | ENCERRADO (usuário: "SIM") | `config.LLM_MAX_TOKENS = 16000` (ação #12) |
| R5-06 (SUGESTÃO) tokens de raciocínio | DESCARTADO por decisão do usuário ("NÃO") | Não implementado (`app.py:322-325`), como esperado |
| R4-01 (BAIXA, opcional) | DESCARTADO por decisão do usuário ("NÃO") | `src/retriever.py` sem mudança |
| R4-02 (SUGESTÃO) | DESCARTADO por decisão do usuário ("NÃO") | `show_retrieved` (`app.py:269-278`) sem botão, como esperado |
| R3-04 (BAIXA, opcional) | DESCARTADO por decisão do usuário ("NÃO") | `src/ingest.py` sem mudança (timestamp 02:19:58) |
| Dúvida: histórico com expander fechado | RESPONDIDA ("SIM", atende ao PRD) | `app.py:350-352` mantido |
| Dúvida: SDK `anthropic` direto | RESPONDIDA ("SIM") | `src/generator.py:4` mantido |

## 6. Achados (o que precisa mudar)
Nenhum achado novo nesta iteração.

Observações que **não** são achados (só registro):
- O erro 400 continua mostrando o texto do SDK com o dict (`Requisição inválida...: Error code: 400 - {...}`, ação #10). Isso já era assim na iteração 1, ficou fora do escopo do R5-02 e o usuário não pediu mudança.
- As correções estão no working tree, mas ainda não foram commitadas (`git status`: `M app.py`, `M src/generator.py`). Commitar é decisão do usuário.

## 7. Pontos positivos
- As correções são pequenas e no lugar certo: só `app.py` e `src/generator.py`. Configuração, chunking, embedding e retriever não foram tocados.
- R5-01 guarda o texto cru e escapa só na exibição, então nada é escapado duas vezes. O mesmo helper protege as perguntas exibidas nas abas 4 e 5.
- R5-02 vai além do mínimo pedido: trata o erro SSE de status 200 pelo `body.error.type` e, para outros tipos de erro, mostra a mensagem do corpo em vez do dict cru (ação #8). Também preserva o texto parcial no histórico.
- R5-03 segue o sinal oficial do SDK (`fallback_message` em `usage.iterations`). O cenário de controle mostra que um `model` com alias diferente não gera mais falso positivo de fallback (ação #7).
- O orçamento foi respeitado e o resultado real confirmou o cenário de risco: os dois `R$` na mesma linha saíram escapados.

## 8. Dúvidas para o usuário (bloqueiam decisão, não inventar)
- Nenhuma. Todas as dúvidas da iteração 1 foram respondidas (seção 5).

## 9. Informações não encontradas / não verificadas
- **Renderização visual no navegador (R5-01):** NÃO VERIFICADA. Não há ferramenta de automação de navegador no ambiente (`playwright` não está instalado, e não instalei pacotes). A evidência é o markdown enviado ao frontend com `R\$` (ações #6 e #13). Pelo CommonMark, `\$` é um escape de pontuação ASCII e deve aparecer como `$` literal, sem abrir fórmula. Para confirmar, o usuário pode abrir a aba 5 na própria 8501 e fazer uma pergunta sobre as cotas.
- **Limitação teórica do `md_safe`:** se o modelo escrever `R$` dentro de um trecho de código (entre crases), o escape apareceria como `\$` literal, porque o Markdown não processa escapes dentro de code spans. Não aconteceu em nenhuma resposta real (5 respostas, nas iterações 1 e 2). Não é achado, só registro.
- **Fallback e erro SSE com a API real:** NÃO VERIFICADOS com rede. Não é possível provocar recusa ou sobrecarga legítimas dentro do orçamento e do escopo. Foram cobertos com SSE simulado no formato dos tipos do SDK 2.3.0 (ações #3, #4, #7 e #8).
- **Penalidades de SLA:** a tabela continua cortada no próprio PDF (registrado na iteração 1). É limitação da fonte, não do código.

## 10. Handoff para o Agente Executor
Ordem de execução recomendada (BLOQUEANTE > ALTA > MÉDIA > BAIXA):
- Nenhuma ação pendente. A Onda 5, a final, está APROVADA.
- R3-04, R4-01, R4-02 e R5-06 foram descartados por decisão do usuário. **Não implementar.**

Restrições para o Executor:
- Não alterar parâmetros definidos na SPEC (chunk 350/40, K=3, modelos) sem aprovação do usuário.
- Não implementar itens marcados como SUGESTÃO sem aprovação do usuário.
- Não editar o `.env` do usuário.
- Commitar as correções (`app.py`, `src/generator.py`) só se o usuário pedir.
- Ao terminar, solicitar nova revisão: `/revisar-onda <N>` (só se houver nova mudança).
