import React from 'react';
import { FileCheck, FileX } from 'lucide-react';
import { AttainsStatus } from '../../types/assessment';

interface AttainsStatusCardProps {
  attains: AttainsStatus[] | null;
}

export const AttainsStatusCard: React.FC<AttainsStatusCardProps> = ({ attains }) => {
  if (!attains || attains.length === 0) return null;

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-md)',
      padding: '20px',
      marginBottom: '16px'
    }}>
      <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <FileCheck size={18} style={{ color: '#38bdf8' }} />
        <span>Clean Water Act Section 303(d) Regulatory Status</span>
      </h3>

      {attains.map((au, idx) => {
        const isImpaired = au.overall_status.toLowerCase().includes('impair');

        return (
          <div key={idx} style={{
            background: 'rgba(15, 23, 42, 0.6)',
            border: '1px solid var(--border-color)',
            borderRadius: 'var(--radius-sm)',
            padding: '14px',
            marginBottom: '10px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
              <span style={{ fontSize: '13px', fontWeight: 600, color: '#38bdf8' }}>
                Unit ID: {au.assessment_unit_id}
              </span>
              <span style={{
                fontSize: '11px',
                fontWeight: 700,
                padding: '3px 10px',
                borderRadius: '12px',
                background: isImpaired ? 'rgba(239, 68, 68, 0.2)' : 'rgba(16, 185, 129, 0.2)',
                color: isImpaired ? '#ef4444' : '#10b981'
              }}>
                {au.overall_status}
              </span>
            </div>

            {((au.impairments && au.impairments.length > 0) || ((au as any).parameters && (au as any).parameters.length > 0)) && (
              <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '6px' }}>
                <strong>Impairment Causes:</strong> {((au.impairments || (au as any).parameters) as any[]).map((p: any) => p.name || p.cause_name || p).join(', ')}
              </div>
            )}

            {((au.tmdl_actions && au.tmdl_actions.length > 0) || ((au as any).tmdl_projects && (au as any).tmdl_projects.length > 0)) && (
              <div style={{ fontSize: '12px', color: 'var(--text-subtle)', marginTop: '4px' }}>
                <strong>Active TMDL Projects:</strong> {((au.tmdl_actions || (au as any).tmdl_projects) as any[]).map((t: any) => t.name || t.action_name || t).join(', ')}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};
