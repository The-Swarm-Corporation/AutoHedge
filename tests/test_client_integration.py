import sys
from unittest.mock import MagicMock
sys.modules['swarms'] = MagicMock()
sys.modules['swarms.utils'] = MagicMock()
sys.modules['swarms.utils.any_to_str'] = MagicMock()

import pytest
from fastapi.testclient import TestClient

from autohedge.api.main import app

client = TestClient(app)

def test_serve_index():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "AutoHedge" in response.text
    assert "<form id=\"task-form\"" in response.text

def test_api_routes_still_work():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
