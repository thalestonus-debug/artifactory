#!/usr/bin/env python3
"""Valida a organização do repositório (rodado no CI e antes de cada commit).

Verifica:
  - todo plugin em plugins/ (exceto _modelo) tem .claude-plugin/plugin.json válido;
  - o nome no plugin.json bate com o nome da pasta;
  - todo plugin está no catálogo (.claude-plugin/marketplace.json) e vice-versa;
  - toda skill tem SKILL.md com frontmatter 'name' (igual à pasta) e 'description'.

Uso:
    python3 ferramentas/validar.py
"""
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PLUGINS = RAIZ / "plugins"


def frontmatter(texto):
    m = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
    if not m:
        return None
    campos = {}
    for linha in m.group(1).splitlines():
        if ":" in linha:
            k, v = linha.split(":", 1)
            campos[k.strip()] = v.strip()
    return campos


def validar():
    erros = []
    cat = json.loads((RAIZ / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
    no_catalogo = {p["name"]: p for p in cat.get("plugins", [])}

    pastas = sorted(p for p in PLUGINS.iterdir() if p.is_dir() and not p.name.startswith("_"))
    for pasta in pastas:
        manifesto = pasta / ".claude-plugin" / "plugin.json"
        if not manifesto.is_file():
            erros.append(f"{pasta.name}: falta .claude-plugin/plugin.json")
            continue
        dados = json.loads(manifesto.read_text(encoding="utf-8"))
        if dados.get("name") != pasta.name:
            erros.append(f"{pasta.name}: plugin.json tem name={dados.get('name')!r}, esperado {pasta.name!r}")
        entrada = no_catalogo.get(pasta.name)
        if not entrada:
            erros.append(f"{pasta.name}: não está no marketplace.json")
        elif entrada.get("source") != f"./plugins/{pasta.name}":
            erros.append(f"{pasta.name}: source no catálogo deveria ser ./plugins/{pasta.name}")

        skills = sorted((pasta / "skills").glob("*/")) if (pasta / "skills").is_dir() else []
        if not skills:
            erros.append(f"{pasta.name}: nenhuma skill em skills/")
        for s in skills:
            md = s / "SKILL.md"
            if not md.is_file():
                erros.append(f"{pasta.name}/{s.name}: falta SKILL.md")
                continue
            fm = frontmatter(md.read_text(encoding="utf-8"))
            if fm is None:
                erros.append(f"{pasta.name}/{s.name}: SKILL.md sem frontmatter (--- ... ---)")
                continue
            if fm.get("name") != s.name:
                erros.append(f"{pasta.name}/{s.name}: frontmatter name={fm.get('name')!r} difere da pasta")
            if not fm.get("description"):
                erros.append(f"{pasta.name}/{s.name}: frontmatter sem description")

    nomes = {p.name for p in pastas}
    for nome in no_catalogo:
        if nome not in nomes:
            erros.append(f"catálogo: plugin {nome!r} listado mas plugins/{nome} não existe")
    return erros, [p.name for p in pastas]


if __name__ == "__main__":
    erros, plugins = validar()
    if erros:
        print("Problemas encontrados:")
        for e in erros:
            print(f"  - {e}")
        sys.exit(1)
    print(f"OK: {len(plugins)} frente(s) válida(s): {', '.join(plugins)}")
