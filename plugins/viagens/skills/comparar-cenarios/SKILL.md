---
name: comparar-cenarios
description: Consolida cotações de transporte e hospedagem de uma viagem e monta o comparativo de cenários (avião, ônibus, carro alugado, misto x Airbnb, Booking) com total, valor por pessoa e horas de deslocamento. Use depois das cotações, no fluxo de planejar-viagem, ou quando o usuário trouxer preços e quiser saber qual combinação compensa.
---

# Comparar cenários

## Rodar

```bash
python3 <pasta-desta-skill>/scripts/cenarios.py cotacoes.json          # tabelas em Markdown
python3 <pasta-desta-skill>/scripts/cenarios.py cotacoes.json --json   # dados para outros usos
```

Exemplo completo de entrada: `../../exemplos/cotacoes.json`.

## Cenários calculados

**Transporte**
- **Avião** — todos os trechos de avião (onde não há voo, usa ônibus e avisa).
- **Ônibus** — todos de ônibus (onde não há, usa avião e avisa).
- **Carro alugado** — `diaria × dias + taxas + combustível (km ÷ consumo × preço) + pedágios + estacionamento`.
- **Misto** — em cada trecho, o mais barato entre avião e ônibus.

**Hospedagem**: Airbnb, Booking e "mais barato por cidade".

O script cruza tudo e ordena as combinações do total mais barato para o mais caro.

## Como interpretar e recomendar

Depois das tabelas, escreva em linguagem simples:

1. **Mais barato** — primeira linha das combinações.
2. **Mais rápido** — menor tempo em deslocamento; diga quanto custa a mais que o mais barato.
3. **Custo-benefício** — sua recomendação, pesando: diferença de preço vs. horas economizadas,
   carro valer mais com 3+ viajantes ou cidades sem rodoviária/aeroporto, cancelamento grátis,
   e cansaço de trechos noturnos longos.

Sempre repita os avisos do script e destaque valores marcados como estimados.
