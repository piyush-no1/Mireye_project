import React from 'react';
import { Droplet, ShieldAlert, Waves } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 28px',
      background: 'rgba(18, 25, 41, 0.85)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border-color)',
      position: 'sticky',
      top: 0,
      zIndex: 1000
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 15px rgba(14, 165, 233, 0.4)'
        }}>
          <Waves style={{ color: '#fff', width: '24px', height: '24px' }} />
        </div>
        <div>
          <h1 style={{ fontSize: '20px', fontWeight: 700, letterSpacing: '-0.02em', background: 'linear-gradient(90deg, #38bdf8, #818cf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            AquaTrace
          </h1>
          <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Agentic Waterbody Pollution Assessment Platform
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          background: 'rgba(14, 165, 233, 0.1)',
          borderRadius: '20px',
          border: '1px solid rgba(14, 165, 233, 0.25)',
          fontSize: '12px',
          color: '#38bdf8'
        }}>
          <Droplet style={{ width: '14px', height: '14px' }} />
          <span>USGS & EPA Live Data</span>
        </div>
      </div>
    </header>
  );
};
