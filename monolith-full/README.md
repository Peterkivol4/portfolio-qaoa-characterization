# monolith-full

This directory contains the generated monolithic mirror of the modular
`src/layerfield_qaoa/` package.

Files:

- `layerfield_qaoa_monolith.py`: single-file generated source mirror

Source of truth:

- The modular implementation under `src/layerfield_qaoa/` remains the
  primary editable codebase.
- The monolith is regenerated from that source so future repo changes can be
  mirrored consistently instead of being hand-copied.

Regenerate after source changes:

```bash
python scripts/build_monolith_full.py
```

Verify that the committed monolith is up to date:

```bash
python scripts/build_monolith_full.py --check
```
