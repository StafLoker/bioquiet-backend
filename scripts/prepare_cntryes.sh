#!/usr/bin/env bash
# prepare_cntryes.sh — prepares the CNTRYES ecological metadata
#
# Covers everything in docs/cntryes.md:
#   1. Checks dependencies (mdbtools, python)
#   2. Downloads Natura2000_end2023_ES_20250423.zip from MITECO
#   3. Extracts the .accdb database
#   4. Runs extract_cntryes.py to generate JSON files in src/data/
#
# Run from the project root:
#   bash scripts/prepare_cntryes.sh

set -euo pipefail

# ── paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RAW="$ROOT/raw-data"
OUT="$ROOT/src/data"

ZIP="$RAW/cntryes.zip"
ACCDB="$RAW/Natura2000_end2023_ES_20250423.accdb"
EXTRACT_SCRIPT="$SCRIPT_DIR/extract_cntryes.py"

CNTRYES_URL="https://www.miteco.gob.es/content/dam/miteco/es/biodiversidad/servicios/banco-datos-naturaleza/informacion-disponible/cntryes/Natura2000_end2023_ES_20250423.zip"

# ── helpers ──────────────────────────────────────────────────────────────────
info()  { echo "[cntryes] $*"; }
error() { echo "[cntryes] ERROR: $*" >&2; exit 1; }

# ── 1. check dependencies ────────────────────────────────────────────────────
info "Checking dependencies..."

if ! command -v mdb-export &>/dev/null; then
    error "mdbtools not found. Install with: brew install mdbtools"
fi

PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON="$candidate"
        break
    fi
done
[[ -n "$PYTHON" ]] || error "Python not found."

# prefer the project venv if it exists
VENV_PYTHON="$ROOT/.venv/bin/python3"
if [[ -f "$VENV_PYTHON" ]]; then
    PYTHON="$VENV_PYTHON"
fi

info "  mdb-export $(mdb-export --version 2>&1 | head -1)"
info "  python $("$PYTHON" --version)"

# ── 2. download ZIP ──────────────────────────────────────────────────────────
mkdir -p "$RAW" "$OUT"

if [[ ! -f "$ZIP" ]]; then
    info "Downloading CNTRYES database from MITECO (~9 MB)..."
    curl -L --progress-bar -o "$ZIP" "$CNTRYES_URL"
    info "Downloaded."
else
    info "cntryes.zip already exists ($(du -sh "$ZIP" | cut -f1)), skipping download."
fi

# ── 3. extract .accdb ────────────────────────────────────────────────────────
if [[ ! -f "$ACCDB" ]]; then
    info "Extracting cntryes.zip..."
    unzip -q "$ZIP" -d "$RAW"
    info "Extracted."
else
    info "Database already extracted, skipping unzip."
fi

[[ -f "$ACCDB" ]] || error "Expected $ACCDB after extraction but not found."
info "Database: $(du -sh "$ACCDB" | cut -f1)"

# ── 4. extract JSON files ────────────────────────────────────────────────────
info "Running extract_cntryes.py..."
cd "$ROOT"
"$PYTHON" "$EXTRACT_SCRIPT"

info ""
info "Done. Files written to src/data/:"
for f in zepa_sites zepa_habitats zepa_species zepa_impacts zepa_management; do
    path="$OUT/${f}.json"
    [[ -f "$path" ]] && info "  ${f}.json ($(du -sh "$path" | cut -f1))"
done
