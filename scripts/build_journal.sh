#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DOC="$ROOT/docs/student_research_journal.tex"
OUTDIR="$ROOT/docs"

"$ROOT/scripts/sync_overleaf_journal.sh"

if command -v latexmk >/dev/null 2>&1; then
  latexmk -pdf -interaction=nonstopmode -output-directory="$OUTDIR" "$DOC"
  exit 0
fi

if command -v pdflatex >/dev/null 2>&1; then
  pdflatex -interaction=nonstopmode -output-directory="$OUTDIR" "$DOC"
  pdflatex -interaction=nonstopmode -output-directory="$OUTDIR" "$DOC"
  exit 0
fi

echo "No LaTeX engine found. Install latexmk or pdflatex to build docs/student_research_journal.tex." >&2
exit 1
