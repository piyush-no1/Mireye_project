from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AssessmentState(BaseModel):
    run_id: str
    query: str
    input_lat: Optional[float] = None
    input_lng: Optional[float] = None
    status: str = "pending"
    error_message: Optional[str] = None
    resolved_location: Optional[Dict[str, Any]] = None
    hydrology: Optional[Dict[str, Any]] = None
    water_quality_samples: List[Dict[str, Any]] = Field(default_factory=list)
    attains_status: List[Dict[str, Any]] = Field(default_factory=list)
    attains_summary: Optional[Dict[str, Any]] = None
    polluters: List[Dict[str, Any]] = Field(default_factory=list)
    land_risk_points: List[Dict[str, Any]] = Field(default_factory=list)
    telemetry: List[Dict[str, Any]] = Field(default_factory=list)
    risk_summary: Optional[Dict[str, Any]] = None
    errors: List[Dict[str, str]] = Field(default_factory=list)
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)
