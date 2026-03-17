import json
import os
from typing import Any

_data_path = os.path.join(os.path.dirname(__file__), "data", "zepa_simplified.geojson")

with open(_data_path) as f:
    GEOJSON: dict[str, Any] = json.load(f)

# Red Natura 2000 CCAA codes (2-digit prefix after "ES" in localId)
# Source: Ministerio MITECO / INSPIRE codelist
_CCAA_CODES: dict[str, str] = {
    "00": "Plurirregional",
    "11": "Galicia",
    "12": "Principado de Asturias",
    "13": "Cantabria",
    "21": "País Vasco",
    "22": "Comunidad Foral de Navarra",
    "23": "La Rioja",
    "24": "Aragón",
    "30": "Comunidad de Madrid",
    "31": "Castilla y León",  # also 41-46
    "32": "Castilla-La Mancha",
    "33": "Extremadura",
    "41": "Castilla y León",
    "42": "Castilla y León",
    "43": "Castilla y León",
    "44": "Castilla y León",
    "45": "Castilla y León",
    "46": "Castilla y León",
    "51": "Cataluña",
    "52": "Comunitat Valenciana",
    "53": "Illes Balears",
    "61": "Andalucía",
    "62": "Región de Murcia",
    "63": "Ciudad de Ceuta",
    "64": "Ciudad de Melilla",
    "70": "Canarias",
    "ZZ": "Espacio marino plurirregional",
}

# Noise thresholds (dB LAeq) for ZEPA zones.
# Based on: normativa espacios naturales (sensibilidad acústica alta) +
# scientific literature on bird population response to noise.
# Safe: < 45 dB  |  Warning: 45–60 dB  |  Danger: > 60 dB
NOISE_THRESHOLDS: dict[str, int] = {
    "db_safe": 45,
    "db_warning": 60,
}


def _ccaa_from_local_id(local_id: str) -> str:
    """Derive the autonomous community name from a Red Natura 2000 localId."""
    code = local_id[2:4]  # characters at index 2-3, e.g. "ES41xxxx" → "41"
    return _CCAA_CODES.get(code, "Desconocida")


def _serialize_zone(feature: dict[str, Any]) -> dict[str, Any]:
    props = feature["properties"]
    local_id: str = props.get("localId", "")
    return {
        "id": local_id,
        "name": props.get("SOName", ""),
        "ccaa": _ccaa_from_local_id(local_id),
        "noise_thresholds": NOISE_THRESHOLDS,
        "geometry": feature["geometry"],
    }


def get_zepa_by_bbox(minLon: float, minLat: float, maxLon: float, maxLat: float) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for feature in GEOJSON["features"]:
        coords: list[list[float]] = feature["geometry"]["coordinates"][0]
        lons = [c[0] for c in coords]
        lats = [c[1] for c in coords]
        if max(lons) >= minLon and min(lons) <= maxLon and max(lats) >= minLat and min(lats) <= maxLat:
            results.append(_serialize_zone(feature))
    return results
