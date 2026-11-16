---
name: cotar-hospedagem
description: Cota a hospedagem de cada cidade da viagem no Airbnb e no Booking, com as datas de check-in/check-out e número de hóspedes do plano. Use dentro do fluxo de planejar-viagem ou quando o usuário pedir para comparar Airbnb x Booking em uma ou mais cidades.
---

# Cotar hospedagem

Entrada: `plano.json` gerado por `planejar-viagem/scripts/plano.py`.
Saída: bloco `estadias` do `cotacoes.json`.

## 1. Gerar os links de busca

```bash
python3 <pasta-desta-skill>/scripts/links_hospedagem.py plano.json > links_hospedagem.json
```

Os links já levam cidade, check-in, check-out, hóspedes e moeda BRL (Booking ordenado por preço).
Use `"quartos"` no plano se o grupo precisar de mais de um quarto.

## 2. Pesquisar preços

Para cada estadia, em cada plataforma, registre **uma opção representativa**:

- A mais barata com nota ≥ 8,0 (Booking) ou ≥ 4,7 (Airbnb) e pelo menos ~20 avaliações,
  bem localizada (centro ou perto das atrações principais).
- **Preço total** da estadia com taxas (limpeza, serviço, ISS). No Airbnb, sempre o total
  final, não a diária anunciada.
- Nome, nota, link do anúncio e se tem cancelamento grátis.

Se o usuário tiver preferências (quarto privativo, cozinha, piscina, pet), aplique os filtros
e cite-os no relatório.

## 3. Formato no cotacoes.json

```json
{
  "id": "H1", "cidade": "Rio de Janeiro", "checkin": "2026-12-18", "checkout": "2026-12-21", "noites": 3,
  "airbnb":  {"preco_total": 1380, "nome": "Apto 2 quartos em Copacabana", "nota": 4.86,
              "link": "https://…", "cancelamento_gratis": true, "cotado_em": "2026-11-16"},
  "booking": {"preco_total": 1520, "nome": "Hotel X", "nota": 8.6, "link": "https://…",
              "cancelamento_gratis": true, "cotado_em": "2026-11-16"}
}
```

Valores aproximados levam `"estimado": true`. Se uma plataforma não tiver opção na cidade,
omita a chave — o comparador usa a outra e avisa.
