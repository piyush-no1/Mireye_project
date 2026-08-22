import React from 'react';
import { ErrorsBanner } from './ErrorsBanner';
import { RiskScoreCard } from './RiskScoreCard';
import { AttainsStatusCard } from './AttainsStatusCard';
import { TelemetryChart } from './TelemetryChart';
import { AssessmentResult } from '../../types/assessment';
import { FlaskConical, Factory, TreePine } from 'lucide-react';

interface ResultsPanelProps {
  result: AssessmentResult | null;
}

export const ResultsPanel: React.FC<ResultsPanelProps> = ({ result }) => {
  if (!result) return null;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflowY: 'auto' }}>
      <ErrorsBanner errors={result.errors || []} />

      <RiskScoreCard summary={result.risk_summary} />

      <AttainsStatusCard attains={result.attains_status} />

      <TelemetryChart telemetry={result.telemetry} />

      {/* EPA Water Quality Samples summary */}
      {result.water_quality_samples && result.water_quality_samples.length > 0 && (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '20px',
          marginBottom: '16px'
        }}>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FlaskConical size={18} style={{ color: '#10b981' }} />
            <span>EPA Water Quality Sample Measurements ({result.water_quality_samples.length})</span>
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {result.water_quality_samples.slice(0, 5).map((sample, idx) => (
              <div key={idx} style={{
                display: 'flex',
                justifyContent: 'space-between',
                padding: '8px 12px',
                background: 'rgba(15, 23, 42, 0.5)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '13px'
              }}>
                <span style={{ color: 'var(--text-main)' }}>{sample.characteristic_name}</span>
                <span style={{ fontWeight: 600, color: '#10b981' }}>
                  {sample.result_value !== null ? `${sample.result_value} ${sample.unit_code || ''}` : 'N/A'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* EPA ECHO NPDES Polluters summary */}
      {result.polluters && result.polluters.length > 0 && (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '20px',
          marginBottom: '16px'
        }}>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Factory size={18} style={{ color: '#ef4444' }} />
            <span>NPDES Point-Source Polluting Facilities ({result.polluters.length})</span>
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {result.polluters.map((facility, idx) => (
              <div key={idx} style={{
                padding: '10px 12px',
                background: 'rgba(15, 23, 42, 0.5)',
                borderRadius: 'var(--radius-sm)',
                fontSize: '13px',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center'
              }}>
                <div>
                  <div style={{ fontWeight: 600, color: 'var(--text-main)' }}>{facility.facility_name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>ID: {facility.source_id}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '11px', fontWeight: 700, color: facility.effluent_exceedances > 0 ? '#ef4444' : '#10b981' }}>
                    {facility.effluent_exceedances} Exceedance(s)
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--text-subtle)' }}>Status: {facility.permit_status}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mireye Land Risk Overlay summary */}
      {result.land_risk_points && result.land_risk_points.length > 0 && (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: 'var(--radius-md)',
          padding: '20px'
        }}>
          <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TreePine size={18} style={{ color: '#8b5cf6' }} />
            <span>Mireye Riparian Buffer & Catchment Risk</span>
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', fontSize: '13px' }}>
            <div style={{ padding: '10px', background: 'rgba(15, 23, 42, 0.5)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>Avg Bank Slope</div>
              <div style={{ fontSize: '16px', fontWeight: 700, color: '#8b5cf6' }}>
                {(result.land_risk_points.reduce((acc, p) => acc + p.slope_degrees, 0) / result.land_risk_points.length).toFixed(1)}°
              </div>
            </div>
            <div style={{ padding: '10px', background: 'rgba(15, 23, 42, 0.5)', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ color: 'var(--text-muted)', fontSize: '11px' }}>Tree Canopy Coverage</div>
              <div style={{ fontSize: '16px', fontWeight: 700, color: '#8b5cf6' }}>
                {(result.land_risk_points.reduce((acc, p) => acc + p.tree_canopy_pct, 0) / result.land_risk_points.length).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
