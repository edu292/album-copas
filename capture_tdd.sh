#!/usr/bin/env bash
set -u

PHASE="${1:-red}"
OUT_DIR="docs/${PHASE}"
mkdir -p "$OUT_DIR"

sleep 0.5

for feature in core/tests/features/*.feature; do
    name="$(basename "$feature" .feature)"
    expr=$(uv run python -c '
import sys, re, unicodedata

text = open(sys.argv[1], encoding="utf-8").read()
titles = re.findall(r"^\s*(?:Cenário|Esquema do Cenário):\s*(.+)$", text, re.M)
slugs = []
for t in titles:
    # Match pytest-bdd scenario function naming
    s = re.sub(r"[^\w\s]", "", t.lower()).strip()
    s = re.sub(r"\s+", "_", s)
    slugs.append(s)
print(" or ".join(slugs))
' "$feature")

    clear
    echo "=== [${PHASE^^}] ${name} ==="
    uv run pytest core/tests/test_album.py -k "$expr" --tb=line -v --no-header || true
    sleep 0.5
    grim "${OUT_DIR}/${name}.png"
done

echo "Screenshots saved in ${OUT_DIR}/"
