import json
import sys
from unittest.mock import MagicMock
sys.modules['swarms'] = MagicMock()
sys.modules['swarms.utils'] = MagicMock()
sys.modules['swarms.utils.any_to_str'] = MagicMock()

from unittest.mock import patch
import asyncio

import time
import pytest
from fastapi.testclient import TestClient

from autohedge.api.main import app
from autohedge.api import job_manager

client = TestClient(app)

@pytest.fixture(autouse=True)
def clear_jobs():
    job_manager._jobs.clear()

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

@patch("autohedge.api.job_manager.AutoHedge.run")
def test_analyze_valid_request_and_flow(mock_run):
    # Mock synchronous result
    mock_run.return_value = [{"role": "director", "content": "mocked structured result"}]

    # 1. Create Job
    response = client.post("/api/analyze", json={"task": "Test task"})
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "pending"
    job_id = data["job_id"]

    # Allow background task to execute
    # Since we are using TestClient and asyncio.create_task in job_manager,
    # the task runs in the current event loop. We can yield to let it finish.
    for _ in range(20):
        if job_manager.get_job(job_id)["status"] in ["completed", "failed"]:
            break
        time.sleep(0.1)

    # 2. Poll Job
    response = client.get(f"/api/analyze/{job_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "completed"
    assert data["result"] == [{"role": "director", "content": "mocked structured result"}]
    assert data["error"] is None

@patch("autohedge.api.job_manager.AutoHedge.run")
def test_analyze_job_failure(mock_run):
    mock_run.side_effect = Exception("Mocked execution failure")

    response = client.post("/api/analyze", json={"task": "Fail task"})
    job_id = response.json()["job_id"]

    for _ in range(20):
        if job_manager.get_job(job_id)["status"] in ["completed", "failed"]:
            break
        time.sleep(0.1)

    response = client.get(f"/api/analyze/{job_id}")
    data = response.json()
    assert data["status"] == "failed"
    assert data["result"] is None
    assert "Mocked execution failure" in data["error"]

def test_analyze_invalid_request():
    response = client.post("/api/analyze", json={"task": ""})
    assert response.status_code == 422
    assert "Task cannot be empty" in response.json()["detail"]

def test_analyze_unknown_job():
    response = client.get("/api/analyze/invalid-uuid")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found"
