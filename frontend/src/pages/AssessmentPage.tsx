import React, { useState } from 'react';
import { SearchBar } from '../components/SearchBar/SearchBar';
import { MapView } from '../components/MapView/MapView';
import { ResultsPanel } from '../components/ResultsPanel/ResultsPanel';
import { useCreateAssessment } from '../hooks/useCreateAssessment';
import { useAssessmentPolling } from '../hooks/useAssessmentPolling';
import { AlertCircle, HelpCircle, Loader2 } from 'lucide-react';

export const AssessmentPage: React.FC = () => {
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  const createMutation = useCreateAssessment();
  const { status, error, isLoading, result } = useAssessmentPolling(activeRunId);

  const handleSearch = (query: string) => {
    createMutation.mutate(query, {
      onSuccess: (data) => {
        setActiveRunId(data.run_id);
      },
    });
  };

  // Active search if mutation is pending OR if polling status is pending OR if result is still loading
  const isSearching = createMutation.isPending || (activeRunId !== null && (status === 'pending' || isLoading));

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

      {/* Pending spinner overlay */}
      {isSearching && (
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
            LangGraph Agent Pipeline Running...
          </div>
          <div style={{ fontSize: '13px', color: 'var(--text-muted)', textAlign: 'center', maxWidth: '500px' }}>
            Geocoding location ➔ Tracing USGS flowlines ➔ Concurrent EPA & Mireye tool retrieval ➔ Computing risk score
          </div>
        </div>
      )}

      {/* Main split dashboard: Map + Results Panel */}
      {result && result.status === 'completed' && !isSearching && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(300px, 1fr) minmax(350px, 450px)',
          gap: '24px',
          flex: 1,
          minHeight: '550px'
        }}>
          <MapView result={result} />
          <ResultsPanel result={result} />
        </div>
      )}
    </div>
  );
};
