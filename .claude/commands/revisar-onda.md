---
description: Chama o agente revisor (Tech Lead) para revisar uma onda e gerar o documento em revisoes/
argument-hint: <número da onda 1-5>
---

Use o subagente `revisor` para revisar a **Onda $ARGUMENTS** do projeto, seguindo `REVISOR.md`.

Ao receber o resultado:
1. Mostre ao usuário o caminho do documento gerado, o veredito e a contagem de achados por severidade.
2. Liste as dúvidas pendentes para o usuário, se houver.
3. Não comece a corrigir os achados automaticamente: pergunte se o usuário quer acionar o agente executor com o documento de revisão como insumo.
