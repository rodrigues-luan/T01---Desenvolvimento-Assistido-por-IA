# Revisão - Onda 1 - Iteração 1
**Data:** 2026-10-31 | **Revisor:** Tech Lead (agente revisor) | **Veredito:** APROVADO

## 1. Resumo executivo
A Onda 1 entregou a plataforma base: venv isolado (Python 3.13.1), `requirements.txt` com LangChain, Streamlit, Chroma e PyMuPDF, todos instalados e importáveis, além de `.env.example` completo, `.gitignore` protegendo `.env` e configuração central em `src/config.py`. O app Streamlit sobe sem erro (AppTest sem exceções; servidor headless respondeu HTTP 200) e já tem as abas por etapa do RAG, com a sidebar mostrando os parâmetros da SPEC. Nenhum achado bloqueante ou alto. O principal risco para as próximas ondas é a falta de reprodutibilidade, porque as dependências não estão fixadas (R1-01).

## 2. Escopo revisado
- Onda/objetivo segundo a SPEC: "1 - Desenvolver a plataforma em Python usando tanto o Langchain para o RAG quando o Streamlit para visualizar cada etapa do RAG. Utilize a versão 3.11+ do python e isole o ambente para evitar conflitos" (`SPEC.md:8`), mais "Coloque todas as variaveis no .env.example" (`SPEC.md:14`).
- Onda identificada: informada no pedido (Onda 1, iteração 1). O pedido é confirmado pelo código: as abas das ondas 2 a 5 estão marcadas como "Em construção" (`app.py:34-41`) e `revisoes/` estava vazia.
- Arquivos analisados: `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `src/__init__.py`, `src/config.py`, `app.py`; também `AGENTS.md`, `PRD.md`, `SPEC.md`, `REVISOR.md`, `docs/` (listagem), `contexto/contexto.txt` (início), `.venv/pyvenv.cfg`.
- Revisão anterior considerada: nenhuma.

## 3. O que o revisor fez (rastreabilidade)
| # | Ação | Comando/arquivo | Resultado |
|---|---|---|---|
| 1 | Verificou a versão do Python do venv | `.venv/Scripts/python --version` | 3.13.1, OK (>= 3.11) |
| 2 | Verificou o isolamento do venv | `.venv/pyvenv.cfg` | `include-system-site-packages = false`, OK |
| 3 | Listou as versões instaladas dos pacotes do requirements | `importlib.metadata.version(...)` | streamlit 1.66.1, langchain 1.4.7, langchain-core 1.7.3, langchain-community 0.4.2, langchain-text-splitters 1.1.3, langchain-openai 1.7.3, langchain-anthropic 1.7.7, langchain-chroma 1.1.0, chromadb 1.5.9, pymupdf 2.0, python-dotenv 1.2.4 |
| 4 | Importou todas as libs | `import streamlit, dotenv, langchain, ..., chromadb, fitz` | OK. Avisos: `DeprecationWarning` de que o langchain-community está sendo descontinuado ("being sunset") e `FutureWarning` de que a API `fitz` está deprecada |
| 5 | Verificou a consistência das dependências | `pip check` | "No broken requirements found." |
| 6 | Carregou a config sem `.env` | `from src import config` | 350 / 40 / text-embedding-3-small / 3 / claude-opus-5-5 / 1024; os 3 PDFs foram listados |
| 7 | Executou o app sem servidor | `streamlit.testing.v1.AppTest.from_file('app.py').run()` | 0 exceções; 4 abas; a sidebar mostra os parâmetros; o Setup lista os 3 PDFs |
| 8 | Subiu o servidor real em modo headless por cerca de 25 s | `streamlit run app.py --server.headless true --server.port 8599` | `/_stcore/health` 200, `/` 200 |
| 9 | Procurou segredos hardcoded | `grep -E "sk-|api_key\s*=\s*'..."` em app.py, src, README, .env.example, requirements | Nenhuma ocorrência |
| 10 | Testou a robustez da config | `CHUNK_SIZE= python -c "from src import config"` | `ValueError: invalid literal for int()` (ver R1-02) |
| 11 | Testou a validação de parâmetros | `CHUNK_SIZE=30 CHUNK_OVERLAP=40` | Aceito sem erro (ver R1-02) |
| 12 | Conferiu a presença do `.env` | `ls .env` | Ausente, o que é esperado (o usuário vai preencher) |

## 4. Checklist da onda
| Critério (fonte) | Status | Evidência |
|---|---|---|
| Python 3.11+ com ambiente isolado (SPEC onda 1) | OK | Python 3.13.1; `pyvenv.cfg` com `include-system-site-packages = false` |
| Dependências declaradas (REVISOR transversal) | OK (com ressalva R1-01) | `requirements.txt:1-11`, sem versões fixadas |
| LangChain e Streamlit instalados e importáveis (SPEC onda 1) | OK | Ação #4 |
| App Streamlit sobe (REVISOR transversal) | OK | Ações #7 e #8 |
| Estrutura para exibir as etapas do RAG (SPEC onda 1 / objetivo) | OK | `app.py:22-24`: abas "0. Setup", "1. Chunks (Retriever)", "2. Busca (Augmented)", "3. Chat (Generation)" |
| Plataforma mostra a etapa atual desde a etapa 0 (SPEC objetivo) | OK | A aba Setup lista os PDFs de `docs/` (`app.py:26-32`); a sidebar mostra os parâmetros (`app.py:11-20`) |
| `.env.example` com todas as variáveis usadas no código, sem valores reais (SPEC:14) | OK | As 10 chaves de `src/config.py:10-24` estão em `.env.example:2-21`; as credenciais estão vazias |
| `.env` não versionado; nenhuma chave hardcoded | OK | `.gitignore:1`; ação #9; a UI só mostra "configurada/ausente", nunca o valor (`app.py:19-20`) |
| Parâmetros vêm de config/env | OK | `src/config.py:16-24`, com padrões iguais aos da SPEC (350/40, text-embedding-3-small, K=3, claude-opus-5-5) |
| Instrução de execução | OK | `README.md:5-12` |
| Nenhum dado inventado sobre a Xperiun | OK | A UI só exibe os nomes e tamanhos dos arquivos reais de `docs/` e os textos de status das ondas |
| Ondas anteriores sem regressão | N/A | Primeira onda |

## 5. Status dos achados anteriores (se re-revisão)
| ID | Status | Evidência |
|---|---|---|
| - | N/A | Primeira revisão |

## 6. Achados (o que precisa mudar)

### [R1-01] Dependências sem versão fixada - MÉDIA
- **Onde:** `requirements.txt:1-11`
- **Problema:** nenhum pacote tem versão fixada (ex.: `langchain`, `chromadb`, `streamlit`). Uma reinstalação futura, ou em outra máquina, pode puxar versões com breaking changes. O ecossistema LangChain/Chroma muda de API com frequência, e o próprio langchain-community já emite aviso de descontinuação (ação #4). Hoje o ambiente está consistente (`pip check` OK), mas não é reproduzível.
- **Regra violada:** REVISOR transversal, "dependências declaradas" e "ondas anteriores continuam funcionando (sem regressão)". É um risco de manutenibilidade, não uma violação explícita da SPEC.
- **Ação para o Executor:** fixar no `requirements.txt` as versões já instaladas e validadas no `.venv` (ver a ação #3 desta revisão), com `==` ou `~=`. Exemplo: `streamlit==1.66.1`, `langchain==1.4.7`, `langchain-core==1.7.3`, `langchain-text-splitters==1.1.3`, `langchain-openai==1.7.3`, `langchain-anthropic==1.7.7`, `langchain-chroma==1.1.0`, `chromadb==1.5.9`, `pymupdf==2.0`, `python-dotenv==1.2.4` (e `langchain-community==0.4.2`, se for mantido; ver R1-03).
- **Critério de aceite:** todas as linhas do `requirements.txt` têm versão; `.venv/Scripts/python -m pip install -r requirements.txt --dry-run` não propõe mudanças no ambiente atual, e `pip check` continua OK.

### [R1-02] Config quebra com variável vazia e não valida parâmetros - BAIXA
- **Onde:** `src/config.py:16-17`, `src/config.py:21`, `src/config.py:24`
- **Problema:** `int(os.getenv("CHUNK_SIZE", "350"))` só usa o padrão quando a variável não existe. Se ela existir vazia (ex.: o usuário apaga o valor no `.env`), o app inteiro cai com `ValueError: invalid literal for int() with base 10: ''` (ação #10). Também não há validação: `CHUNK_SIZE=30` com `CHUNK_OVERLAP=40` é aceito (ação #11), e isso vai gerar erro ou comportamento inesperado no splitter da Onda 2.
- **Regra violada:** nenhuma regra explícita da SPEC. É robustez de configuração, que vai pesar na Onda 2 (chunk 350/40) e na Onda 4 (K configurável).
- **Ação para o Executor:** criar um helper (ex.: `_int_env(nome, padrão)`) que trate string vazia como ausente e dê uma mensagem clara quando o valor for inválido. Validar `0 <= CHUNK_OVERLAP < CHUNK_SIZE` e `TOP_K >= 1`, e mostrar o erro de forma amigável no Streamlit (`st.error`) em vez de traceback.
- **Critério de aceite:** `CHUNK_SIZE= python -c "from src import config; print(config.CHUNK_SIZE)"` imprime 350; `CHUNK_SIZE=30 CHUNK_OVERLAP=40` produz uma mensagem de erro clara; os padrões continuam 350/40/3.

### [R1-03] Dependência `langchain-community` em descontinuação e uso da API `fitz` deprecada - BAIXA
- **Onde:** `requirements.txt:5`; aviso ao importar `fitz` (ação #4)
- **Problema:** ao importar `langchain_community`, a biblioteca emite `DeprecationWarning` dizendo que está "being sunset and is no longer actively maintained". O PyMuPDF 2.0 avisa que "The `fitz` API is deprecated [...] Use `import pymupdf` instead". O código da Onda 1 ainda não usa nenhum dos dois, mas a Onda 2 (extração de PDF) vai usar.
- **Regra violada:** nenhuma regra explícita. É um alerta preventivo para a Onda 2.
- **Ação para o Executor:** na Onda 2, usar `import pymupdf` (não `fitz`) para a extração, conforme a decisão aprovada de usar PyMuPDF primeiro. Avaliar se `langchain-community` é realmente necessário: se a extração for feita direto com PyMuPDF e o split com `langchain-text-splitters`, remova-o do `requirements.txt`. Se for mantido, justifique no README.
- **Critério de aceite:** na revisão da Onda 2, nenhum `import fitz` no código, e `langchain-community` removido ou com uso justificado.

### [R1-04] Mostrar a pasta `contexto/` e o papel dela no Setup - SUGESTÃO
- **Onde:** `app.py:26-32`
- **Problema:** a aba Setup mostra apenas `docs/`. Pela decisão aprovada, `contexto/` não entra no RAG e serve só de base para o system prompt. Exibir isso na aba Setup tornaria esse papel visível na plataforma, em linha com o objetivo da SPEC de "visualizar todas as informações na plataforma".
- **Regra violada:** nenhuma (fora do escopo obrigatório).
- **Ação para o Executor:** só com aprovação do usuário: na aba Setup, listar os arquivos de `config.CONTEXTO_DIR` com a legenda "usado apenas no system prompt (Onda 5), não indexado no RAG".
- **Critério de aceite:** a aba Setup mostra `contexto.txt` com essa legenda.

## 7. Pontos positivos
- Configuração centralizada em `src/config.py`, com padrões idênticos aos da SPEC e caminhos resolvidos a partir de `ROOT_DIR` (funciona independentemente do diretório de execução).
- `.env.example` cobre 100% das variáveis lidas no código, sem valores de credencial.
- A UI nunca exibe o valor das chaves, só se estão configuradas ou ausentes (`app.py:19-20`).
- As abas já estão mapeadas para as etapas da SPEC, com indicação da onda em que cada uma será entregue, o que atende o requisito "desde a etapa 0 eu quero visualizar".
- O aviso da PoC sobre acesso de todos os usuários a todos os documentos está explícito na UI (`app.py:9`), como foi decidido.
- `.gitignore` cobre `.env`, `.venv/`, `__pycache__/` e `.streamlit/secrets.toml`.

## 8. Dúvidas para o usuário (bloqueiam decisão, não inventar)
- Nenhuma. As decisões que estavam em aberto (K=3 configurável, Chroma em memória com `st.cache_resource`, `contexto/` fora do RAG, venv + requirements, acesso total na PoC, PyMuPDF antes de OCR, git só ao final) já foram aprovadas pelo usuário.

## 9. Informações não encontradas / não verificadas
- Chamadas reais às APIs da OpenAI e da Anthropic: NÃO VERIFICADO, requer credencial (não há `.env`, o que é esperado). Também não fazem parte do escopo da Onda 1.
- Renderização visual no navegador: NÃO VERIFICADO de forma visual. Foi verificada por AppTest (árvore de elementos) e pelo health check HTTP do servidor headless.
- Execução em outra máquina a partir do zero (`python -m venv` + `pip install -r requirements.txt`): NÃO VERIFICADO, porque exigiria instalar pacotes. Ver R1-01.

## 10. Handoff para o Agente Executor
Ordem de execução recomendada (BLOQUEANTE > ALTA > MÉDIA > BAIXA):
- [ ] R1-01 - Fixar no `requirements.txt` as versões instaladas no `.venv`
- [ ] R1-02 - Tratar variável vazia ou inválida em `src/config.py` e validar `CHUNK_OVERLAP < CHUNK_SIZE` e `TOP_K >= 1`
- [ ] R1-03 - Na Onda 2, usar `import pymupdf` e reavaliar a necessidade de `langchain-community`
- [ ] R1-04 - (SUGESTÃO, só com aprovação do usuário) mostrar `contexto/` e o papel dela na aba Setup

Restrições para o Executor:
- Não alterar parâmetros definidos na SPEC (chunk 350/40, K=3, modelos) sem aprovação do usuário.
- Não implementar itens marcados como SUGESTÃO sem aprovação do usuário.
- Ao terminar, solicitar nova revisão: `/revisar-onda <N>`.
