#!/usr/bin/env python3
"""Calcula a chegada de cada trecho a partir do horário de saída e do tempo de estrada.

O tempo dos roteadores (OSRM, Google sem trânsito) não inclui paradas, abastecimento nem
trânsito. Por isso aplicamos um fator (padrão 1,2 = 20% a mais) e arredondamos para 5 min.

Entrada (arquivo ou "-" para stdin):
    {
      "fator": 1.2,
      "trechos": [
        {"id": "T1", "de": "São Paulo", "para": "Belo Horizonte",
         "saida": "2027-01-28T19:00", "duracao_h": 7.9}
      ]
    }

Saída: os mesmos trechos com "duracao_real_h", "chegada" (ISO) e "chegada_txt"
("sex 29/01 04:30"), além de avisos para chegadas de madrugada (00h–05h) e para
trechos que começam antes da chegada do anterior.

Uso:
    python3 horarios.py agenda.json
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta

DIAS = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"]


def txt(dt: datetime) -> str:
    return f"{DIAS[dt.weekday()]} {dt:%d/%m %H:%M}"


def arredondar_5min(dt: datetime) -> datetime:
    minutos = round((dt.minute + dt.second / 60) / 5) * 5
    return dt.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=minutos)


def calcular(agenda: dict) -> dict:
    fator = float(agenda.get("fator", 1.2))
    saida_trechos, avisos = [], []
    chegada_anterior = None
    for t in agenda["trechos"]:
        saida = datetime.fromisoformat(t["saida"])
        if chegada_anterior and saida < chegada_anterior:
            avisos.append(f"{t.get('id', '?')}: sai ({txt(saida)}) antes de chegar do trecho anterior ({txt(chegada_anterior)})")
        horas = float(t["duracao_h"]) * fator
        chegada = arredondar_5min(saida + timedelta(hours=horas))
        if 0 <= chegada.hour < 5:
            avisos.append(f"{t.get('id', '?')}: chegada de madrugada em {t.get('para', '?')} ({txt(chegada)})")
        saida_trechos.append({
            **t,
            "duracao_real_h": round(horas, 2),
            "saida_txt": txt(saida),
            "chegada": chegada.isoformat(timespec="minutes"),
            "chegada_txt": txt(chegada),
        })
        chegada_anterior = chegada
    return {"fator": fator, "trechos": saida_trechos, "avisos": avisos}


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    fonte = sys.stdin if argv[1] == "-" else open(argv[1], encoding="utf-8")
    with fonte:
        agenda = json.load(fonte)
    json.dump(calcular(agenda), sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
