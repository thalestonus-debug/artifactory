---
name: planejar-viagem
description: Planeja uma viagem completa a partir só da quantidade de dias e dos locais, cotando cenários de transporte (avião, ônibus, carro alugado) e de hospedagem (Airbnb, Booking) e entregando um comparativo com totais por pessoa. Use quando o usuário pedir para planejar, orçar ou cotar uma viagem, roteiro, férias ou "quanto custa ir para X".
---

# Planejar viagem (orquestrador)

Esta skill conduz o processo de ponta a ponta. Ela chama, em ordem, as skills
`cotar-transporte`, `cotar-hospedagem` e `comparar-cenarios` deste mesmo plugin.
Os scripts ficam em `scripts/` dentro da pasta de cada skill e usam só Python 3 padrão.

## 1. Coletar o mínimo

O usuário só precisa informar **quantidade de dias** e **locais**. Para o resto, use
padrões e diga quais assumiu (sem travar a conversa com perguntas):

| Campo | Padrão se não informado |
|---|---|
| `origem` | Pergunte **uma vez** — é o único dado indispensável além de dias e locais |
| `data_inicio` | Próxima sexta-feira com pelo menos 30 dias de antecedência |
| `viajantes` | 2 adultos |
| `retornar_origem` | `true` |
| noites por cidade | Divididas igualmente (o script faz isso) |

Convenção: **N dias = N-1 noites** (chega no dia 1, volta no dia N).

## 2. Montar o plano

Salve o pedido em `viagem.json` (pasta de trabalho do usuário ou scratchpad) e rode:

```bash
python3 <pasta-desta-skill>/scripts/plano.py viagem.json > plano.json
```

Exemplo de entrada: `../../exemplos/viagem.json`. A saída tem `trechos` (T1, T2…) e
`estadias` (H1, H2…) com datas. Se fizer sentido, acrescente ao `plano.json` os
códigos `iata` e `uf` das cidades — melhora os links gerados nas próximas etapas.

## 3. Cotar

1. Siga a skill **cotar-transporte** para cada trecho (avião, ônibus) e para o carro alugado.
2. Siga a skill **cotar-hospedagem** para cada estadia (Airbnb e Booking).

Ambas preenchem um único `cotacoes.json` (formato em `../../exemplos/cotacoes.json`).

## 4. Comparar e entregar

Siga a skill **comparar-cenarios** para gerar o comparativo e então entregue o relatório
no formato de `templates/relatorio.md`:

1. Resumo da viagem (datas, cidades, noites, viajantes) e premissas assumidas.
2. Recomendação: o cenário **mais barato**, o **mais rápido** e o **melhor custo-benefício**,
   com uma frase justificando cada um.
3. Tabelas geradas pelo `cenarios.py`.
4. Links de busca já preenchidos, para o usuário conferir e reservar.
5. Avisos: preços que são estimativa vs. verificados, data da cotação, trechos sem opção.

## Regras

- **Nunca invente preço.** Todo valor vem de uma fonte consultada (busca na web, página da
  empresa) ou é marcado como `"estimado": true` com a base da estimativa.
- Registre a fonte e a data de cada cotação. Preços de viagem mudam rápido.
- Não faça reservas nem compras: entregue os links para o usuário decidir.
- Se não houver acesso à web, gere o plano e os links mesmo assim e explique que os preços
  precisam ser preenchidos (ou peça ao usuário para colar os valores que encontrar).
