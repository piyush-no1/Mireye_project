import React, { useState } from 'react';
import { AssessmentResult } from '../../types/assessment';
import { Activity, ChevronDown, ChevronUp, Database } from 'lucide-react';

interface MireyeAgentLogCardProps {
  result: AssessmentResult;
}

export const MireyeAgentLogCard: React.FC<MireyeAgentLogCardProps> = ({ result }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const calls = result.source_investigation_log;

  // Don't show if source attribution hasn't completed or if there are no calls
  if (!calls) {
    return null;
  }

  if (calls.length === 0) {
    return (
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-md)',
        padding: '16px 20px',
        marginBottom: '16px',
        display: 'flex',
        alignItems: 'center',
        gap: '10px'
      }}>
        <Activity size={18} style={{ color: 'var(--text-muted)' }} />
        <span style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
          The Source Reasoning Agent did not need to call the Mireye API for this assessment.
        </span>
      </div>
    );
  }

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-md)',
      padding: '20px',
      marginBottom: '16px'
    }}>
      <div 
        style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', cursor: 'pointer' }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px', margin: 0 }}>
          <Activity size={18} style={{ color: '#0ea5e9' }} />
          <span>Mireye API Agent Log</span>
        </h3>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            background: 'rgba(14, 165, 233, 0.1)',
            color: '#0ea5e9',
            padding: '2px 8px',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: 600
          }}>
            {calls.length} Call{calls.length > 1 ? 's' : ''} Made
          </div>
          {isExpanded ? <ChevronUp size={18} style={{ color: 'var(--text-muted)' }} /> : <ChevronDown size={18} style={{ color: 'var(--text-muted)' }} />}
        </div>
      </div>

      {isExpanded && (
        <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {calls.map((call: any, idx: number) => {
            let displayResponse = '';
            try {
              displayResponse = JSON.stringify(call.arguments, null, 2);
            } catch (e) {
              displayResponse = String(call.arguments);
            }

            return (
              <div key={idx} style={{
                background: 'rgba(15, 23, 42, 0.5)',
                border: '1px solid rgba(14, 165, 233, 0.2)',
                borderRadius: 'var(--radius-sm)',
                padding: '12px',
                fontSize: '13px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px', color: '#0ea5e9', fontWeight: 600 }}>
                  <Database size={14} />
                  Round {call.round}: {call.tool}
                </div>
                <div style={{ marginBottom: '8px', color: 'var(--text-main)' }}>
                  <strong>Reason:</strong> {call.reason}
                </div>
                <div style={{ 
                  background: 'var(--bg-elevated)', 
                  padding: '8px', 
                  borderRadius: '4px',
                  maxHeight: '200px',
                  overflowY: 'auto',
                  fontFamily: 'monospace',
                  fontSize: '11px',
                  whiteSpace: 'pre-wrap',
                  color: 'var(--text-secondary)'
                }}>
                  {displayResponse}
                </div>
                <div style={{ marginTop: '8px', color: 'var(--text-muted)' }}>
                  <strong>Summary:</strong> {call.summary}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
