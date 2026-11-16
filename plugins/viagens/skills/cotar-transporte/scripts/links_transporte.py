#!/usr/bin/env python3
"""Gera links de busca já preenchidos para cada trecho: avião, ônibus e carro alugado.

Entrada: o JSON produzido por planejar-viagem/scripts/plano.py (arquivo ou "-" para stdin).
Saída: JSON com, para cada trecho, links por modal + link de rota no Google Maps
(usado para distância e tempo de carro).

Campos opcionais no plano que melhoram os links:
    "iata": {"São Paulo": "SAO", "Rio de Janeiro": "RIO"}   -> habilita link do Kayak voos
    "uf":   {"São Paulo": "sp", "Paraty": "rj"}             -> habilita link direto da ClickBus

Uso:
    python3 links_transporte.py plano.json
"""
from __future__ import annotations

import json
import sys
import unicodedata
from datetime import date
from urllib.parse import quote, quote_plus, urlencode


def slug(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    partes = "".join(c.lower() if c.isalnum() else " " for c in sem_acento).split()
    return "-".join(partes)


def links_trecho(trecho: dict, viajantes: int, iata: dict, uf: dict) -> dict:
    de, para, data = trecho["de"], trecho["para"], trecho["data"]
    data_br = date.fromisoformat(data).strftime("%d/%m/%Y")

    aviao = {
        "google_flights": "https://www.google.com/travel/flights?"
        + urlencode({"q": f"voos de {de} para {para} em {data} {viajantes} adultos", "hl": "pt-BR", "curr": "BRL"}),
    }
    if de in iata and para in iata:
        aviao["kayak"] = (
            f"https://www.kayak.com.br/flights/{iata[de].upper()}-{iata[para].upper()}/{data}/{viajantes}adults"
        )

    onibus = {
        "busca_google": "https://www.google.com/search?q="
        + quote_plus(f"passagem de ônibus {de} para {para} {data_br}"),
    }
    if de in uf and para in uf:
        onibus["clickbus"] = (
            f"https://www.clickbus.com.br/onibus/{slug(de)}-{uf[de].lower()}/"
            f"{slug(para)}-{uf[para].lower()}?departureDate={data}"
        )

    carro = {
        "rota_google_maps": "https://www.google.com/maps/dir/?"
        + urlencode({"api": "1", "origin": de, "destination": para, "travelmode": "driving"}),
    }

    return {"id": trecho["id"], "de": de, "para": para, "data": data,
            "aviao": aviao, "onibus": onibus, "carro": carro}


def links_aluguel_carro(plano: dict) -> dict:
    """Aluguel único cobrindo a viagem toda, retirando e devolvendo na origem."""
    origem = plano["origem"]
    ini, fim = plano["data_inicio"], plano["data_fim"]
    return {
        "retirada": origem,
        "periodo": [ini, fim],
        "kayak_carros": f"https://www.kayak.com.br/cars/{quote(slug(origem))}/{ini}/{fim}",
        "busca_google": "https://www.google.com/search?q="
        + quote_plus(f"aluguel de carro {origem} {ini} a {fim} Localiza Movida Unidas Rentcars"),
    }


def gerar(plano: dict) -> dict:
    viajantes = int(plano.get("viajantes", 1))
    iata, uf = plano.get("iata", {}), plano.get("uf", {})
    return {
        "trechos": [links_trecho(t, viajantes, iata, uf) for t in plano["trechos"]],
        "aluguel_carro": links_aluguel_carro(plano),
    }


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
