from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs' / 'baseline_manifest.json'
SKIP = {
    '.git',
    '__pycache__',
    '.pytest_cache',
    '.mypy_cache',
    '.ruff_cache',
    'baseline_manifest.json',
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _iter_files(root: Path):
    for p in sorted(root.rglob('*')):
        rel = p.relative_to(root)
        parts = set(rel.parts)
        if p.is_dir():
            continue
        if parts & SKIP:
            continue
        if rel.parts[:1] == ('artifacts_check',) or rel.parts[:1] == ('tmp_artifacts',) or rel.parts[:1] == ('tmp_stage',) or rel.parts[:1] == ('tmp_stage2',) or rel.parts[:1] == ('tmp_check',) or rel.parts[:1] == ('tmp_step5',) or rel.parts[:1] == ('tmp_step7',) or rel.parts[:1] == ('smoke_portfolio_qaoa',) or rel.parts[:1] == ('suite_outputs',):
            continue
        yield p


def main() -> None:
    files = []
    repo_hasher = hashlib.sha256()
    for p in _iter_files(ROOT):
        rel = p.relative_to(ROOT).as_posix()
        digest = _sha256(p)
        repo_hasher.update(rel.encode('utf-8'))
        repo_hasher.update(b'\0')
        repo_hasher.update(digest.encode('ascii'))
        files.append({'path': rel, 'sha256': digest, 'size': p.stat().st_size})

    payload = {
        'schema_version': 1,
        'file_count': len(files),
        'repo_digest': repo_hasher.hexdigest(),
        'files': files,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(OUT)


if __name__ == '__main__':
    main()
