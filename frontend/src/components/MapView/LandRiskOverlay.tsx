import React from 'react';
import { CircleMarker, Popup } from 'react-leaflet';
import { LandRiskPoint } from '../../types/assessment';

interface LandRiskOverlayProps {
  points: LandRiskPoint[] | null;
}

export const LandRiskOverlay: React.FC<LandRiskOverlayProps> = ({ points }) => {
  if (!points || points.length === 0) return null;

  return (
    <>
      {points.map((pt, idx) => {
        const isHighSlope = pt.slope_degrees > 12.0;
        const color = isHighSlope ? '#8b5cf6' : '#a855f7';

        return (
          <CircleMarker
            key={`land-risk-${idx}`}
            center={[pt.lat, pt.lng]}
            radius={6}
            pathOptions={{
              color: color,
              fillColor: color,
              fillOpacity: 0.6,
              weight: 1.5,
              dashArray: '3, 3'
            }}
          >
            <Popup>
              <div style={{ color: '#0f172a', fontSize: '13px', lineHeight: '1.5' }}>
                <strong style={{ fontSize: '14px', display: 'block', color: '#581c87' }}>
                  🌿 Mireye Riparian Land Risk
                </strong>
                <div><strong>Slope:</strong> {pt.slope_degrees.toFixed(1)}°</div>
                <div><strong>Tree Canopy:</strong> {pt.tree_canopy_pct.toFixed(1)}%</div>
                <div><strong>Land Cover:</strong> {pt.lcms_class}</div>
                <div><strong>FEMA Flood Zone:</strong> {pt.fema_flood_zone}</div>
                <div><strong>5Y NDVI Delta:</strong> {pt.ndvi_change_5y.toFixed(2)}</div>
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
};
