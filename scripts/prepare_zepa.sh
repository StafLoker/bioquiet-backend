#!/usr/bin/env bash
# prepare_zepa.sh — prepares the ZEPA geometry dataset
#
# Covers everything in docs/zepa.md:
#   1. Checks dependencies (GDAL, mapshaper)
#   2. Verifies the manually downloaded rn2000.zip exists in raw-data/
#   3. Extracts the shapefile
#   4. Converts + filters to GeoJSON (UTM → WGS84, ZEPA only)
#   5. Simplifies to 5% for mobile use
#   6. Writes src/data/zepa_simplified.geojson
#
# The shapefile ZIP cannot be downloaded automatically — the ministry server
# blocks curl/wget. You must download it manually first:
#
#   1. Open in Safari or Chrome:
#      https://www.mapama.gob.es/app/descargas/descargafichero.aspx?f=rn2000.zip
#   2. Move the downloaded file:
#      mv ~/Downloads/rn2000.zip raw-data/
#
# Then run this script from the project root:
#   bash scripts/prepare_zepa.sh

set -euo pipefail

# ── paths ────────────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
RAW="$ROOT/raw-data"
OUT="$ROOT/src/data"

ZIP="$RAW/rn2000.zip"
SHP="$RAW/PS.RNATURA2000_2024_P.shp"
FULL_GEOJSON="$RAW/zepa_full.geojson"
SIMPLIFIED="$OUT/zepa_simplified.geojson"

# ── helpers ──────────────────────────────────────────────────────────────────
info()  { echo "[zepa] $*"; }
error() { echo "[zepa] ERROR: $*" >&2; exit 1; }

# ── 1. check dependencies ────────────────────────────────────────────────────
info "Checking dependencies..."

if ! command -v ogr2ogr &>/dev/null; then
    error "ogr2ogr not found. Install GDAL with: brew install gdal"
fi

if ! command -v mapshaper &>/dev/null; then
    error "mapshaper not found. Install with: npm install -g mapshaper"
fi

info "  ogr2ogr $(ogr2ogr --version 2>&1 | head -1)"
info "  mapshaper $(mapshaper --version 2>&1 | head -1)"

# ── 2. check ZIP exists ──────────────────────────────────────────────────────
mkdir -p "$RAW" "$OUT"

if [[ ! -f "$ZIP" ]]; then
    error "raw-data/rn2000.zip not found.

The ministry server blocks automated downloads. Download it manually:
  1. Open in Safari or Chrome:
     https://www.mapama.gob.es/app/descargas/descargafichero.aspx?f=rn2000.zip
  2. Move the file:
     mv ~/Downloads/rn2000.zip raw-data/"
fi

info "Found raw-data/rn2000.zip ($(du -sh "$ZIP" | cut -f1))"

# ── 3. extract shapefile ─────────────────────────────────────────────────────
if [[ ! -f "$SHP" ]]; then
    info "Extracting rn2000.zip..."
    unzip -q "$ZIP" -d "$RAW"
    info "Extracted."
else
    info "Shapefile already extracted, skipping unzip."
fi

# verify the shapefile is there
[[ -f "$SHP" ]] || error "Expected $SHP after extraction but not found."

COUNT=$(ogrinfo -al -so "$SHP" 2>/dev/null | grep "Feature Count" | awk '{print $NF}')
info "Shapefile has $COUNT features (expect 1636)"

# ── 4. filter + convert to GeoJSON ──────────────────────────────────────────
# The ministry dataset has a typo: 342 records use "SpecialProtecionArea"
# (missing 't') instead of "SpecialProtectionArea". The LIKE wildcard
# "%SpecialProte%Area%" captures both variants.
if [[ ! -f "$FULL_GEOJSON" ]]; then
    info "Filtering ZEPA zones and converting UTM → WGS84..."
    ogr2ogr \
        -f GeoJSON \
        -t_srs EPSG:4326 \
        -where "desig0 LIKE '%SpecialProte%Area%' OR desig1 LIKE '%SpecialProte%Area%' OR desig2 LIKE '%SpecialProte%Area%'" \
        "$FULL_GEOJSON" \
        "$SHP"

    ZEPA_COUNT=$(ogrinfo -al -so "$FULL_GEOJSON" 2>/dev/null | grep "Feature Count" | awk '{print $NF}')
    info "Filtered to $ZEPA_COUNT ZEPA features (expect 602)"
    [[ "$ZEPA_COUNT" -eq 602 ]] || echo "[zepa] WARNING: expected 602, got $ZEPA_COUNT"
else
    info "zepa_full.geojson already exists, skipping conversion."
fi

# ── 5. simplify to 5% ───────────────────────────────────────────────────────
info "Simplifying geometries to 5%..."
mapshaper "$FULL_GEOJSON" -simplify 5% -o "$SIMPLIFIED" 2>&1 \
    | grep -v "^$" | sed 's/^/[mapshaper] /'

SIZE=$(du -sh "$SIMPLIFIED" | cut -f1)
info "Done. Output: src/data/zepa_simplified.geojson ($SIZE)"
