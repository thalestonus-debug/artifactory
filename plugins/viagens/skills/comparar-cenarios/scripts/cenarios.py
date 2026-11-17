#!/usr/bin/env python3
"""Consolida as cotações e monta os cenários da viagem (transporte x hospedagem).

Entrada: cotacoes.json (formato documentado em ../SKILL.md e em exemplos/cotacoes.json).
Saída: relatório em Markdown (padrão) ou JSON (--json).

Cenários de transporte:
  - aviao   : todos os trechos de avião (onde não houver voo, usa ônibus e avisa)
  - onibus  : todos os trechos de ônibus (onde não houver ônibus, usa avião e avisa)
  - carro   : carro alugado na viagem toda (diárias + taxas + combustível + pedágios + estacionamento)
              ou, se houver "carro_proprio" nas cotações, carro próprio (combustível + pedágios + estacionamento)
  - misto   : em cada trecho, o mais barato entre avião e ônibus

Cenários de hospedagem:
  - airbnb, booking, e "mais_barato" (o menor preço por cidade entre os dois)

Uso:
    python3 cenarios.py cotacoes.json          # Markdown
    python3 cenarios.py cotacoes.json --json   # JSON
"""
from __future__ import annotations

import json
import sys

MODAIS_PUBLICOS = ("aviao", "onibus")
NOMES_TRANSPORTE = {
    "aviao": "Avião",
    "onibus": "Ônibus",
    "carro": "Carro alugado",
    "misto": "Misto (mais barato por trecho)",
}
NOMES_HOSPEDAGEM = {"airbnb": "Airbnb", "booking": "Booking", "mais_barato": "Mais barato por cidade"}


class ErroCotacao(ValueError):
    pass


def _custo_publico(opcao: dict, viajantes: int) -> float:
    if "preco_total" in opcao:
        base = float(opcao["preco_total"])
    else:
        base = float(opcao["preco_por_pessoa"]) * viajantes
    return base + float(opcao.get("extras_por_pessoa", 0)) * viajantes


def custo_carro(trechos: list[dict], aluguel: dict) -> dict:
    """Custo total do carro alugado para a viagem inteira."""
    faltando = [t["id"] for t in trechos if "carro" not in t]
    if faltando:
        raise ErroCotacao(f"Trechos sem dados de carro: {', '.join(faltando)}")
    dias = int(aluguel.get("dias", 0))
    km = sum(float(t["carro"]["distancia_km"]) for t in trechos)
    litros = km / float(aluguel["consumo_km_l"])
    partes = {
        "aluguel": float(aluguel.get("diaria", 0)) * dias + float(aluguel.get("taxas", 0)),
        "combustível": litros * float(aluguel["preco_combustivel"]),
        "pedágios": sum(float(t["carro"].get("pedagio", 0)) for t in trechos),
        "estacionamento": float(aluguel.get("estacionamento_dia", 0)) * dias,
    }
    return {
        "total": sum(partes.values()),
        "detalhe": {k: round(v, 2) for k, v in partes.items()},
        "km": round(km, 1),
        "horas": sum(float(t["carro"].get("duracao_h", 0)) for t in trechos),
    }


def cenario_transporte(nome: str, trechos: list[dict], viajantes: int, aluguel: dict | None) -> dict:
    if nome == "carro":
        if not aluguel:
            raise ErroCotacao("Sem 'aluguel_carro' nas cotações.")
        c = custo_carro(trechos, aluguel)
        return {"total": c["total"], "horas": c["horas"], "avisos": [],
                "detalhe": c["detalhe"], "km": c["km"], "escolhas": {t["id"]: "carro" for t in trechos}}

    total, horas, avisos, escolhas = 0.0, 0.0, [], {}
    for t in trechos:
        disponiveis = [m for m in MODAIS_PUBLICOS if m in t]
        if not disponiveis:
            raise ErroCotacao(f"Trecho {t['id']} sem cotação de avião nem de ônibus.")
        if nome == "misto":
            modal = min(disponiveis, key=lambda m: _custo_publico(t[m], viajantes))
        elif nome in t:
            modal = nome
        else:
            modal = disponiveis[0]
            avisos.append(f"{t['id']} ({t['de']} → {t['para']}): sem {NOMES_TRANSPORTE[nome].lower()}, usado {NOMES_TRANSPORTE[modal].lower()}")
        total += _custo_publico(t[modal], viajantes)
        horas += float(t[modal].get("duracao_h", 0))
        escolhas[t["id"]] = modal
    return {"total": total, "horas": horas, "avisos": avisos, "escolhas": escolhas}


def cenario_hospedagem(nome: str, estadias: list[dict]) -> dict:
    total, avisos, escolhas = 0.0, [], {}
    for e in estadias:
        disponiveis = [p for p in ("airbnb", "booking") if p in e]
        if not disponiveis:
            raise ErroCotacao(f"Estadia {e['id']} ({e['cidade']}) sem cotação.")
        if nome == "mais_barato":
            plat = min(disponiveis, key=lambda p: float(e[p]["preco_total"]))
        elif nome in e:
            plat = nome
        else:
            plat = disponiveis[0]
            avisos.append(f"{e['cidade']}: sem {NOMES_HOSPEDAGEM[nome]}, usado {NOMES_HOSPEDAGEM[plat]}")
        total += float(e[plat]["preco_total"])
        escolhas[e["id"]] = plat
    return {"total": total, "avisos": avisos, "escolhas": escolhas}


def calcular(cot: dict) -> dict:
    viajantes = int(cot.get("viajantes", 1))
    trechos, estadias = cot.get("trechos", []), cot.get("estadias", [])
    proprio = cot.get("carro_proprio")
    aluguel = cot.get("aluguel_carro")
    if proprio:  # carro próprio: mesmo cálculo, sem diárias
        aluguel = {**proprio, "diaria": 0, "taxas": 0}

    transportes, indisponiveis = {}, {}
    tem_publico = any(m in t for t in trechos for m in MODAIS_PUBLICOS)
    for nome in NOMES_TRANSPORTE:
        if nome != "carro" and not tem_publico:
            continue  # nenhuma cotação de avião/ônibus (ex.: viagem só de carro próprio)
        try:
            transportes[nome] = cenario_transporte(nome, trechos, viajantes, aluguel)
        except (ErroCotacao, KeyError) as e:
            indisponiveis[nome] = str(e)
    misto = transportes.get("misto")
    if misto and any(transportes[n]["escolhas"] == misto["escolhas"] for n in MODAIS_PUBLICOS if n in transportes):
        del transportes["misto"]  # idêntico a avião ou ônibus: não repetir nas tabelas
    hospedagens = {}
    for n in NOMES_HOSPEDAGEM:
        if n != "mais_barato" and not any(n in e for e in estadias):
            continue  # plataforma sem nenhuma cotação: não vira cenário
        hospedagens[n] = cenario_hospedagem(n, estadias)
    if list(hospedagens) == ["mais_barato"] or len(hospedagens) == 2:
        hospedagens.pop("mais_barato", None)  # só uma plataforma: "mais barato" seria repetição

    combinacoes = []
    for nt, t in transportes.items():
        for nh, h in hospedagens.items():
            total = t["total"] + h["total"]
            combinacoes.append({
                "transporte": nt, "hospedagem": nh,
                "total": round(total, 2), "por_pessoa": round(total / viajantes, 2),
                "horas_deslocamento": round(t["horas"], 1),
            })
    combinacoes.sort(key=lambda c: c["total"])
    return {
        "carro_proprio": bool(proprio),
        "viajantes": viajantes,
        "transporte": transportes,
        "transporte_indisponivel": indisponiveis,
        "hospedagem": hospedagens,
        "combinacoes": combinacoes,
    }


def brl(v: float) -> str:
    s = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"


def horas(h: float) -> str:
    return f"{h:.1f}".replace(".", ",") + " h"


def markdown(r: dict) -> str:
    v = r["viajantes"]
    nomes_t = dict(NOMES_TRANSPORTE)
    if r.get("carro_proprio"):
        nomes_t["carro"] = "Carro próprio"
    linhas = [f"## Comparativo de cenários ({v} viajante{'s' if v > 1 else ''})", ""]

    linhas += ["### Transporte", "", "| Cenário | Total | Por pessoa | Horas em deslocamento |", "|---|---:|---:|---:|"]
    for n, t in sorted(r["transporte"].items(), key=lambda kv: kv[1]["total"]):
        linhas.append(f"| {nomes_t[n]} | {brl(t['total'])} | {brl(t['total'] / v)} | {horas(t['horas'])} |")
    for n, motivo in r["transporte_indisponivel"].items():
        linhas.append(f"| {nomes_t[n]} | indisponível | — | — |")
    if "carro" in r["transporte"]:
        d = {k: x for k, x in r["transporte"]["carro"]["detalhe"].items() if x}
        linhas += ["", nomes_t["carro"] + ": " + ", ".join(f"{k} {brl(x)}" for k, x in d.items())
                   + f" ({r['transporte']['carro']['km']:.0f} km)."]

    linhas += ["", "### Hospedagem", "", "| Cenário | Total | Por pessoa |", "|---|---:|---:|"]
    for n, h in sorted(r["hospedagem"].items(), key=lambda kv: kv[1]["total"]):
        linhas.append(f"| {NOMES_HOSPEDAGEM[n]} | {brl(h['total'])} | {brl(h['total'] / v)} |")

    linhas += ["", "### Combinações (da mais barata para a mais cara)", "",
               "| # | Transporte | Hospedagem | Total | Por pessoa | Horas em deslocamento |",
               "|---:|---|---|---:|---:|---:|"]
    for i, c in enumerate(r["combinacoes"], 1):
        linhas.append(
            f"| {i} | {nomes_t[c['transporte']]} | {NOMES_HOSPEDAGEM[c['hospedagem']]} | "
            f"{brl(c['total'])} | {brl(c['por_pessoa'])} | {horas(c['horas_deslocamento'])} |"
        )

    avisos = [a for t in r["transporte"].values() for a in t["avisos"]]
    avisos += [a for h in r["hospedagem"].values() for a in h["avisos"]]
    avisos += [f"{nomes_t[n]} indisponível: {m}" for n, m in r["transporte_indisponivel"].items()]
    if avisos:
        linhas += ["", "### Avisos", ""] + [f"- {a}" for a in dict.fromkeys(avisos)]
    return "\n".join(linhas) + "\n"


def main(argv: list[str]) -> int:
    args = [a for a in argv[1:] if a != "--json"]
    if len(args) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    fonte = sys.stdin if args[0] == "-" else open(args[0], encoding="utf-8")
    with fonte:
        cot = json.load(fonte)
    try:
        r = calcular(cot)
    except ErroCotacao as e:
        print(f"Erro: {e}", file=sys.stderr)
        return 1
    if "--json" in argv:
        json.dump(r, sys.stdout, ensure_ascii=False, indent=2)
        print()
    else:
        sys.stdout.write(markdown(r))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
