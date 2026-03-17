
import os
import sqlite3
import logging
from datetime import datetime

import requests
from flask import Flask, render_template, request, jsonify

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


app = Flask(__name__)

API_KEY = os.getenv("OPENWEATHER_API_KEY", "demo_key")
API_URL = "https://api.openweathermap.org/data/2.5/weather"
DB_PATH = os.getenv("DB_PATH", "weather.db")


def get_db():
    """Return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create the searches table if it doesn't exist."""
    with get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS searches (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                city      TEXT    NOT NULL,
                country   TEXT,
                temp      REAL,
                condition TEXT,
                searched_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
    logger.info("Database initialised.")


def save_search(city, country, temp, condition):
    """Persist a search record."""
    with get_db() as conn:
        conn.execute(
            "INSERT INTO searches (city, country, temp, condition, searched_at) VALUES (?,?,?,?,?)",
            (city, country, temp, condition, datetime.utcnow().isoformat()),
        )
        conn.commit()


def get_recent_searches(limit=5):
    """Return the most recent unique city searches."""
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT city, country, temp, condition, searched_at
            FROM searches
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]



def fetch_weather(city: str) -> dict:
    """
    Call OpenWeatherMap and return a normalised dict.
    Raises ValueError on bad city, RuntimeError on API issues.
    """
    if not city or not city.strip():
        raise ValueError("City name cannot be empty.")

    params = {"q": city.strip(), "appid": API_KEY, "units": "metric"}

    try:
        resp = requests.get(API_URL, params=params, timeout=5)
    except requests.exceptions.Timeout:
        raise RuntimeError("Weather API timed out. Please try again.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("Cannot reach weather service. Check your connection.")

    if resp.status_code == 404:
        raise ValueError(f"City '{city}' not found. Check spelling and try again.")
    if resp.status_code == 401:
        raise RuntimeError("Invalid API key. Set OPENWEATHER_API_KEY env variable.")
    if resp.status_code != 200:
        raise RuntimeError(f"Unexpected API error (HTTP {resp.status_code}).")

    data = resp.json()

    return {
        "city": data["name"],
        "country": data["sys"]["country"],
        "temp": round(data["main"]["temp"], 1),
        "feels_like": round(data["main"]["feels_like"], 1),
        "humidity": data["main"]["humidity"],
        "pressure": data["main"]["pressure"],
        "wind_speed": data["wind"]["speed"],
        "condition": data["weather"][0]["main"],
        "description": data["weather"][0]["description"].title(),
        "icon": data["weather"][0]["icon"],
        "visibility": data.get("visibility", 0) // 1000,  # km
    }



@app.route("/")
def index():
    recent = get_recent_searches()
    return render_template("index.html", recent=recent)


@app.route("/api/weather")
def api_weather():
    """
    GET /api/weather?city=<name>
    Returns JSON weather data or an error message.
    """
    city = request.args.get("city", "").strip()
    try:
        weather = fetch_weather(city)
        save_search(
            weather["city"],
            weather["country"],
            weather["temp"],
            weather["condition"],
        )
        logger.info("Weather fetched for %s, %s", weather["city"], weather["country"])
        return jsonify({"status": "ok", "data": weather})

    except ValueError as exc:
        logger.warning("Bad request: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 400

    except RuntimeError as exc:
        logger.error("Server error: %s", exc)
        return jsonify({"status": "error", "message": str(exc)}), 500


@app.route("/api/recent")
def api_recent():
    """GET /api/recent — returns last 5 searches."""
    return jsonify({"status": "ok", "data": get_recent_searches()})


@app.route("/health")
def health():
    """Health-check endpoint used by Nagios / K8s liveness probe."""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})



if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)