import re

from fastapi.testclient import TestClient

from src.photo_archivist.app import app


def test_health_returns_ok_and_version():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("application/json")
    data = resp.json()
    # required keys
    assert data.get("ok") is True
    assert "version" in data
    # semver-like version
    assert re.match(r"^\d+\.\d+\.\d+$", data["version"])
    # service name
    assert data.get("service") == "photo-archivist"
