from typing import Any, Optional, Dict
from pydantic import BaseModel, Field

class AnalysisRequest(BaseModel):
    task: str = Field(..., description="The task to analyze (e.g., 'Analyze NVDA for 50k allocation')")

class AnalysisJobResponse(BaseModel):
    job_id: str = Field(..., description="Unique identifier for the analysis job")
    status: str = Field(..., description="Current status of the job (pending, running, completed, failed)")

class AnalysisStatusResponse(BaseModel):
    job_id: str
    status: str
    result: Optional[Any] = Field(None, description="The result list of logs for each stock from AutoHedge")
    error: Optional[str] = Field(None, description="Error message if the job failed")

class ErrorResponse(BaseModel):
    status: str = "error"
    error: str
