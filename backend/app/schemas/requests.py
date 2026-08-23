from typing import Optional
from pydantic import BaseModel

class CreateAssessmentRequest(BaseModel):
    query: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    # Segment Mode (Point A ➔ Point B)
    start_lat: Optional[float] = None
    start_lng: Optional[float] = None
    end_lat: Optional[float] = None
    end_lng: Optional[float] = None
    start_name: Optional[str] = None
    end_name: Optional[str] = None

class CreateAssessmentResponse(BaseModel):
    run_id: str
    status: str  # pending

class AssessmentStatusResponse(BaseModel):
    run_id: str
    status: str  # pending | completed | failed | needs_clarification
    error: Optional[str] = None
