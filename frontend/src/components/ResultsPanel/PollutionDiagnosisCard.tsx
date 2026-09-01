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

        {/* Vector Classification & Proportional Breakdown */}
        {master && (
          <div style={{ marginBottom: '16px', background: 'rgba(15, 23, 42, 0.5)', padding: '14px', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>Primary Pollution Vector</span>
                <strong style={{ fontSize: '15px', color: '#38bdf8' }}>{master.dominant_pollution_vector}</strong>
              </div>
            </div>

            {/* Proportional Contribution Bar */}
            <div style={{ marginBottom: '6px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
                <span style={{ color: '#ef4444', fontWeight: 600 }}>Industrial Point-Source: {master.industrial_weight_pct}%</span>
                <span style={{ color: '#eab308', fontWeight: 600 }}>Agricultural Non-Point: {master.agricultural_weight_pct}%</span>
              </div>
              <div style={{ width: '100%', height: '10px', background: '#334155', borderRadius: '5px', overflow: 'hidden', display: 'flex' }}>
                <div style={{ width: `${master.industrial_weight_pct}%`, background: '#ef4444', height: '100%' }} />
                <div style={{ width: `${master.agricultural_weight_pct}%`, background: '#eab308', height: '100%' }} />
              </div>
            </div>
          </div>
        )}

        {/* Combined Evidences Section */}
        {(industrial?.evidence_summary || agricultural?.evidence_summary || master?.synthesis_reasoning) && (
          <div style={{ marginBottom: '16px' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 700, color: 'var(--text-muted)', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Evidences
            </h4>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {master?.synthesis_reasoning && (
                <div style={{ padding: '12px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: 'var(--radius-sm)', fontSize: '13px', color: '#e2e8f0', lineHeight: '1.5', borderLeft: '3px solid #38bdf8' }}>
                  {master.synthesis_reasoning}
                </div>
              )}

              {industrial?.evidence_summary && (
                <div style={{ padding: '12px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: 'var(--radius-sm)', fontSize: '13px', color: '#e2e8f0', lineHeight: '1.5', borderLeft: '3px solid #ef4444' }}>
                  <strong style={{ color: '#ef4444', display: 'block', marginBottom: '4px' }}>Industrial Outfall & NPDES Evidence:</strong>
                  {industrial.evidence_summary}
                </div>
              )}

              {agricultural?.evidence_summary && (
                <div style={{ padding: '12px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: 'var(--radius-sm)', fontSize: '13px', color: '#e2e8f0', lineHeight: '1.5', borderLeft: '3px solid #eab308' }}>
                  <strong style={{ color: '#eab308', display: 'block', marginBottom: '4px' }}>Agricultural Runoff & Watershed Evidence:</strong>
                  {agricultural.evidence_summary}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Chemical & Nutrient Signature Matches */}
        {(industrial?.chemical_signature_match || agricultural?.nutrient_signature_match) && (
          <div style={{ marginBottom: '16px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            {industrial?.chemical_signature_match && (
              <div style={{ padding: '10px 12px', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid rgba(239, 68, 68, 0.25)', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>Chemical Signature Match</span>
                <strong style={{ fontSize: '13px', color: '#f8fafc' }}>{industrial.chemical_signature_match}</strong>
              </div>
            )}
            {agricultural?.nutrient_signature_match && (
              <div style={{ padding: '10px 12px', background: 'rgba(234, 179, 8, 0.1)', border: '1px solid rgba(234, 179, 8, 0.25)', borderRadius: 'var(--radius-sm)' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block' }}>Nutrient Signature Match</span>
                <strong style={{ fontSize: '13px', color: '#f8fafc' }}>{agricultural.nutrient_signature_match}</strong>
              </div>
            )}
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
