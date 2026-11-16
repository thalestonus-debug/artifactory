#!/usr/bin/env python3
"""Cria uma nova frente (plugin) a partir de plugins/_modelo e a registra no catálogo.

Uso:
    python3 ferramentas/nova_frente.py <nome-da-frente> "Descrição curta" [categoria]

Exemplo:
    python3 ferramentas/nova_frente.py financas "Controle de gastos e investimentos" pessoal
"""
import json
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
MODELO = RAIZ / "plugins" / "_modelo"
CATALOGO = RAIZ / ".claude-plugin" / "marketplace.json"


def main(argv):
    if len(argv) not in (3, 4):
        print(__doc__, file=sys.stderr)
        return 2
    nome, descricao = argv[1], argv[2]
    categoria = argv[3] if len(argv) == 4 else "geral"
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", nome):
        print("Erro: use só letras minúsculas, números e hífens (ex.: financas, gestao-obras).", file=sys.stderr)
        return 1
    destino = RAIZ / "plugins" / nome
    if destino.exists():
        print(f"Erro: a frente '{nome}' já existe em {destino.relative_to(RAIZ)}.", file=sys.stderr)
        return 1

    shutil.copytree(MODELO, destino, ignore=shutil.ignore_patterns("__pycache__"))
    for arq in destino.rglob("*"):
        if arq.is_file() and arq.suffix in {".json", ".md", ".py"}:
            texto = arq.read_text(encoding="utf-8")
            arq.write_text(texto.replace("__FRENTE__", nome).replace("__DESCRICAO__", descricao), encoding="utf-8")

    cat = json.loads(CATALOGO.read_text(encoding="utf-8"))
    cat["plugins"].append({
        "name": nome,
        "source": f"./plugins/{nome}",
        "description": descricao,
        "version": "0.1.0",
        "category": categoria,
    })
    cat["plugins"].sort(key=lambda p: p["name"])
    CATALOGO.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"Frente criada em plugins/{nome}/ e registrada no catálogo.")
    print("Próximos passos: renomeie skills/nome-da-skill, escreva o SKILL.md e rode ferramentas/validar.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
