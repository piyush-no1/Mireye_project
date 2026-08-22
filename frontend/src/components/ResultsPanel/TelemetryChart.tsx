import React from 'react';
import { Activity, Gauge, Thermometer, Waves } from 'lucide-react';
import { TelemetryData } from '../../types/assessment';

interface TelemetryChartProps {
  telemetry: TelemetryData[] | null;
}

export const TelemetryChart: React.FC<TelemetryChartProps> = ({ telemetry }) => {
  if (!telemetry || telemetry.length === 0) return null;

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-md)',
      padding: '20px',
      marginBottom: '16px'
    }}>
      <h3 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)', marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <Activity size={18} style={{ color: '#06b6d4' }} />
        <span>USGS NWIS Real-Time Telemetry</span>
      </h3>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '12px' }}>
        {telemetry.map((t, idx) => (
          <React.Fragment key={idx}>
            <div style={{
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              padding: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px' }}>
                <Waves size={14} style={{ color: '#38bdf8' }} />
                <span>Stream Discharge</span>
              </div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#38bdf8' }}>
                {t.discharge_cfs !== null ? `${t.discharge_cfs.toLocaleString()} cfs` : 'N/A'}
              </div>
            </div>

            <div style={{
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              padding: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px' }}>
                <Gauge size={14} style={{ color: '#10b981' }} />
                <span>Gage Height</span>
              </div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#10b981' }}>
                {t.gage_height_ft !== null ? `${t.gage_height_ft.toFixed(2)} ft` : 'N/A'}
              </div>
            </div>

            <div style={{
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid var(--border-color)',
              borderRadius: 'var(--radius-sm)',
              padding: '14px'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '6px' }}>
                <Thermometer size={14} style={{ color: '#f59e0b' }} />
                <span>Water Temp</span>
              </div>
              <div style={{ fontSize: '20px', fontWeight: 700, color: '#f59e0b' }}>
                {t.water_temp_c !== null ? `${t.water_temp_c.toFixed(1)} °C` : 'N/A'}
              </div>
            </div>
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};
