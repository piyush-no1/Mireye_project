export interface InvestigationLogEntry {
  round: number;
  tool: string;
  reason: string;
  arguments: Record<string, any>;
  result_status: 'success' | 'unavailable' | 'error';
  source: string;
  summary: string;
}

export interface SourceCandidate {
  source_type: string;
  source_name: string;
  source_id: string | null;
  latitude: number | null;
  longitude: number | null;
  geography_type: 'point' | 'watershed' | 'assessment_unit' | 'polygon' | 'region' | 'unknown';
  geography_id: string | null;
  relationship_to_primary_path: 'upstream' | 'downstream' | 'adjacent' | 'within_watershed' | 'tributary_connected' | 'disconnected' | 'unknown';
  attribution: 'DOCUMENTED' | 'LIKELY' | 'POSSIBLE' | 'UNSUPPORTED';
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  supporting_evidence: string[];
  contradicting_evidence: string[];
  evidence_sources: string[];
}

export interface Impairment {
  impairment: string;
  affected_uses: string[];
  sources: SourceCandidate[];
}

export interface SourceAttributionData {
  impairments: Impairment[];
  major_source_findings: string[];
  source_data_gaps: string[];
  overall_source_reasoning: string;
}
