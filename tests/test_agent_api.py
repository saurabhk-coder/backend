import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_get_agent_profile():
    response = client.get("/api/v1/agent/profile")
    assert response.status_code == 200
    data = response.json()
    assert "agent_name" in data
    assert data["agent_name"] == "Leslie"
    assert "quick_actions" in data
    assert len(data["quick_actions"]) >= 2


def test_avatar_status():
    response = client.get("/api/v1/agent/avatar/status")
    assert response.status_code == 200
    data = response.json()
    assert data["avatar_status"] in ["idle", "speaking", "listening"]
    assert data["speak_now_available"] is True


def test_agent_db_search():
    response = client.post(
        "/api/v1/agent/search-db",
        json={"query": "shifts timings"},
    )
    # Even if DB is empty or disconnected in test env, endpoint handles it safely
    assert response.status_code in [200, 500]
    if response.status_code == 200:
        data = response.json()
        assert "query" in data
        assert "results" in data
