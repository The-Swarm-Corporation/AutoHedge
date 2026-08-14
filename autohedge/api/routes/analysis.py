from fastapi import APIRouter, HTTPException
from autohedge.api.schemas import AnalysisRequest, AnalysisJobResponse, AnalysisStatusResponse
from autohedge.api.job_manager import submit_job, get_job

router = APIRouter()

@router.post("/analyze", response_model=AnalysisJobResponse)
def analyze(request: AnalysisRequest):
    if not request.task or not request.task.strip():
        raise HTTPException(status_code=422, detail="Task cannot be empty")
        
    job_id = submit_job(request.task)
    return {"job_id": job_id, "status": "pending"}

@router.get("/analyze/{job_id}", response_model=AnalysisStatusResponse)
def get_analysis_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
        
    return {
        "job_id": job_id,
        "status": job["status"],
        "result": job["result"],
        "error": job["error"]
    }
