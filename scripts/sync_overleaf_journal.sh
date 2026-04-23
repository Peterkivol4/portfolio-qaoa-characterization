#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/docs/student_research_journal.tex"
OVERLEAF_DIR="$ROOT/overleaf/student_research_journal"
TARGET="$OVERLEAF_DIR/main.tex"

mkdir -p "$OVERLEAF_DIR"
cp "$SOURCE" "$TARGET"

echo "synced $SOURCE -> $TARGET"
