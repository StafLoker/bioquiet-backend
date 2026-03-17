"""
Extract CNTRYES metadata for ZEPA sites and generate JSON files in src/data/.

Usage:
    python scripts/extract_cntryes.py

Input:
    raw-data/Natura2000_end2023_ES_20250423.accdb
    src/data/zepa_simplified.geojson

Output:
    src/data/zepa_sites.json       — site-level info (area, coords, description, dates)
    src/data/zepa_habitats.json    — Annex I habitats per site
    src/data/zepa_species.json     — Annex I/II species per site
    src/data/zepa_impacts.json     — threats and pressures per site
    src/data/zepa_management.json  — management body per site
"""

import csv
import io
import json
import os
import subprocess
import sys

ACCDB = os.path.join("raw-data", "Natura2000_end2023_ES_20250423.accdb")
GEOJSON = os.path.join("src", "data", "zepa_simplified.geojson")
OUT_DIR = os.path.join("src", "data")


def export_table(table: str) -> list[dict]:
    result = subprocess.run(
        ["mdb-export", ACCDB, table],
        capture_output=True, text=True, check=True
    )
    return list(csv.DictReader(io.StringIO(result.stdout)))


def load_zepa_ids() -> set[str]:
    with open(GEOJSON) as f:
        data = json.load(f)
    return {feat["properties"]["localId"] for feat in data["features"]}


def write_json(name: str, data: object) -> None:
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    size_kb = os.path.getsize(path) / 1024
    print(f"  {path}  ({size_kb:.0f} KB)")


def parse_date(raw: str) -> str | None:
    """Convert Access date '12/01/97 00:00:00' → 'YYYY-MM-DD'."""
    if not raw:
        return None
    try:
        part = raw.split(" ")[0]  # '12/01/97'
        m, d, y = part.split("/")
        year = int(y)
        year = 1900 + year if year >= 50 else 2000 + year
        return f"{year:04d}-{int(m):02d}-{int(d):02d}"
    except Exception:
        return raw or None


def main() -> None:
    if not os.path.exists(ACCDB):
        print(f"ERROR: {ACCDB} not found", file=sys.stderr)
        sys.exit(1)

    print("Loading ZEPA IDs from GeoJSON...")
    zepa_ids = load_zepa_ids()
    print(f"  {len(zepa_ids)} ZEPA sites")

    # ── NATURA2000SITES ──────────────────────────────────────────────────────
    print("Extracting NATURA2000SITES...")
    sites_raw = export_table("NATURA2000SITES")
    sites: dict[str, object] = {}
    for row in sites_raw:
        sc = row["SITECODE"]
        if sc not in zepa_ids:
            continue
        sites[sc] = {
            "area_ha": float(row["AREAHA"]) if row["AREAHA"] else None,
            "longitude": float(row["LONGITUDE"]) if row["LONGITUDE"] else None,
            "latitude": float(row["LATITUDE"]) if row["LATITUDE"] else None,
            "marine_pct": float(row["MARINE_AREA_PERCENTAGE"]) if row["MARINE_AREA_PERCENTAGE"] else None,
            "date_spa": parse_date(row["DATE_SPA"]),
            "spa_legal_ref": row["SPA_LEGAL_REFERENCE"] or None,
            "description": row["DOCUMENTATION"].strip() or None,
            "quality": row["QUALITY"].strip() or None,
            "other_characteristics": row["OTHERCHARACT"].strip() or None,
        }
    print(f"  {len(sites)} sites matched")
    write_json("zepa_sites.json", sites)

    # ── HABITATS ─────────────────────────────────────────────────────────────
    print("Extracting HABITATS...")
    habitats_raw = export_table("HABITATS")
    habitats: dict[str, list] = {}
    for row in habitats_raw:
        sc = row["SITECODE"]
        if sc not in zepa_ids:
            continue
        habitats.setdefault(sc, []).append({
            "code": row["HABITATCODE"],
            "description": row["DESCRIPTION"],
            "priority": row["HABITAT_PRIORITY"] == "1",
            "cover_ha": float(row["COVER_HA"]) if row["COVER_HA"] else None,
            "representativity": row["REPRESENTATIVITY"] or None,
            "conservation": row["CONSERVATION"] or None,
            "global_assessment": row["GLOBAL_ASSESSMENT"] or None,
        })
    print(f"  {len(habitats)} sites with habitat data")
    write_json("zepa_habitats.json", habitats)

    # ── SPECIES ──────────────────────────────────────────────────────────────
    print("Extracting SPECIES...")
    species_raw = export_table("SPECIES")
    species: dict[str, list] = {}
    for row in species_raw:
        sc = row["SITECODE"]
        if sc not in zepa_ids:
            continue
        species.setdefault(sc, []).append({
            "code": row["SPECIESCODE"],
            "name": row["SPECIESNAME"],
            "group": row["SPGROUP"],
            "population_type": row["POPULATION_TYPE"] or None,
            "abundance": row["ABUNDANCE_CATEGORY"] or None,
            "conservation": row["CONSERVATION"] or None,
            "global": row["GLOBAL"] or None,
        })
    print(f"  {len(species)} sites with species data")
    write_json("zepa_species.json", species)

    # ── IMPACT (threats & pressures) ─────────────────────────────────────────
    print("Extracting IMPACT...")
    impact_raw = export_table("IMPACT")
    impacts: dict[str, list] = {}
    for row in impact_raw:
        sc = row["SITECODE"]
        if sc not in zepa_ids:
            continue
        impacts.setdefault(sc, []).append({
            "code": row["IMPACTCODE"],
            "description": row["DESCRIPTION"],
            "intensity": row["INTENSITY"] or None,
            "occurrence": row["OCCURRENCE"] or None,
            "type": row["IMPACT_TYPE"] or None,
        })
    print(f"  {len(impacts)} sites with impact data")
    write_json("zepa_impacts.json", impacts)

    # ── MANAGEMENT ───────────────────────────────────────────────────────────
    print("Extracting MANAGEMENT...")
    mgmt_raw = export_table("MANAGEMENT")
    management: dict[str, list] = {}
    for row in mgmt_raw:
        sc = row["SITECODE"]
        if sc not in zepa_ids:
            continue
        management.setdefault(sc, []).append({
            "org_name": row["ORG_NAME"].strip() or None,
            "org_email": row["ORG_EMAIL"].strip() or None,
            "plan_url": row["MANAG_PLAN_URL"].strip() or None,
            "measures": row["MANAG_CONSERV_MEASURES"].strip() or None,
        })
    print(f"  {len(management)} sites with management data")
    write_json("zepa_management.json", management)

    print("\nDone.")


if __name__ == "__main__":
    main()
