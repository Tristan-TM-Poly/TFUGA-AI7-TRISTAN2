#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
pdflatex -interaction=nonstopmode -halt-on-error main.tex
biber main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
python scripts/page_controller.py main.pdf
