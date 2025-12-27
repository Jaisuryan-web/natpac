from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root123",     # change if needed
    database="natpac_travel"
)

cursor = db.cursor(dictionary=True)

@app.route("/")
def root():
    return send_from_directory(".", "index.html")

@app.route("/start")
def start_page():
    return send_from_directory(".", "start.html")

@app.route("/history")
def history_page():
    return send_from_directory(".", "history.html")

@app.route("/saveTrip", methods=["POST"])
def save_trip():
    data = request.json

    query = """
    INSERT INTO trips (latitude, longitude, mode, purpose, cost)
    VALUES (%s, %s, %s, %s, %s)
    """

    values = (
        data["latitude"],
        data["longitude"],
        data["mode"],
        data["purpose"],
        data["cost"]
    )

    cursor.execute(query, values)
    db.commit()

    return jsonify({"status": "saved"})

@app.route("/trips", methods=["GET"])
def trips():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    params = []
    where = []
    if start_date:
        where.append("DATE(created_at) >= %s")
        params.append(start_date)
    if end_date:
        where.append("DATE(created_at) <= %s")
        params.append(end_date)
    base = "SELECT * FROM trips"
    if where:
        base += " WHERE " + " AND ".join(where)
    base += " ORDER BY id DESC LIMIT 500"
    cursor.execute(base, params)
    rows = cursor.fetchall()
    return jsonify(rows)

@app.route("/trips", methods=["DELETE"])
def clear_trips():
    cursor.execute("DELETE FROM trips")
    db.commit()
    return jsonify({"status": "cleared", "deleted": cursor.rowcount})

@app.route("/trips_geo", methods=["GET"])
def trips_geo():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    params = []
    where = []
    if start_date:
        where.append("DATE(created_at) >= %s")
        params.append(start_date)
    if end_date:
        where.append("DATE(created_at) <= %s")
        params.append(end_date)
    base = "SELECT id, latitude, longitude, mode, purpose, cost FROM trips"
    if where:
        base += " WHERE " + " AND ".join(where)
    base += " ORDER BY id DESC LIMIT 1000"
    cursor.execute(base, params)
    rows = cursor.fetchall()
    features = []
    for r in rows:
        try:
            lat = float(r["latitude"]) if isinstance(r["latitude"], (int, float, str)) else None
            lon = float(r["longitude"]) if isinstance(r["longitude"], (int, float, str)) else None
        except Exception:
            lat, lon = None, None
        if lat is None or lon is None:
            continue
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lon, lat]},
            "properties": {
                "id": r.get("id"),
                "mode": r.get("mode"),
                "purpose": r.get("purpose"),
                "cost": r.get("cost"),
            },
        })
    return jsonify({"type": "FeatureCollection", "features": features})

if __name__ == "__main__":
    app.run(debug=True)
