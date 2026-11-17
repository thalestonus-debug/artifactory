#!/usr/bin/env python3
"""Escolhe anúncios de hospedagem segundo as preferências do grupo.

Calcula a mediana de preço dos anúncios com as datas exatas e ranqueia os que ficam
até um teto relativo a ela, priorizando bairros preferidos e anúncios bem avaliados.

Entrada (arquivo ou "-" para stdin):
    {
      "preferencias": {
        "bairros_prioritarios": ["Graça"],   # aparecem primeiro (comparação sem acento/caixa)
        "bairros_evitar": [],                # descartados
        "teto_relativo_mediana": 1.0,        # 1.0 = até a mediana; 1.1 = até 10% acima
        "nota_min": 4.7,
        "avaliacoes_min": 5
      },
      "anuncios": [
        {"nome": "...", "bairro": "Graça", "preco_total": 4606, "nota": 4.9,
         "avaliacoes": 12, "datas_exatas": true}
      ]
    }

Anúncios com "datas_exatas": false (seção "datas próximas") ficam fora da mediana e da escolha.
Anúncios sem nota ou com poucas avaliações vão para "sem_historico": podem ser baratos,
mas só valem com cancelamento grátis e conferência de fotos e endereço.

Uso:
    python3 escolher.py anuncios.json
"""
from __future__ import annotations

import json
import statistics
import sys
import unicodedata


def _norm(s: str) -> str:
    return unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower().strip()


def escolher(dados: dict) -> dict:
    pref = dados.get("preferencias", {})
    prioritarios = {_norm(b) for b in pref.get("bairros_prioritarios", [])}
    evitar = {_norm(b) for b in pref.get("bairros_evitar", [])}
    teto_rel = float(pref.get("teto_relativo_mediana", 1.0))
    nota_min = float(pref.get("nota_min", 4.7))
    aval_min = int(pref.get("avaliacoes_min", 5))

    validos = [a for a in dados.get("anuncios", []) if a.get("datas_exatas", True)]
    if not validos:
        return {"mediana": None, "teto": None, "recomendados": [], "sem_historico": [], "descartados": 0}

    mediana = statistics.median(float(a["preco_total"]) for a in validos)
    teto = mediana * teto_rel

    recomendados, sem_historico, descartados = [], [], 0
    for a in validos:
        bairro = _norm(a.get("bairro", ""))
        if bairro in evitar or float(a["preco_total"]) > teto:
            descartados += 1
            continue
        item = {**a, "prioritario": bairro in prioritarios,
                "vs_mediana_pct": round((float(a["preco_total"]) / mediana - 1) * 100)}
        nota, aval = a.get("nota"), int(a.get("avaliacoes") or 0)
        if nota is None or aval < aval_min:
            sem_historico.append(item)
        elif float(nota) >= nota_min:
            recomendados.append(item)
        else:
            descartados += 1

    def ordem(x):
        return (not x["prioritario"], float(x["preco_total"]))

    recomendados.sort(key=ordem)
    sem_historico.sort(key=ordem)
    return {
        "mediana": round(mediana, 2),
        "teto": round(teto, 2),
        "recomendados": recomendados,
        "sem_historico": sem_historico,
        "descartados": descartados,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    fonte = sys.stdin if argv[1] == "-" else open(argv[1], encoding="utf-8")
    with fonte:
        dados = json.load(fonte)
    json.dump(escolher(dados), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
