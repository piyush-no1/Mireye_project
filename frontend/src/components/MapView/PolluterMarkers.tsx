import React from 'react';
import { CircleMarker, Popup } from 'react-leaflet';
import { PolluterFacility } from '../../types/assessment';

interface PolluterMarkersProps {
  polluters: PolluterFacility[] | null;
}

export const PolluterMarkers: React.FC<PolluterMarkersProps> = ({ polluters }) => {
  if (!polluters || polluters.length === 0) return null;

  return (
    <>
      {polluters.map((facility, idx) => {
        const hasViolations = facility.effluent_exceedances > 0 || facility.quarters_in_noncompliance > 0;
        const color = hasViolations ? '#ef4444' : '#f59e0b';

        return (
          <CircleMarker
            key={`${facility.source_id}-${idx}`}
            center={[facility.lat, facility.lng]}
            radius={8}
            pathOptions={{
              color: color,
              fillColor: color,
              fillOpacity: 0.8,
              weight: 2
            }}
          >
            <Popup>
              <div style={{ color: '#0f172a', fontSize: '13px', lineHeight: '1.5' }}>
                <strong style={{ fontSize: '14px', display: 'block', color: '#1e293b' }}>
                  🏢 {facility.facility_name}
                </strong>
                <div><strong>NPDES Source ID:</strong> {facility.source_id}</div>
                <div><strong>Permit Status:</strong> {facility.permit_status}</div>
                <div><strong>Effluent Exceedances:</strong> {facility.effluent_exceedances}</div>
                <div><strong>Noncompliance Quarters:</strong> {facility.quarters_in_noncompliance}</div>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
};
