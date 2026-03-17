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
- Returns zone name, autonomous community, geometry, and noise thresholds
- Data: Red Natura 2000, MITECO (CC BY 4.0), 602 zones


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
      "name": "Cuenca del río Manzanares",
      "ccaa": "Comunidad de Madrid",
      "noise_thresholds": { "db_safe": 45, "db_warning": 60 },
      "geometry": { "type": "MultiPolygon", "coordinates": ["..."] }
    }
  ],
  "metadata": { "count": 1 }
}
```

> See [`docs/zepa.md`](docs/zepa.md) for data preparation instructions.
