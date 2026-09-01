import React from 'react';
import { Droplet, ShieldAlert, Waves } from 'lucide-react';

export const Header: React.FC = () => {
  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '16px 28px',
      background: 'rgba(8, 27, 51, 0.85)',
      backdropFilter: 'blur(16px)',
      borderBottom: '1px solid rgba(56, 189, 248, 0.3)',
      position: 'sticky',
      top: 0,
      zIndex: 1000
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{
          width: '42px',
          height: '42px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, #38bdf8 0%, #0284c7 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 20px rgba(56, 189, 248, 0.5)'
        }}>
          <Waves style={{ color: '#fff', width: '24px', height: '24px' }} />
        </div>
        <div>
          <h1 style={{ fontSize: '22px', fontWeight: 700, letterSpacing: '-0.02em', color: '#38bdf8' }}>
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
          background: 'rgba(56, 189, 248, 0.15)',
          borderRadius: '20px',
          border: '1px solid rgba(56, 189, 248, 0.35)',
          fontSize: '12px',
          color: '#e0f2fe'
        }}>
          <Droplet style={{ width: '14px', height: '14px', color: '#38bdf8' }} />
          <span>USGS, EPA & Mireye Live Data</span>
        </div>
      </div>
    </header>
  );
};
