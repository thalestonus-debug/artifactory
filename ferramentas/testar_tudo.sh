#!/usr/bin/env bash
# Valida a estrutura e roda os testes de todas as frentes (inclusive o modelo).
set -euo pipefail
cd "$(dirname "$0")/.."
python3 ferramentas/validar.py
for testes in plugins/*/tests; do
  echo "== $testes"
  python3 -m unittest discover -s "$testes"
done
