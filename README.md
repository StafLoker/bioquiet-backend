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

Full API reference (OpenAPI): https://stafloker.github.io/bioquiet-backend/

> See [`docs/zepa.md`](docs/zepa.md) for geometry data preparation instructions.
> See [`docs/cntryes.md`](docs/cntryes.md) for ecological metadata preparation instructions.
