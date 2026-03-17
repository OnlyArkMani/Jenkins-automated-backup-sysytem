import json
import pytest
from unittest.mock import patch, MagicMock

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app import app, init_db, fetch_weather




@pytest.fixture
def client(tmp_path):
    """Create a test Flask client with an isolated SQLite DB."""
    app.config["TESTING"] = True
    os.environ["DB_PATH"] = str(tmp_path / "test.db")
    with app.app_context():
        init_db()
    with app.test_client() as c:
        yield c


MOCK_WEATHER_RESPONSE = {
    "name": "London",
    "sys": {"country": "GB"},
    "main": {
        "temp": 15.3,
        "feels_like": 13.8,
        "humidity": 72,
        "pressure": 1013,
    },
    "wind": {"speed": 4.2},
    "weather": [{"main": "Clouds", "description": "overcast clouds", "icon": "04d"}],
    "visibility": 10000,
}




def test_index_returns_200(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert b"atmos" in resp.data.lower() or b"weather" in resp.data.lower()


def test_health_endpoint(client):
    resp = client.get("/health")
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_weather_api_missing_city(client):
    resp = client.get("/api/weather")
    data = json.loads(resp.data)
    assert resp.status_code == 400
    assert data["status"] == "error"


def test_weather_api_empty_city(client):
    resp = client.get("/api/weather?city=")
    data = json.loads(resp.data)
    assert resp.status_code == 400
    assert data["status"] == "error"


@patch("app.requests.get")
def test_weather_api_success(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_WEATHER_RESPONSE
    mock_get.return_value = mock_resp

    resp = client.get("/api/weather?city=London")
    data = json.loads(resp.data)

    assert resp.status_code == 200
    assert data["status"] == "ok"
    assert data["data"]["city"] == "London"
    assert data["data"]["country"] == "GB"
    assert data["data"]["temp"] == 15.3
    assert data["data"]["humidity"] == 72


@patch("app.requests.get")
def test_weather_api_city_not_found(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_get.return_value = mock_resp

    resp = client.get("/api/weather?city=FakeCity123")
    data = json.loads(resp.data)

    assert resp.status_code == 400
    assert data["status"] == "error"
    assert "not found" in data["message"].lower()


@patch("app.requests.get")
def test_weather_api_invalid_key(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_get.return_value = mock_resp

    resp = client.get("/api/weather?city=London")
    data = json.loads(resp.data)

    assert resp.status_code == 500
    assert data["status"] == "error"


def test_recent_searches_empty(client):
    resp = client.get("/api/recent")
    data = json.loads(resp.data)
    assert resp.status_code == 200
    assert data["status"] == "ok"
    assert isinstance(data["data"], list)


@patch("app.requests.get")
def test_recent_searches_populated(mock_get, client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_WEATHER_RESPONSE
    mock_get.return_value = mock_resp

    client.get("/api/weather?city=London")

    resp = client.get("/api/recent")
    data = json.loads(resp.data)
    assert len(data["data"]) >= 1
    assert data["data"][0]["city"] == "London"




def test_fetch_weather_empty_string():
    with pytest.raises(ValueError, match="empty"):
        fetch_weather("")


def test_fetch_weather_whitespace():
    with pytest.raises(ValueError):
        fetch_weather("   ")


@patch("app.requests.get")
def test_fetch_weather_timeout(mock_get):
    import requests as req
    mock_get.side_effect = req.exceptions.Timeout
    with pytest.raises(RuntimeError, match="timed out"):
        fetch_weather("London")


@patch("app.requests.get")
def test_fetch_weather_connection_error(mock_get):
    import requests as req
    mock_get.side_effect = req.exceptions.ConnectionError
    with pytest.raises(RuntimeError, match="connect"):
        fetch_weather("London")


@patch("app.requests.get")
def test_fetch_weather_returns_normalised_data(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = MOCK_WEATHER_RESPONSE
    mock_get.return_value = mock_resp

    result = fetch_weather("London")

    assert result["city"] == "London"
    assert result["temp"] == 15.3
    assert result["humidity"] == 72
    assert result["wind_speed"] == 4.2
    assert result["visibility"] == 10        # 10000m → 10km
    assert result["description"] == "Overcast Clouds"