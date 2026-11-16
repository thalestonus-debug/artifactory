---
name: cotar-transporte
description: Cota os deslocamentos de uma viagem em três modais — avião, ônibus e carro alugado (diárias, combustível, pedágios) — para cada trecho do plano. Use dentro do fluxo de planejar-viagem ou quando o usuário pedir para comparar avião x ônibus x carro entre cidades.
---

# Cotar transporte

Entrada: `plano.json` gerado por `planejar-viagem/scripts/plano.py`.
Saída: blocos `trechos` e `aluguel_carro` do `cotacoes.json`.

## 1. Gerar os links de busca

```bash
python3 <pasta-desta-skill>/scripts/links_transporte.py plano.json > links_transporte.json
```

Para cada trecho saem links do Google Flights (e Kayak, se houver `iata` no plano),
busca de ônibus (e ClickBus, se houver `uf`) e a rota no Google Maps. Também sai um link
de aluguel de carro cobrindo a viagem toda.

## 2. Pesquisar preços

Use as ferramentas de busca/web disponíveis (WebSearch, WebFetch, navegador). Para cada trecho:

**Avião** — Google Flights, Skyscanner, Kayak, sites das companhias (LATAM, GOL, Azul).
- Registre o menor preço por pessoa **com bagagem de mão**, duração porta a porta estimada
  (voo + ~2 h de aeroporto + deslocamento até o aeroporto).
- Use `extras_por_pessoa` para bagagem despachada e transfer até o aeroporto.
- Se não houver aeroporto na cidade, omita `aviao` no trecho (o comparador trata isso).

**Ônibus** — ClickBus, Buser, Guichê Virtual, sites das viações.
- Menor preço por pessoa e duração da viagem.

**Carro** — distância e tempo pelo Google Maps; pedágios por Google Maps, QualP ou
sites das concessionárias. Preencha `carro` em **todos** os trechos.

**Aluguel do carro** (bloco único) — Localiza, Movida, Unidas, Rentcars, Kayak:
- `diaria` da categoria econômica com proteção básica, `dias` = dias da viagem,
  `taxas` (taxa de retorno em outra cidade, condutor adicional etc.).
- `consumo_km_l` ≈ 11 (econômico, estrada) se não houver dado melhor; `preco_combustivel`
  = média da gasolina na região (ANP) — marque como estimativa.
- `estacionamento_dia` se os hotéis/cidades cobrarem.

## 3. Formato no cotacoes.json

```json
{
  "id": "T1", "de": "São Paulo", "para": "Rio de Janeiro", "data": "2026-12-18",
  "aviao":  {"preco_por_pessoa": 389.9, "extras_por_pessoa": 80, "duracao_h": 4.0,
             "fonte": "Google Flights", "cotado_em": "2026-11-16"},
  "onibus": {"preco_por_pessoa": 149.9, "duracao_h": 6.5, "fonte": "ClickBus", "cotado_em": "2026-11-16"},
  "carro":  {"distancia_km": 435, "duracao_h": 6.0, "pedagio": 92.3, "fonte": "Google Maps"}
}
```

Valores aproximados ou inferidos levam `"estimado": true`. Pode-se usar `preco_total`
no lugar de `preco_por_pessoa` quando o site mostrar só o total.
