# viagens

Planeje uma viagem informando **só a quantidade de dias e os locais**. O processo monta o
roteiro, cota os deslocamentos e as estadias e devolve um comparativo de cenários.

## Skills

| Skill | Para que serve |
|---|---|
| `planejar-viagem` | Orquestrador: coleta o mínimo, monta o roteiro e chama as demais |
| `cotar-transporte` | Avião, ônibus e carro alugado (diárias, combustível, pedágios) por trecho |
| `cotar-hospedagem` | Airbnb e Booking por cidade, com datas e hóspedes |
| `comparar-cenarios` | Cruza tudo: totais, valor por pessoa, horas de deslocamento e recomendação |

## Fluxo

```
viagem.json ──plano.py──▶ plano.json ──links_*.py──▶ links de busca preenchidos
                                │
                     pesquisa de preços (web)
                                ▼
                         cotacoes.json ──cenarios.py──▶ comparativo + recomendação
```

## Rodar os scripts na mão

```bash
python3 skills/planejar-viagem/scripts/plano.py exemplos/viagem.json > plano.json
```

```bash
python3 skills/cotar-transporte/scripts/links_transporte.py plano.json
```

```bash
python3 skills/cotar-hospedagem/scripts/links_hospedagem.py plano.json
```

```bash
python3 skills/comparar-cenarios/scripts/cenarios.py exemplos/cotacoes.json
```

> Os valores em `exemplos/cotacoes.json` são ilustrativos, só para mostrar o formato.

## Convenções

- **N dias = N-1 noites.** Noites não fixadas são divididas igualmente entre as cidades.
- Preço nunca é inventado: vem de uma fonte com data, ou é marcado como `"estimado": true`.
- Nada é reservado automaticamente — o relatório entrega os links para você decidir.
