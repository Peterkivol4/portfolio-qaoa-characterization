# Overleaf Journal Project

This folder is an upload-ready Overleaf copy of the student research journal.

Files:

- `main.tex`: the LaTeX entry point to compile in Overleaf

How to use it:

1. Upload the entire `overleaf/student_research_journal/` folder to Overleaf.
2. Set `main.tex` as the main document if Overleaf does not detect it automatically.
3. Compile with pdfLaTeX.

Sync policy:

- The canonical editable source in this repo remains `docs/student_research_journal.tex`.
- Run `./scripts/sync_overleaf_journal.sh` after editing the canonical source.
- `./scripts/build_journal.sh` runs that sync step automatically before local compilation.
