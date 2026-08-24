export interface ResolvedLocation {
  matched_name: string;
  lat: number;
  lng: number;
}

import { SourceAttributionData, InvestigationLogEntry } from './sourceAttribution';

export interface HydrologyData {
  comid: string;
  flowline_geojson: any;
  bbox: [number, number, number, number];
  _bank_points?: Array<{ lat: number; lng: number }>;
}

export interface WaterQualitySample {
  monitoring_location_id: string;
  characteristic_name: string;
  result_value: number | null;
  unit_code?: string;
  activity_start_date?: string;
  lat?: number;
  lng?: number;
}

export interface AttainsSummary {
  assessment_units: number;
  supporting_units: number;
  impaired_units: number;
  designated_use_summary: Record<string, any>;
  persistent_impairments: any[];
  new_impairments: any[];
  resolved_impairments: any[];
  major_causes: any[];
  probable_sources: any[];
  tmdl_actions: any[];
  historical_trend: string;
  source: string;
  retrieval_timestamp: string;
}

export interface AttainsStatus {
  assessment_unit_id: string;
  waterbody_name?: string;
  assessment_cycle: string;
  overall_status: string;
  uses: any[];
  impairments: any[];
  history: any[];
  tmdl_actions: any[];
  source: string;
  geometry?: any;
}

export interface PolluterFacility {
  source_id: string;
  facility_name: string;
  lat: number;
  lng: number;
  permit_status: string;
  effluent_exceedances: number;
  quarters_in_noncompliance: number;
}

export interface LandRiskPoint {
  lat: number;
  lng: number;
  slope_degrees: number;
  elevation: number;
  lcms_class: string;
  tree_canopy_pct: number;
  ndvi_current: number;
  ndvi_change_5y: number;
  fema_flood_zone: string;
}

export interface TelemetryData {
  site_id: string;
  discharge_cfs: number | null;
  gage_height_ft: number | null;
  water_temp_c: number | null;
  date_time: string | null;
}

export interface RiskSummary {
  rating: string;
  label: string;
  risk_factors: string[];
  mitigating_factors: string[];
  temporal_assessment: string;
  spatial_assessment: string;
  data_limitations: string;
  notes: string;
}

export interface StageError {
  stage: string;
  tool: string;
  message: string;
}

export interface AssessmentResult {
  run_id: string;
  status: 'pending' | 'assessment_completed' | 'completed' | 'failed' | 'needs_clarification';
  query: string;
  segment_mode?: boolean;
  start_point?: ResolvedLocation | null;
  end_point?: ResolvedLocation | null;
  resolved_location: ResolvedLocation | null;
  hydrology: HydrologyData | null;
  water_quality_samples: WaterQualitySample[] | null;
  attains_status: AttainsStatus[] | null;
  attains_summary?: AttainsSummary | null;
  polluters: PolluterFacility[] | null;
  land_risk_points: LandRiskPoint[] | null;
  telemetry: TelemetryData[] | null;
  risk_summary: RiskSummary | null;
  source_attribution?: SourceAttributionData | null;
  source_investigation_log?: InvestigationLogEntry[];
  errors: StageError[];
  execution_log?: Array<Record<string, any>>;
  generated_at: string;
}

export interface AssessmentStatusResponse {
  run_id: string;
  status: 'pending' | 'assessment_completed' | 'completed' | 'failed' | 'needs_clarification';
  error: string | null;
}
