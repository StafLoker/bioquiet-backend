import json
import os
from typing import Any

_data_dir = os.path.join(os.path.dirname(__file__), "data")


def _load(name: str) -> Any:
    with open(os.path.join(_data_dir, name), encoding="utf-8") as f:
        return json.load(f)


_GEOJSON: dict[str, Any] = _load("zepa_simplified.geojson")
_SITES: dict[str, Any] = _load("zepa_sites.json")
_HABITATS: dict[str, Any] = _load("zepa_habitats.json")
_SPECIES: dict[str, Any] = _load("zepa_species.json")
_IMPACTS: dict[str, Any] = _load("zepa_impacts.json")
_MANAGEMENT: dict[str, Any] = _load("zepa_management.json")

# Noise thresholds (dB LAeq) for ZEPA zones.
# Based on: normativa espacios naturales (sensibilidad acústica alta) +
# scientific literature on bird population response to noise.
# Safe: < 45 dB  |  Warning: 45–60 dB  |  Danger: > 60 dB
_NOISE_THRESHOLDS: dict[str, int] = {
    "db_safe": 45,
    "db_warning": 60,
}


def _serialize_zone(feature: dict[str, Any]) -> dict[str, Any]:
    props = feature["properties"]
    local_id: str = props.get("localId", "")
    site = _SITES.get(local_id, {})
    return {
        "id": local_id,
        "name": props.get("SOName", ""),
        "noise_thresholds": _NOISE_THRESHOLDS,
        "area_ha": site.get("area_ha"),
        "date_spa": site.get("date_spa"),
        "spa_legal_ref": site.get("spa_legal_ref"),
        "description": site.get("description"),
        "quality": site.get("quality"),
        "habitats": _HABITATS.get(local_id, []),
        "species": _SPECIES.get(local_id, []),
        "impacts": _IMPACTS.get(local_id, []),
        "management": _MANAGEMENT.get(local_id, []),
        "geometry": feature["geometry"],
    }


def _points(feature: dict[str, Any]) -> list[list[float]]:
    geom = feature["geometry"]
    if geom is None:
        return []
    coords = geom["coordinates"]
    if geom["type"] == "Polygon":
        # coordinates[ring][point]
        return [pt for ring in coords for pt in ring]
    else:
        # MultiPolygon: coordinates[polygon][ring][point]
        return [pt for polygon in coords for ring in polygon for pt in ring]


def get_zepa_by_bbox(minLon: float, minLat: float, maxLon: float, maxLat: float) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for feature in _GEOJSON["features"]:
        pts = _points(feature)
        if not pts:
            continue
        lons = [pt[0] for pt in pts]
        lats = [pt[1] for pt in pts]
        if max(lons) >= minLon and min(lons) <= maxLon and max(lats) >= minLat and min(lats) <= maxLat:
            results.append(_serialize_zone(feature))
    return results
