import React, { useState } from 'react';
import { AssessmentResult } from '../../types/assessment';
import { Database, ChevronDown, ChevronRight, Server } from 'lucide-react';

interface Props {
  result: AssessmentResult;
}

const SourceCard: React.FC<{ title: string; description: string; data: any; icon?: React.ReactNode }> = ({ title, description, data, icon }) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div style={{
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-md)',
      background: 'var(--bg-card)',
      overflow: 'hidden',
      marginBottom: '12px'
    }}>
      <div 
        onClick={() => setExpanded(!expanded)}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: '16px',
          cursor: 'pointer',
          background: expanded ? 'rgba(0,0,0,0.02)' : 'transparent',
          borderBottom: expanded ? '1px solid var(--border-color)' : 'none'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {icon || <Database size={20} style={{ color: 'var(--text-muted)' }} />}
          <div>
            <h4 style={{ margin: 0, fontSize: '15px', color: 'var(--text-primary)' }}>{title}</h4>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{description}</span>
          </div>
        </div>
        <div style={{ color: 'var(--text-muted)' }}>
          {expanded ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
        </div>
      </div>
      
      {expanded && (
        <div style={{ padding: '16px', background: '#1e1e1e', color: '#d4d4d4', fontSize: '13px', overflowX: 'auto' }}>
          <pre style={{ margin: 0, fontFamily: 'monospace' }}>
            {JSON.stringify(data, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
};

export const DataSourcesPanel: React.FC<Props> = ({ result }) => {
  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: 'var(--radius-lg)',
      padding: '24px',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '20px' }}>
        <Server size={24} style={{ color: '#8b5cf6' }} />
        <h2 style={{ margin: 0, fontSize: '20px', color: 'var(--text-primary)' }}>Data Sources & API Payloads</h2>
      </div>
      <p style={{ fontSize: '14px', color: 'var(--text-muted)', marginBottom: '24px' }}>
        This panel breaks down the exact provenance of the data collected by the agent workflow for this assessment. 
        Expand any source below to inspect the raw JSON data returned by the underlying API.
      </p>

      <div>
        {result.resolved_location && (
          <SourceCard 
            title="Mireye Geocoding API / Nominatim" 
            description="Geocoding resolution for the queried waterbody."
            data={result.resolved_location} 
          />
        )}
        
        {result.attains_status && result.attains_status.length > 0 && (
          <SourceCard 
            title="EPA ATTAINS API" 
            description="Clean Water Act Section 303(d) impairment status and designated uses."
            data={result.attains_status} 
          />
        )}

        {result.polluters && result.polluters.length > 0 && (
          <SourceCard 
            title="EPA ECHO (ICIS-NPDES) API" 
            description="Active point-source permitted facilities and their effluent violations."
            data={result.polluters} 
          />
        )}

        {result.industrial_analysis?.tri_releases_summary && (
          <SourceCard 
            title="EPA TRI Chemical Release Inventory API" 
            description="Toxics Release Inventory (TRI) chemical discharge records and facility releases."
            data={result.industrial_analysis.tri_releases_summary} 
          />
        )}

        {result.agricultural_analysis?.crop_coverage && (
          <SourceCard 
            title="USDA Cropland Data Layer (CDL) & CAFO Metrics" 
            description="Agricultural cropland breakdown, fertilizer application intensity, and CAFO counts."
            data={{
              crop_coverage: result.agricultural_analysis.crop_coverage,
              cafos: result.agricultural_analysis.cafos_in_watershed || []
            }} 
          />
        )}

        {result.agricultural_analysis?.eutrophication_index && (
          <SourceCard 
            title="Sentinel Satellite Eutrophication Index" 
            description="Chlorophyll-a concentration, turbidity, and satellite-detected algal bloom risk."
            data={result.agricultural_analysis.eutrophication_index} 
          />
        )}

        {result.water_quality_samples && result.water_quality_samples.length > 0 && (
          <SourceCard 
            title="EPA Water Quality Portal (WQP)" 
            description="Recent chemical and physical water quality samples (DO, Nitrate, Metals, etc.)."
            data={result.water_quality_samples} 
          />
        )}

        {result.land_risk_points && result.land_risk_points.length > 0 && (
          <SourceCard 
            title="Mireye Earth API (Land Risk)" 
            description="Topographic slope, elevation, tree canopy coverage, and vegetation index (NDVI)."
            data={result.land_risk_points} 
          />
        )}

        {result.hydrology && (
          <SourceCard 
            title="USGS NLDI API" 
            description="Hydrographic flowline tracing and basin boundaries."
            data={result.hydrology} 
          />
        )}

        {result.telemetry && result.telemetry.length > 0 && (
          <SourceCard 
            title="USGS NWIS Water Services" 
            description="Real-time streamflow telemetry (discharge, gage height, temperature)."
            data={result.telemetry} 
          />
        )}

        {result.execution_log && result.execution_log.length > 0 && (
          <SourceCard 
            title="Mireye & Multi-Agent Execution Audit Log" 
            description="Chronological audit trace of every tool, agent, and API call executed for this run."
            icon={<Server size={20} style={{ color: '#38bdf8' }} />}
            data={result.execution_log} 
          />
        )}

        <div style={{ marginTop: '32px', borderTop: '1px solid var(--border-color)', paddingTop: '24px' }}>
          <h3 style={{ margin: '0 0 16px 0', fontSize: '18px', color: 'var(--text-primary)' }}>LLM Reasoning Payload</h3>
          <SourceCard 
            title="OpenAI Agent Prompt Data" 
            description="The exact aggregated data payload sent to the OpenAI reasoning agent for scoring."
            icon={<Server size={20} style={{ color: '#10b981' }} />}
            data={{
              query: result.query,
              industrial_analysis: result.industrial_analysis || null,
              agricultural_analysis: result.agricultural_analysis || null,
              master_synthesis: result.master_synthesis || null,
              attains_summary: result.attains_summary || null,
              polluters: result.polluters || [],
              water_quality_samples: result.water_quality_samples || [],
              land_risk_points: result.land_risk_points || [],
              telemetry: result.telemetry || []
            }}
          />
        </div>
      </div>
    </div>
  );
};
