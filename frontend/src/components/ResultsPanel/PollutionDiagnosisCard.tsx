import React from 'react';
import { IndustrialAnalysis, AgriculturalAnalysis, MasterSynthesis } from '../../types/assessment';
import { CheckCircle2, Activity } from 'lucide-react';

interface PollutionDiagnosisCardProps {
  industrial?: IndustrialAnalysis | null;
  agricultural?: AgriculturalAnalysis | null;
  master?: MasterSynthesis | null;
  waterbodyType?: string | null;
}

export const PollutionDiagnosisCard: React.FC<PollutionDiagnosisCardProps> = ({
  industrial,
  agricultural,
  master,
  waterbodyType
}) => {
  if (!industrial && !agricultural && !master) return null;

  const isPond = waterbodyType === 'pond_lake';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '16px' }}>

      {/* Main Unified Diagnosis Card */}
      <div style={{
        background: 'var(--bg-card)',
        border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius-md)',
        padding: '20px'
      }}>
        <h3 style={{ fontSize: '16px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={18} style={{ color: '#38bdf8' }} />
          <span>Root Causes & Pollution Severity Analysis</span>
        </h3>

        {/* Vector Classification */}
        {master && master.dominant_pollution_vector && (
          <div style={{ marginBottom: '16px', background: 'rgba(15, 23, 42, 0.5)', padding: '14px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>Primary Contaminant & Vector Classification</span>
                <strong style={{ fontSize: '15px', color: '#38bdf8' }}>{master.dominant_pollution_vector}</strong>
              </div>
            </div>
          </div>
        )}

        {/* Synthesis Reasoning */}
        {master?.synthesis_reasoning && (
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Synthesis Overview
            </h4>
            <div style={{ padding: '12px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: 'var(--radius-sm)', fontSize: '13px', color: '#e2e8f0', lineHeight: '1.5', borderLeft: '3px solid #38bdf8' }}>
              {master.synthesis_reasoning}
            </div>
          </div>
        )}

        {/* Actionable Prioritized Remediation Recommendations */}
        {master?.remediation_recommendations && master.remediation_recommendations.length > 0 && (
          <div>
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Actionable Remediation & Mitigation Plan
            </h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              {master.remediation_recommendations.map((rec: string, idx: number) => (
                <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', padding: '8px 10px', background: 'rgba(15, 23, 42, 0.5)', borderRadius: 'var(--radius-sm)', fontSize: '12px', color: '#e2e8f0' }}>
                  <CheckCircle2 size={16} style={{ color: '#10b981', flexShrink: 0, marginTop: '2px' }} />
                  <span>{rec}</span>
                </div>
              ))}
            </div>
          </div>
        )}

      </div>
    </div>
  );
};
