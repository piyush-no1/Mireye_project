import React, { useState } from 'react';
import { SearchBar } from '../components/SearchBar/SearchBar';
import { MapView } from '../components/MapView/MapView';
import { ResultsPanel } from '../components/ResultsPanel/ResultsPanel';
import { RiskScoreCard } from '../components/ResultsPanel/RiskScoreCard';
import { DataSourcesPanel } from '../components/DataSourcesPanel';
import { useCreateAssessment } from '../hooks/useCreateAssessment';
import { useAssessmentPolling } from '../hooks/useAssessmentPolling';
import { AlertCircle, HelpCircle, Loader2 } from 'lucide-react';

import { CreateAssessmentPayload } from '../api/assessments';

export const AssessmentPage: React.FC = () => {
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const [searchPayload, setSearchPayload] = useState<CreateAssessmentPayload | null>(null);
  const createMutation = useCreateAssessment();
  const { status, error, isLoading, result } = useAssessmentPolling(activeRunId);

  const handleSearch = (payload: CreateAssessmentPayload) => {
    setSearchPayload(payload);
    createMutation.mutate(payload, {
      onSuccess: (data) => {
        setActiveRunId(data.run_id);
      },
    });
  };

  // Active search if mutation is pending OR if polling status is pending OR if result is still loading
  const isSearching = createMutation.isPending || (activeRunId !== null && (status === 'pending' || isLoading));

  // Construct display result combining intermediate polling result or draft search payload
  const displayResult = result || (searchPayload ? {
    run_id: activeRunId || 'pending-run',
    status: 'pending' as const,
    query: searchPayload.query || 'Waterbody Corridor',
    segment_mode: Boolean(searchPayload.start_lat && searchPayload.end_lat),
    start_point: searchPayload.start_lat && searchPayload.start_lng ? {
      matched_name: 'Point A (Start)',
      lat: searchPayload.start_lat,
      lng: searchPayload.start_lng
    } : null,
    end_point: searchPayload.end_lat && searchPayload.end_lng ? {
      matched_name: 'Point B (End)',
      lat: searchPayload.end_lat,
      lng: searchPayload.end_lng
    } : null,
    resolved_location: searchPayload.start_lat && searchPayload.start_lng ? {
      matched_name: searchPayload.query || 'Selected Location',
      lat: searchPayload.start_lat,
      lng: searchPayload.start_lng
    } : null,
    hydrology: null,
    water_quality_samples: null,
    attains_status: null,
    polluters: null,
    land_risk_points: null,
    telemetry: null,
    risk_summary: null,
    errors: [],
    generated_at: new Date().toISOString()
  } : null);

  const isCompleted = result && (result.status === 'completed' || result.status === 'assessment_completed') && !isSearching;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', gap: '20px' }}>
      <SearchBar onSearch={handleSearch} isLoading={isSearching} />

      {/* Needs clarification banner */}
      {status === 'needs_clarification' && (
        <div style={{
          maxWidth: '800px',
          margin: '0 auto',
          width: '100%',
          background: 'rgba(245, 158, 11, 0.15)',
          border: '1px solid rgba(245, 158, 11, 0.4)',
          borderRadius: 'var(--radius-md)',
          padding: '16px',
          color: '#fde047',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <HelpCircle size={24} style={{ flexShrink: 0, color: '#f59e0b' }} />
          <div>
            <strong style={{ fontSize: '14px', display: 'block', color: '#f59e0b' }}>
              Ambiguous Location — Please Refine Search
            </strong>
            <span style={{ fontSize: '13px' }}>
              We couldn't resolve your waterbody query unambiguously. Please specify state or nearby city (e.g., "Potomac River near Great Falls, VA").
            </span>
          </div>
        </div>
      )}

      {/* Error state */}
      {error && !isSearching && (
        <div style={{
          maxWidth: '800px',
          margin: '0 auto',
          width: '100%',
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          borderRadius: 'var(--radius-md)',
          padding: '16px',
          color: '#fca5a5',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <AlertCircle size={24} style={{ flexShrink: 0, color: '#ef4444' }} />
          <div>
            <strong style={{ fontSize: '14px', display: 'block', color: '#ef4444' }}>
              Assessment Execution Failed
            </strong>
            <span style={{ fontSize: '13px' }}>
              {typeof error === 'string' ? error : (error as any)?.message || 'An unexpected error occurred during processing.'}
            </span>
          </div>
        </div>
      )}

      {/* Loading state before initial location resolution */}
      {isSearching && !displayResult?.resolved_location && !displayResult?.start_point && (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '50px 20px',
          background: 'var(--bg-card)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border-color)',
          gap: '16px',
          maxWidth: '800px',
          margin: '0 auto',
          width: '100%'
        }}>
          <Loader2 size={40} style={{ color: '#38bdf8' }} className="animate-spin" />
          <div style={{ fontSize: '17px', fontWeight: 600, color: '#38bdf8' }}>
            Geocoding Location & Initializing Agent Pipeline...
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)', textAlign: 'center', maxWidth: '500px' }}>
            Resolving coordinates ➔ Tracing USGS flowlines ➔ Retrieving Mireye & EPA data
          </div>
        </div>
      )}

      {/* Main split row: Map + ONLY Environmental Assessment Rating Card */}
      {displayResult && (displayResult.resolved_location || displayResult.start_point) && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(300px, 1fr) minmax(320px, 420px)',
          gap: '24px',
          minHeight: '520px'
        }}>
          {/* Map focused on selected waterbody segment/location continuously */}
          <MapView result={displayResult} />

          {/* Right side: ONLY Environmental Assessment Rating Card (or Live Inference Card during search) */}
          {isSearching ? (
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '40px 24px',
              background: 'var(--bg-card)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              gap: '16px',
              textAlign: 'center'
            }}>
              <Loader2 size={44} style={{ color: '#38bdf8' }} className="animate-spin" />
              <div>
                <div style={{ fontSize: '18px', fontWeight: 600, color: '#38bdf8', marginBottom: '6px' }}>
                  Multi-Agent Inference Running...
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                  Map focused on selected waterbody segment. Tracing USGS flowlines, querying EPA ECHO, Mireye land risk & computing severity.
                </div>
              </div>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <RiskScoreCard summary={result?.risk_summary || null} />
            </div>
          )}
        </div>
      )}

      {/* Full-width detailed diagnostic sections in order below Map & Rating */}
      {result && !isSearching && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', marginTop: '8px' }}>
          <ResultsPanel result={result} omitRatingCard={true} />
          <DataSourcesPanel result={result} />
        </div>
      )}
    </div>
  );
};

