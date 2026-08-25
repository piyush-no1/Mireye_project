from typing import List, Dict, Any, Optional, Literal
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

class AttainsSummary(BaseModel):
    assessment_units: int = 0
    supporting_units: int = 0
    impaired_units: int = 0
    designated_use_summary: Dict[str, Any] = Field(default_factory=dict)
    persistent_impairments: List[Dict[str, Any]] = Field(default_factory=list)
    new_impairments: List[Dict[str, Any]] = Field(default_factory=list)
    resolved_impairments: List[Dict[str, Any]] = Field(default_factory=list)
    major_causes: List[Dict[str, Any]] = Field(default_factory=list)
    probable_sources: List[Dict[str, Any]] = Field(default_factory=list)
    tmdl_actions: List[Dict[str, Any]] = Field(default_factory=list)
    historical_trend: str = "Unknown"
    source: str = "ATTAINS"
    retrieval_timestamp: str = ""

class AttainsStatus(BaseModel):
    assessment_unit_id: str
    waterbody_name: Optional[str] = None
    assessment_cycle: str
    overall_status: str
    uses: List[Dict[str, Any]] = Field(default_factory=list)
    impairments: List[Dict[str, Any]] = Field(default_factory=list)
    history: List[Dict[str, Any]] = Field(default_factory=list)
    tmdl_actions: List[Dict[str, Any]] = Field(default_factory=list)
    source: str = "ATTAINS"
    geometry: Optional[Dict[str, Any]] = None

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

class HypothesisItem(BaseModel):
    hypothesis: str
    initial_reasoning: str
    data_needed_to_confirm: List[str] = Field(default_factory=list)

class HypothesisGenerationOutput(BaseModel):
    segment_id: str
    hypotheses: List[HypothesisItem] = Field(default_factory=list)
    insufficient_evidence: bool = False

class EvidenceSynthesisOutput(BaseModel):
    segment_id: str
    final_cause: str
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    confidence: Literal["high", "medium", "low"] = "medium"
    alternative_explanations_considered: List[str] = Field(default_factory=list)
    grade_contribution_notes: str = ""

class RiskSummary(BaseModel):
    rating: str = "A"
    label: str = "Low Risk"
    risk_factors: List[str] = Field(default_factory=list)
    mitigating_factors: List[str] = Field(default_factory=list)
    temporal_assessment: str = ""
    spatial_assessment: str = ""
    data_limitations: str = ""
    notes: str = ""
    scoring_engine: str = "openai_reasoning_agent"

class StageError(BaseModel):
    stage: str
    tool: str
    message: str

class AssessmentResult(BaseModel):
    run_id: str
    status: str  # completed | failed | needs_clarification
    query: str
    segment_mode: bool = False
    start_point: Optional[ResolvedLocation] = None
    end_point: Optional[ResolvedLocation] = None
    resolved_location: Optional[ResolvedLocation] = None
    hydrology: Optional[HydrologyData] = None
    water_quality_samples: Optional[List[WaterQualitySample]] = None
    attains_status: Optional[List[AttainsStatus]] = None
    attains_summary: Optional[AttainsSummary] = None
    polluters: Optional[List[PolluterFacility]] = None
    land_risk_points: Optional[List[LandRiskPoint]] = None
    telemetry: Optional[List[TelemetryData]] = None
    hypothesis_generation: Optional[HypothesisGenerationOutput] = None
    targeted_evidence: Optional[Dict[str, Any]] = None
    evidence_synthesis: Optional[EvidenceSynthesisOutput] = None
    risk_summary: Optional[RiskSummary] = None
    source_attribution: Optional[Dict[str, Any]] = None
    source_investigation_log: Optional[List[Dict[str, Any]]] = None
    errors: List[StageError] = Field(default_factory=list)
    execution_log: List[Dict[str, Any]] = Field(default_factory=list)
    generated_at: str
