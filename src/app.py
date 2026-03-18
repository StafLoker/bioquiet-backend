from flask import Flask, jsonify, request, Response
from zepa_data import get_zepa_by_bbox

app = Flask(__name__)


def success(data: object, message: str = "", metadata: dict = {}) -> Response:
    return jsonify({
        "status": "success",
        "message": message,
        "data": data,
        "metadata": metadata,
    })


def error(message: str, metadata: dict = {}) -> tuple[Response, int]:
    return jsonify({
        "status": "error",
        "message": message,
        "data": None,
        "metadata": metadata,
    }), 400


@app.route("/api/v1/zepa")
def zepa() -> Response:
    params = request.args
    missing = [p for p in ("lonWest", "latSouth", "lonEast", "latNorth") if p not in params]
    if missing:
        return error(f"Missing required query parameters: {', '.join(missing)}")
    try:
        minLon = float(params["lonWest"])
        minLat = float(params["latSouth"])
        maxLon = float(params["lonEast"])
        maxLat = float(params["latNorth"])
    except ValueError:
        return error("Query parameters must be valid decimal numbers")

    zones = get_zepa_by_bbox(minLon, minLat, maxLon, maxLat)
    count = len(zones)
    message = f"{count} ZEPA zone{'s' if count != 1 else ''} found in the requested area." if count else "No ZEPA zones found in the requested area."
    return success(
        data=zones,
        message=message,
        metadata={"count": count},
    )


if __name__ == "__main__":
    import os
    app.run(port=int(os.environ.get("PORT", 5000)))
