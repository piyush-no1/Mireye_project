from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class MireyeGeocodeResponse(BaseModel):
    matched_name: str
    lat: float
    lng: float
    confidence: Optional[float] = 1.0

class USGSNLDIResponse(BaseModel):
    comid: str
    flowline_geojson: Dict[str, Any]

class NWISValue(BaseModel):
    value: str
    dateTime: str
    qualifiers: Optional[List[str]] = None

class NWISTimeSeries(BaseModel):
    variableCode: str
    values: List[NWISValue] = []

class USGSEchoFacility(BaseModel):
    source_id: str
    facility_name: str
    lat: float
    lng: float
    permit_status: str
    effluent_exceedances: int = 0
    quarters_in_noncompliance: int = 0
