import React from 'react';
import { IndustrialAnalysis, AgriculturalAnalysis, MasterSynthesis } from '../../types/assessment';
import { Factory, Wheat, Brain, ShieldAlert, CheckCircle2 } from 'lucide-react';

interface MoAAnalysisCardsProps {
  industrial?: IndustrialAnalysis | null;
  agricultural?: AgriculturalAnalysis | null;
  master?: MasterSynthesis | null;
  waterbodyType?: string | null;
}

export const MoAAnalysisCards: React.FC<MoAAnalysisCardsProps> = ({
  industrial,
  agricultural,
  master,
  waterbodyType
}) => {
  if (!industrial && !agricultural && !master) return null;

  const isPond = waterbodyType === 'pond_lake';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', marginBottom: '16px' }}>
      
      {/* Waterbody Type Banner */}
      <div style={{
        background: isPond ? 'rgba(56, 189, 248, 0.12)' : 'rgba(16, 185, 129, 0.12)',
        border: `1px solid ${isPond ? 'rgba(56, 189, 248, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
        borderRadius: 'var(--radius-md)',
        padding: '12px 16px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '20px' }}>{isPond ? '🌊' : '🏞️'}</span>
          <div>
            <strong style={{ fontSize: '14px', color: isPond ? '#38bdf8' : '#10b981', display: 'block' }}>
              {isPond ? 'Pond / Lake Examination (Lentic Waterbody)' : 'Waterbody Corridor Examination (Lotic Waterbody)'}
            </strong>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              {isPond 
                ? 'Examined 100% full closed waterbody boundary perimeter & deep-water core sampling nodes.'
                : 'Traced continuous USGS stream flowlines and sampled riparian waterbody corridors.'}
            </span>
          </div>
        </div>
        <span style={{
          padding: '4px 10px',
          borderRadius: '12px',
          fontSize: '11px',
          fontWeight: 700,
          background: isPond ? '#0284c7' : '#059669',
          color: '#ffffff'
        }}>
          {isPond ? 'FULL POND POLYGON' : 'WATERBODY ROUTE TRACE'}
        </span>
      </div>

      {/* Master Orchestrator Vector Synthesis Card */}
      {master && (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid rgba(56, 189, 248, 0.4)',
          borderRadius: 'var(--radius-md)',
          padding: '20px'
        }}>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: '#38bdf8', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Brain size={18} style={{ color: '#38bdf8' }} />
            <span>Master Orchestrator — Cross-Domain Vector Synthesis</span>
          </h3>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '14px' }}>
            <div style={{ padding: '12px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Dominant Vector</div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc', marginTop: '2px' }}>
                {master.dominant_pollution_vector}
              </div>
            </div>
            <div style={{ padding: '12px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Overall Grade</div>
              <div style={{ fontSize: '15px', fontWeight: 700, color: '#38bdf8', marginTop: '2px' }}>
                {master.overall_rating} ({master.overall_label})
              </div>
            </div>
          </div>

          {/* Proportional Vector Contribution Progress Bar */}
          <div style={{ marginBottom: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', marginBottom: '6px' }}>
              <span style={{ color: '#ef4444', fontWeight: 600 }}>🏭 Industrial Point-Source: {master.industrial_weight_pct}%</span>
              <span style={{ color: '#eab308', fontWeight: 600 }}>🌾 Agricultural Non-Point: {master.agricultural_weight_pct}%</span>
            </div>
            <div style={{ width: '100%', height: '10px', background: '#334155', borderRadius: '5px', overflow: 'hidden', display: 'flex' }}>
              <div style={{ width: `${master.industrial_weight_pct}%`, background: '#ef4444', height: '100%' }} />
              <div style={{ width: `${master.agricultural_weight_pct}%`, background: '#eab308', height: '100%' }} />
            </div>
          </div>

          {master.synthesis_reasoning && (
            <div style={{ fontSize: '13px', color: 'var(--text-main)', lineHeight: '1.5', padding: '10px 12px', background: 'rgba(15, 23, 42, 0.4)', borderRadius: 'var(--radius-sm)', marginBottom: '12px' }}>
              <strong>Synthesis Reasoning:</strong> {master.synthesis_reasoning}
            </div>
          )}

          {master.remediation_recommendations && master.remediation_recommendations.length > 0 && (
            <div>
              <strong style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Prioritized Remediation Actions:</strong>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                {master.remediation_recommendations.map((rec: string, idx: number) => (
                  <div key={idx} style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', fontSize: '12px', color: '#e2e8f0' }}>
                    <CheckCircle2 size={15} style={{ color: '#10b981', flexShrink: 0, marginTop: '2px' }} />
                    <span>{rec}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Industrial Specialist Agent Card */}
      {industrial && (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '16px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Factory size={16} style={{ color: '#ef4444' }} />
              <span>Industrial Specialist Agent Report</span>
            </h4>
            <span style={{
              padding: '2px 8px',
              borderRadius: '8px',
              fontSize: '12px',
              fontWeight: 700,
              background: industrial.risk_score >= 60 ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
              color: industrial.risk_score >= 60 ? '#ef4444' : '#10b981'
            }}>
              Score: {industrial.risk_score} ({industrial.risk_rating})
            </span>
          </div>

          {industrial.chemical_signature_match && (
            <div style={{ fontSize: '12px', color: '#f8fafc', marginBottom: '8px' }}>
              <strong>Chemical Signature Match:</strong> {industrial.chemical_signature_match}
            </div>
          )}

          {industrial.evidence_summary && (
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
              {industrial.evidence_summary}
            </div>
          )}
        </div>
      )}

      {/* Agricultural Specialist Agent Card */}
      {agricultural && (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '16px'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Wheat size={16} style={{ color: '#eab308' }} />
              <span>Agricultural Specialist Agent Report</span>
            </h4>
            <span style={{
              padding: '2px 8px',
              borderRadius: '8px',
              fontSize: '12px',
              fontWeight: 700,
              background: agricultural.risk_score >= 60 ? 'rgba(234, 179, 8, 0.2)' : 'rgba(16, 185, 129, 0.2)',
              color: agricultural.risk_score >= 60 ? '#eab308' : '#10b981'
            }}>
              Score: {agricultural.risk_score} ({agricultural.risk_rating})
            </span>
          </div>

          {agricultural.nutrient_signature_match && (
            <div style={{ fontSize: '12px', color: '#f8fafc', marginBottom: '8px' }}>
              <strong>Nutrient Signature Match:</strong> {agricultural.nutrient_signature_match}
            </div>
          )}

          {agricultural.evidence_summary && (
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.4' }}>
              {agricultural.evidence_summary}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
