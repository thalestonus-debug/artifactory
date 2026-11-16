#!/usr/bin/env python3
"""Exemplo de script de skill: lê um JSON e devolve um JSON. Substitua pela sua lógica."""
import json
import sys


def processar(dados: dict) -> dict:
    return {"recebido": dados}


if __name__ == "__main__":
    fonte = sys.stdin if len(sys.argv) < 2 or sys.argv[1] == "-" else open(sys.argv[1], encoding="utf-8")
    json.dump(processar(json.load(fonte)), sys.stdout, ensure_ascii=False, indent=2)
    print()
