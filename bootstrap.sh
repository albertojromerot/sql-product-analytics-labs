#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python src/generate_data.py

mkdir -p notebooks_build reports/latest assets
for nb in notebooks_py/*.py; do
  base=$(basename "$nb" .py)
  jupytext --from py:percent --to ipynb "$nb" -o "notebooks_build/${base}.ipynb"
done

for nb in notebooks_build/*.ipynb; do
for nb in notebooks/*.ipynb; do
  jupyter nbconvert --to html --execute "$nb" --output-dir reports/latest
done
