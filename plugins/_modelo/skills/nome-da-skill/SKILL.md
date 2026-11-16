---
name: nome-da-skill
description: O que esta skill faz e QUANDO o Claude deve usá-la (frases que o usuário diria). Seja específico — é isto que faz a skill ser acionada.
---

# Nome da skill

## Entrada
O que o usuário precisa informar e quais padrões assumir quando não informar.

## Passo a passo
1. …
2. Scripts determinísticos ficam em `scripts/` (Python 3, só biblioteca padrão):
   `python3 <pasta-desta-skill>/scripts/exemplo.py entrada.json`
3. …

## Saída
Formato da entrega (tabela, relatório, arquivo).

## Regras
- O que nunca fazer (ex.: inventar dados, executar ações irreversíveis sem confirmar).
