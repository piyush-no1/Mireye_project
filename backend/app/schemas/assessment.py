from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ResolvedLocation(BaseModel):
    matched_name: str
    lat: float
    lng: float

class HydrologyData(BaseModel):
    comid: str
    flowline_geojson: Dict[str, Any]
    bbox: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0, 0.0])

class WaterQualitySample(BaseModel):
    monitoring_location_id: str
    characteristic_name: str
    result_value: Optional[float] = None
    unit_code: Optional[str] = "N/A"
    activity_start_date: Optional[str] = None

class AttainsStatus(BaseModel):
    assessment_unit_id: str
    overall_status: str
    use_attainment: Dict[str, Any] = Field(default_factory=dict)
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    tmdl_projects: List[Dict[str, Any]] = Field(default_factory=list)

class PolluterFacility(BaseModel):
    source_id: str
    facility_name: str
    lat: float
    lng: float
    permit_status: str
    effluent_exceedances: int = 0
    quarters_in_noncompliance: int = 0

class LandRiskPoint(BaseModel):
    lat: float
    lng: float
    slope_degrees: float = 0.0
    elevation: float = 0.0
    lcms_class: str = "Unknown"
    tree_canopy_pct: float = 0.0
    ndvi_current: float = 0.0
    ndvi_change_5y: float = 0.0
    fema_flood_zone: str = "X"

class TelemetryData(BaseModel):
    site_id: str
    discharge_cfs: Optional[float] = None
    gage_height_ft: Optional[float] = None
    water_temp_c: Optional[float] = None
    date_time: Optional[str] = None

class RiskSummary(BaseModel):
    overall_score: float = 0.0  # 0 to 100
    label: str = "Low Risk"
    notes: str = ""

class StageError(BaseModel):
    stage: str
    tool: str
    message: str

class AssessmentResult(BaseModel):
    run_id: str
    status: str  # completed | failed | needs_clarification
    query: str
    resolved_location: Optional[ResolvedLocation] = None
    hydrology: Optional[HydrologyData] = None
    water_quality_samples: Optional[List[WaterQualitySample]] = None
    attains_status: Optional[List[AttainsStatus]] = None
    polluters: Optional[List[PolluterFacility]] = None
    land_risk_points: Optional[List[LandRiskPoint]] = None
    telemetry: Optional[List[TelemetryData]] = None
    risk_summary: Optional[RiskSummary] = None
    errors: List[StageError] = Field(default_factory=list)
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)
    generated_at: str
