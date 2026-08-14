import threading
import uuid
import traceback
from typing import Dict, Any

from autohedge.main import AutoHedge
from loguru import logger

# In-memory store: job_id -> dict with status, result, error
_jobs: Dict[str, Dict[str, Any]] = {}

def create_job() -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "status": "pending",
        "result": None,
        "error": None
    }
    return job_id

def get_job(job_id: str) -> Dict[str, Any]:
    return _jobs.get(job_id)

def _execute_job_sync(job_id: str, task: str):
    """Background task to run AutoHedge logic."""
    try:
        _jobs[job_id]["status"] = "running"
        logger.info(f"Job {job_id} starting with task: {task}")
        
        system = AutoHedge()
        result = system.run(task=task)
        
        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["result"] = result
        logger.info(f"Job {job_id} completed successfully")
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}\n{traceback.format_exc()}")
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)

def submit_job(task: str) -> str:
    """Creates a job and schedules its background execution."""
    job_id = create_job()
    thread = threading.Thread(target=_execute_job_sync, args=(job_id, task))
    thread.start()
    return job_id
