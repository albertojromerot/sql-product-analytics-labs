#!/usr/bin/env bash
set -euo pipefail

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python src/generate_data.py

for nb in notebooks/*.ipynb; do
  jupyter nbconvert --to html --execute "$nb" --output-dir reports/latest
done
