#!/usr/bin/env python3
"""Gera links de busca já preenchidos (datas, cidade, hóspedes) no Airbnb e no Booking
para cada estadia do plano.

Entrada: o JSON produzido por planejar-viagem/scripts/plano.py (arquivo ou "-" para stdin).
Campo opcional no plano: "quartos" (padrão: 1) — usado no Booking.

Uso:
    python3 links_hospedagem.py plano.json
"""
from __future__ import annotations

import json
import sys
import unicodedata
from urllib.parse import quote, urlencode


def slug_airbnb(cidade: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", cidade).encode("ascii", "ignore").decode()
    return quote("-".join(sem_acento.split()))


def links_estadia(estadia: dict, viajantes: int, quartos: int) -> dict:
    cidade, ci, co = estadia["cidade"], estadia["checkin"], estadia["checkout"]
    airbnb = f"https://www.airbnb.com.br/s/{slug_airbnb(cidade)}/homes?" + urlencode(
        {"checkin": ci, "checkout": co, "adults": viajantes, "currency": "BRL"}
    )
    booking = "https://www.booking.com/searchresults.pt-br.html?" + urlencode(
        {
            "ss": cidade,
            "checkin": ci,
            "checkout": co,
            "group_adults": viajantes,
            "no_rooms": quartos,
            "group_children": 0,
            "selected_currency": "BRL",
            "order": "price",
        }
    )
    return {
        "id": estadia["id"],
        "cidade": cidade,
        "checkin": ci,
        "checkout": co,
        "noites": estadia["noites"],
        "airbnb": airbnb,
        "booking": booking,
    }


def gerar(plano: dict) -> dict:
    viajantes = int(plano.get("viajantes", 1))
    quartos = int(plano.get("quartos", 1))
    return {"estadias": [links_estadia(e, viajantes, quartos) for e in plano["estadias"]]}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    fonte = sys.stdin if argv[1] == "-" else open(argv[1], encoding="utf-8")
    with fonte:
        plano = json.load(fonte)
    json.dump(gerar(plano), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
