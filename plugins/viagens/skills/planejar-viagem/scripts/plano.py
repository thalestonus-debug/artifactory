#!/usr/bin/env python3
"""Monta o esqueleto da viagem: trechos (deslocamentos) e estadias (noites por cidade).

Entrada: um JSON (arquivo ou stdin) no formato

    {
      "origem": "São Paulo",
      "data_inicio": "2026-12-20",
      "dias": 7,                         # total de dias da viagem (opcional se cada destino tiver "noites")
      "viajantes": 2,
      "retornar_origem": true,           # padrão: true
      "destinos": [
        {"cidade": "Rio de Janeiro"},    # sem "noites": divide automaticamente
        {"cidade": "Paraty", "noites": 2}
      ]
    }

Convenção: uma viagem de N dias tem N-1 noites (chega no dia 1, volta no dia N).
As noites que não foram fixadas por destino são distribuídas igualmente entre os demais,
com o resto indo para os primeiros destinos da lista.

Saída: JSON com "trechos" e "estadias", pronto para as skills de cotação.

Uso:
    python3 plano.py viagem.json
    echo '{...}' | python3 plano.py -
"""
from __future__ import annotations

import json
import sys
from datetime import date, timedelta


class ErroPlano(ValueError):
    pass


def _distribuir_noites(destinos: list[dict], dias: int | None) -> list[int]:
    fixas = [d.get("noites") for d in destinos]
    for n in fixas:
        if n is not None and (not isinstance(n, int) or n < 0):
            raise ErroPlano(f"'noites' deve ser inteiro >= 0, recebido: {n!r}")

    livres = [i for i, n in enumerate(fixas) if n is None]
    if not livres:
        total = sum(fixas)
        if dias is not None and total != dias - 1:
            raise ErroPlano(
                f"A soma das noites por destino ({total}) não bate com {dias} dias "
                f"({dias - 1} noites). Ajuste 'dias' ou as 'noites'."
            )
        return fixas  # type: ignore[return-value]

    if dias is None:
        raise ErroPlano("Informe 'dias' no total ou 'noites' em todos os destinos.")
    if dias < 1:
        raise ErroPlano("'dias' deve ser >= 1.")

    restantes = (dias - 1) - sum(n for n in fixas if n is not None)
    if restantes < 0:
        raise ErroPlano(
            f"As noites fixadas já passam de {dias - 1} noites ({dias} dias)."
        )
    base, resto = divmod(restantes, len(livres))
    resultado = list(fixas)
    for pos, i in enumerate(livres):
        resultado[i] = base + (1 if pos < resto else 0)
    return resultado  # type: ignore[return-value]


def montar_plano(spec: dict) -> dict:
    origem = spec.get("origem")
    destinos = spec.get("destinos") or []
    if not origem:
        raise ErroPlano("Campo 'origem' é obrigatório.")
    if not destinos:
        raise ErroPlano("Informe ao menos um destino em 'destinos'.")
    destinos = [d if isinstance(d, dict) else {"cidade": str(d)} for d in destinos]
    for d in destinos:
        if not d.get("cidade"):
            raise ErroPlano("Todo destino precisa de 'cidade'.")

    try:
        inicio = date.fromisoformat(spec["data_inicio"])
    except (KeyError, ValueError) as e:
        raise ErroPlano("'data_inicio' é obrigatório no formato AAAA-MM-DD.") from e

    viajantes = int(spec.get("viajantes", 1))
    if viajantes < 1:
        raise ErroPlano("'viajantes' deve ser >= 1.")
    retornar = bool(spec.get("retornar_origem", True))
    noites = _distribuir_noites(destinos, spec.get("dias"))

    trechos, estadias = [], []
    atual, dia = origem, inicio
    for d, n in zip(destinos, noites):
        if n == 0:
            # Passa pela cidade sem dormir: não gera trecho separado nem estadia.
            continue
        trechos.append({
            "id": f"T{len(trechos) + 1}",
            "de": atual,
            "para": d["cidade"],
            "data": dia.isoformat(),
        })
        saida = dia + timedelta(days=n)
        estadias.append({
            "id": f"H{len(estadias) + 1}",
            "cidade": d["cidade"],
            "checkin": dia.isoformat(),
            "checkout": saida.isoformat(),
            "noites": n,
        })
        atual, dia = d["cidade"], saida

    if not estadias:
        raise ErroPlano("Nenhum destino ficou com noites > 0; aumente 'dias'.")

    if retornar and atual != origem:
        trechos.append({
            "id": f"T{len(trechos) + 1}",
            "de": atual,
            "para": origem,
            "data": dia.isoformat(),
        })

    total_noites = sum(e["noites"] for e in estadias)
    return {
        "origem": origem,
        "viajantes": viajantes,
        "data_inicio": inicio.isoformat(),
        "data_fim": dia.isoformat(),
        "dias": total_noites + 1,
        "noites": total_noites,
        "trechos": trechos,
        "estadias": estadias,
    }


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    fonte = sys.stdin if argv[1] == "-" else open(argv[1], encoding="utf-8")
    with fonte:
        spec = json.load(fonte)
    try:
        plano = montar_plano(spec)
    except ErroPlano as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    json.dump(plano, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
