import React from 'react';
import { AssessmentResult } from '../../types/assessment';
import { Search, MapPin, Database, CheckCircle, AlertTriangle, XCircle, Loader2, HelpCircle } from 'lucide-react';

interface SourceAttributionCardProps {
  result: AssessmentResult;
}

export const SourceAttributionCard: React.FC<SourceAttributionCardProps> = ({ result }) => {
  const isRunning = result.status === 'assessment_completed';
  const sourceAttribution = result.source_attribution;

  if (isRunning) {
    return (
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-md)',
        padding: '20px',
        marginBottom: '16px',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '12px'
      }}>
        <Loader2 size={32} style={{ color: '#8b5cf6' }} className="animate-spin" />
        <div style={{ fontSize: '15px', fontWeight: 600, color: '#8b5cf6' }}>
          Investigating Pollution Sources...
        </div>
        <div style={{ fontSize: '13px', color: 'var(--text-muted)', textAlign: 'center' }}>
          The Source Reasoning Agent is dynamically analyzing spatial and environmental data to identify likely contributors.
        </div>
      </div>
    );
  }

  if (!sourceAttribution) {
    return null; // Not running and no data
  }

  const renderAttributionIcon = (attribution: string) => {
    switch (attribution) {
      case 'DOCUMENTED': return <CheckCircle size={14} style={{ color: '#10b981' }} />;
      case 'LIKELY': return <AlertTriangle size={14} style={{ color: '#f59e0b' }} />;
      case 'POSSIBLE': return <HelpCircle size={14} style={{ color: '#38bdf8' }} />;
      case 'UNSUPPORTED': return <XCircle size={14} style={{ color: '#ef4444' }} />;
      default: return null;
    }
  };

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-md)',
      padding: '20px',
      marginBottom: '16px'
    }}>
      <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Search size={18} style={{ color: '#8b5cf6' }} />
        <span>Source Attribution</span>
      </h3>
      
      <div style={{ marginBottom: '16px', fontSize: '13px', color: 'var(--text-secondary)' }}>
        <strong>Overall Reasoning:</strong> {sourceAttribution.overall_source_reasoning}
      </div>

      {sourceAttribution.impairments?.map((imp: any, idx: number) => (
        <div key={idx} style={{
          background: 'rgba(15, 23, 42, 0.4)',
          borderRadius: 'var(--radius-sm)',
          padding: '12px',
          marginBottom: '12px'
        }}>
          <div style={{ fontWeight: 600, color: '#f87171', marginBottom: '8px' }}>
            Impairment: {imp.impairment}
          </div>
          
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {imp.sources?.map((source: any, sIdx: number) => (
              <div key={sIdx} style={{
                background: 'var(--bg-elevated)',
                border: '1px solid var(--border-color)',
                borderRadius: 'var(--radius-sm)',
                padding: '10px',
                fontSize: '13px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                  <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{source.source_name || source.source_type}</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)' }}>
                    {renderAttributionIcon(source.attribution)}
                    {source.attribution}
                  </span>
                </div>
                
                <div style={{ display: 'grid', gridTemplateColumns: 'auto 1fr', gap: '6px', fontSize: '12px', color: 'var(--text-secondary)' }}>
                  <MapPin size={12} style={{ marginTop: '2px' }} />
                  <span>Relationship: {source.relationship_to_primary_path}</span>
                  
                  <Database size={12} style={{ marginTop: '2px' }} />
                  <span>Evidence: {source.evidence_sources?.join(', ')}</span>
                </div>
                
                {source.supporting_evidence?.length > 0 && (
                  <div style={{ marginTop: '8px', fontSize: '12px', color: '#10b981' }}>
                    <strong>Supports:</strong> {source.supporting_evidence.join('; ')}
                  </div>
                )}
                
                {source.contradicting_evidence?.length > 0 && (
                  <div style={{ marginTop: '4px', fontSize: '12px', color: '#ef4444' }}>
                    <strong>Contradicts:</strong> {source.contradicting_evidence.join('; ')}
                  </div>
                )}
              </div>
            ))}
            {(!imp.sources || imp.sources.length === 0) && (
              <div style={{ fontSize: '12px', color: 'var(--text-subtle)' }}>No candidate sources identified.</div>
            )}
          </div>
        </div>
      ))}
      
      {sourceAttribution.source_data_gaps?.length > 0 && (
        <div style={{ marginTop: '12px', padding: '10px', background: 'rgba(245, 158, 11, 0.1)', borderRadius: 'var(--radius-sm)', fontSize: '12px', color: '#f59e0b' }}>
          <strong>Data Gaps:</strong> {sourceAttribution.source_data_gaps.join('; ')}
        </div>
      )}
    </div>
  );
};


