import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { StageError } from '../../types/assessment';

interface ErrorsBannerProps {
  errors: StageError[];
}

export const ErrorsBanner: React.FC<ErrorsBannerProps> = ({ errors }) => {
  if (!errors || errors.length === 0) return null;

  return (
    <div style={{
      background: 'rgba(239, 68, 68, 0.1)',
      border: '1px solid rgba(239, 68, 68, 0.3)',
      borderRadius: 'var(--radius-md)',
      padding: '12px 16px',
      marginBottom: '16px',
      color: '#fca5a5',
      fontSize: '13px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: 600, marginBottom: '6px', color: '#ef4444' }}>
        <AlertTriangle size={16} />
        <span>Partial Failure Warning — Unavailable Data Sources</span>
      </div>
      <ul style={{ paddingLeft: '20px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
        {errors.map((err, idx) => (
          <li key={idx}>
            <strong>{err.stage} ({err.tool}):</strong> {err.message}
          </li>
        ))}
      </ul>
    </div>
  );
};
