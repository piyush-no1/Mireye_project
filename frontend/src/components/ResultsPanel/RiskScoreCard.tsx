import React from 'react';
import { ShieldAlert, ShieldCheck, AlertCircle } from 'lucide-react';
import { RiskSummary } from '../../types/assessment';

interface RiskScoreCardProps {
  summary: RiskSummary | null;
}

export const RiskScoreCard: React.FC<RiskScoreCardProps> = ({ summary }) => {
  if (!summary) return null;

  const score = summary.overall_score;
  let badgeBg = 'rgba(16, 185, 129, 0.15)';
  let badgeColor = '#10b981';
  let Icon = ShieldCheck;

  if (score >= 80.0) {
    badgeBg = 'rgba(239, 68, 68, 0.2)';
    badgeColor = '#ef4444';
    Icon = ShieldAlert;
  } else if (score >= 55.0) {
    badgeBg = 'rgba(249, 115, 22, 0.2)';
    badgeColor = '#f97316';
    Icon = AlertCircle;
  } else if (score >= 25.0) {
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
          Overall Pollution Risk Score
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

      <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '12px' }}>
        <span style={{ fontSize: '38px', fontWeight: 800, color: badgeColor, letterSpacing: '-0.03em' }}>
          {summary.overall_score.toFixed(1)}
        </span>
        <span style={{ fontSize: '14px', color: 'var(--text-subtle)' }}>/ 100 Risk Points</span>
      </div>

      <p style={{ fontSize: '13px', color: 'var(--text-main)', lineHeight: '1.5', background: 'rgba(30, 41, 59, 0.5)', padding: '10px 14px', borderRadius: 'var(--radius-sm)' }}>
        {summary.notes || 'Deterministic multi-source evaluation complete.'}
      </p>
    </div>
  );
};
