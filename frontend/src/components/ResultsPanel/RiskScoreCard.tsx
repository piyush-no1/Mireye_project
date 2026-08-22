import React from 'react';
import { ShieldAlert, ShieldCheck, AlertCircle } from 'lucide-react';
import { RiskSummary } from '../../types/assessment';

interface RiskScoreCardProps {
  summary: RiskSummary | null;
}

export const RiskScoreCard: React.FC<RiskScoreCardProps> = ({ summary }) => {
  if (!summary) return null;

  const rating = summary.rating || 'A';
  let badgeBg = 'rgba(16, 185, 129, 0.15)';
  let badgeColor = '#10b981';
  let Icon = ShieldCheck;

  if (rating === 'F') {
    badgeBg = 'rgba(239, 68, 68, 0.2)';
    badgeColor = '#ef4444';
    Icon = ShieldAlert;
  } else if (rating === 'D' || rating === 'C') {
    badgeBg = 'rgba(249, 115, 22, 0.2)';
    badgeColor = '#f97316';
    Icon = AlertCircle;
  } else if (rating === 'B') {
    badgeBg = 'rgba(245, 158, 11, 0.2)';
    badgeColor = '#f59e0b';
    Icon = AlertCircle;
  }

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-md)',
      padding: '20px',
      marginBottom: '16px'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-muted)' }}>
          Environmental Assessment Rating
        </h3>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px',
          padding: '6px 14px',
          borderRadius: '20px',
          background: badgeBg,
          color: badgeColor,
          fontWeight: 700,
          fontSize: '13px'
        }}>
          <Icon size={16} />
          <span>{summary.label}</span>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '16px' }}>
        <span style={{ fontSize: '48px', fontWeight: 900, color: badgeColor, marginRight: '12px' }}>
          {rating}
        </span>
      </div>

      {summary.risk_factors && summary.risk_factors.length > 0 && (
        <div style={{ marginBottom: '12px' }}>
          <strong style={{ color: 'var(--text-primary)', fontSize: '13px', display: 'block', marginBottom: '4px' }}>Risk Factors</strong>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: 'var(--text-main)' }}>
            {summary.risk_factors.map((rf, i) => <li key={i}>{rf}</li>)}
          </ul>
        </div>
      )}

      {summary.mitigating_factors && summary.mitigating_factors.length > 0 && (
        <div style={{ marginBottom: '12px' }}>
          <strong style={{ color: 'var(--text-primary)', fontSize: '13px', display: 'block', marginBottom: '4px' }}>Mitigating Factors</strong>
          <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '13px', color: 'var(--text-main)' }}>
            {summary.mitigating_factors.map((mf, i) => <li key={i}>{mf}</li>)}
          </ul>
        </div>
      )}

      {summary.temporal_assessment && (
        <div style={{ marginBottom: '12px' }}>
          <strong style={{ color: 'var(--text-primary)', fontSize: '13px', display: 'block', marginBottom: '4px' }}>Temporal Assessment</strong>
          <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-main)' }}>{summary.temporal_assessment}</p>
        </div>
      )}
      
      {summary.spatial_assessment && (
        <div style={{ marginBottom: '12px' }}>
          <strong style={{ color: 'var(--text-primary)', fontSize: '13px', display: 'block', marginBottom: '4px' }}>Spatial Assessment</strong>
          <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-main)' }}>{summary.spatial_assessment}</p>
        </div>
      )}

      {summary.data_limitations && (
        <div style={{ marginBottom: '12px' }}>
          <strong style={{ color: 'var(--text-primary)', fontSize: '13px', display: 'block', marginBottom: '4px' }}>Data Limitations</strong>
          <p style={{ margin: 0, fontSize: '13px', color: 'var(--text-main)' }}>{summary.data_limitations}</p>
        </div>
      )}

      <div style={{ marginTop: '16px' }}>
        <strong style={{ color: 'var(--text-primary)', fontSize: '13px', display: 'block', marginBottom: '4px' }}>Synthesis Notes</strong>
        <p style={{ fontSize: '13px', color: 'var(--text-main)', lineHeight: '1.5', background: 'rgba(30, 41, 59, 0.5)', padding: '10px 14px', borderRadius: 'var(--radius-sm)', margin: 0 }}>
          {summary.notes || 'Deterministic multi-source evaluation complete.'}
        </p>
      </div>
    </div>
  );
};
