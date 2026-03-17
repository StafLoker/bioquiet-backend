<div align="center">
   <img width="150" height="150" src="logo.png" alt="Logo">
   <h1><b>bioquiet-backend</b></h1>
   <p><i>~ REST API for ZEPA protected zones ~</i></p>
</div>

<div align="center">
   <p>Returns ZEPA (Special Bird Protection Areas) polygons and noise thresholds for a given bounding box.</p>
</div>


# Features

- Query ZEPA zones by bounding box (`minLon minLat maxLon maxLat`)
- Returns zone name, geometry, and noise thresholds
- Returns ecological metadata: habitats, species, threats, and management body
- Data: Red Natura 2000 cartography + CNTRYES database, MITECO (CC BY 4.0), 602 zones


# Installation

```bash
uv sync
```


# Usage

```bash
# Development
uv run python src/app.py

# Production
uv run gunicorn -w 2 -b 0.0.0.0:8000 --chdir src app:app
```

```
GET /api/v1/zepa?lonWest=-3.72&latSouth=40.38&lonEast=-3.68&latNorth=40.42
```

```json
{
  "status": "success",
  "message": "",
  "data": [
    {
      "id": "ES3000009",
      "name": "Cortados y cantiles de los ríos Jarama y Manzanares",
      "area_ha": 27983.0,
      "date_spa": "1993-12-01",
      "spa_legal_ref": null,
      "description": "Descripción ecológica del espacio...",
      "quality": "G",
      "habitats": [
        { "code": "6220", "description": "Pseudo-steppe with grasses...", "priority": true, "cover_ha": 120.5, "representativity": "B", "conservation": "B", "global_assessment": "B" }
      ],
      "species": [
        { "code": "A136", "name": "Charadrius dubius", "group": "Birds", "population_type": "c", "abundance": "P", "conservation": "C", "global": "C" }
      ],
      "impacts": [
        { "code": "D01.04", "description": "railway lines, TGV", "intensity": "MEDIUM", "occurrence": "IN", "type": "N" }
      ],
      "management": [
        { "org_name": "Comunidad de Madrid...", "org_email": "...", "plan_url": null, "measures": "..." }
      ],
      "noise_thresholds": { "db_safe": 45, "db_warning": 60 },
      "geometry": { "type": "MultiPolygon", "coordinates": ["..."] }
    }
  ],
  "metadata": { "count": 1 }
}
```

> See [`docs/zepa.md`](docs/zepa.md) for geometry data preparation instructions.
> See [`docs/cntryes.md`](docs/cntryes.md) for ecological metadata preparation instructions.
