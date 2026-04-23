# Portfolio QAOA Thesis Source

This folder is an Overleaf-ready manuscript package for the repository's formal research paper.

## Files

- `main.tex`: full manuscript source
- `references.bib`: bibliography
- `figures/`: committed figures copied from the repository results

## Figure provenance

- `figures/multi_regime_suite_dashboard.png`
  - copied from `results/multi_regime_suite/suite_dashboard.png`
- `figures/mixer_crossover.png`
  - copied from `results/mixer_dominance_pilot_v2/mixer_crossover.png`
- `figures/live_ibm_open_run.png`
  - copied from `results/live_ibm_open_2026_04_19/live_run.png`

## Compile

On Overleaf, set `main.tex` as the main file and use the default PDFLaTeX + BibTeX workflow.

Locally, if a TeX toolchain is installed, a typical sequence is:

```bash
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex
```

## Evidence base

The manuscript is grounded in the committed repository artifacts under:

- `results/multi_regime_suite/`
- `results/mixer_dominance_pilot_v2/`
- `results/live_ibm_open_2026_04_19/`

It intentionally does not make claims beyond those committed artifacts.
