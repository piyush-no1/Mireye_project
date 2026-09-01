from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AssessmentState(BaseModel):
    run_id: str
    query: str
    input_lat: Optional[float] = None
    input_lng: Optional[float] = None
    # Segment Mode fields
    is_segment_mode: bool = False
    start_lat: Optional[float] = None
    start_lng: Optional[float] = None
    end_lat: Optional[float] = None
    end_lng: Optional[float] = None
    start_name: Optional[str] = None
    end_name: Optional[str] = None
    start_location: Optional[Dict[str, Any]] = None
    end_location: Optional[Dict[str, Any]] = None
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
    industrial_analysis: Optional[Dict[str, Any]] = None
    agricultural_analysis: Optional[Dict[str, Any]] = None
    master_synthesis: Optional[Dict[str, Any]] = None
    source_attribution: Optional[Dict[str, Any]] = None
    source_investigation_log: List[Dict[str, Any]] = Field(default_factory=list)
    errors: List[Dict[str, str]] = Field(default_factory=list)
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)
