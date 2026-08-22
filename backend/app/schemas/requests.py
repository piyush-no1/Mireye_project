from typing import Optional
from pydantic import BaseModel

class CreateAssessmentRequest(BaseModel):
    query: str

class CreateAssessmentResponse(BaseModel):
    run_id: str
    status: str  # pending

class AssessmentStatusResponse(BaseModel):
    run_id: str
    status: str  # pending | completed | failed | needs_clarification
    error: Optional[str] = None
