import React, { useMemo } from 'react';
import { GeoJSON } from 'react-leaflet';
import { AttainsStatus } from '../../types/assessment';
import { LocationPoint } from '../../types/assessment';
import * as turf from '@turf/turf';

interface AttainsLayersProps {
  attains_status: AttainsStatus[];
  start_point?: LocationPoint | null;
  end_point?: LocationPoint | null;
  flowline_geojson?: any;
}

export const AttainsLayers: React.FC<AttainsLayersProps> = ({ attains_status, start_point, end_point, flowline_geojson }) => {
  if (!attains_status || attains_status.length === 0) return null;

  const styleByStatus = (status: string, isSaturated: boolean) => {
    switch (status) {
      case 'Impaired':
      case 'Not Supporting':
        return isSaturated 
          ? { color: '#ef4444', weight: 6, opacity: 0.9, fillColor: '#ef4444', fillOpacity: 0.2 }
          : { color: '#fca5a5', weight: 4, opacity: 0.6, fillColor: '#fca5a5', fillOpacity: 0.15, dashArray: '5, 8' };
      case 'Fully Supporting':
        return isSaturated
          ? { color: '#22c55e', weight: 6, opacity: 0.9, fillColor: '#22c55e', fillOpacity: 0.2 }
          : { color: '#86efac', weight: 4, opacity: 0.6, fillColor: '#86efac', fillOpacity: 0.15, dashArray: '5, 8' };
      default:
        return isSaturated
          ? { color: '#94a3b8', weight: 6, opacity: 0.9, fillColor: '#94a3b8', fillOpacity: 0.2 }
          : { color: '#cbd5e1', weight: 4, opacity: 0.6, fillColor: '#cbd5e1', fillOpacity: 0.15, dashArray: '5, 8' };
    }
  };

  const clipBbox = useMemo(() => {
    if (flowline_geojson) {
      try {
        const bbox = turf.bbox(flowline_geojson);
        // bbox is [minX, minY, maxX, maxY] which is [minLng, minLat, maxLng, maxLat]
        return [bbox[0] - 0.003, bbox[1] - 0.003, bbox[2] + 0.003, bbox[3] + 0.003];
      } catch (e) {
        console.error('Failed to calculate bbox for flowline', e);
      }
    }

    if (!start_point || !end_point) return null;
    const minLng = Math.min(start_point.lng, end_point.lng) - 0.002;
    const maxLng = Math.max(start_point.lng, end_point.lng) + 0.002;
    const minLat = Math.min(start_point.lat, end_point.lat) - 0.002;
    const maxLat = Math.max(start_point.lat, end_point.lat) + 0.002;
    return [minLng, minLat, maxLng, maxLat];
  }, [start_point, end_point, flowline_geojson]);

  return (
    <>
      {attains_status.map((au) => {
        if (!au.geometry) return null;

        const saturatedStyle = styleByStatus(au.overall_status, true);
        const unsaturatedStyle = styleByStatus(au.overall_status, false);
        
        let clippedGeometry = null;
        if (clipBbox && (au.geometry.type === 'LineString' || au.geometry.type === 'MultiLineString' || au.geometry.type === 'Polygon' || au.geometry.type === 'MultiPolygon')) {
          try {
            const feat = turf.feature(au.geometry as any);
            const clipped = turf.bboxClip(feat, clipBbox as [number, number, number, number]);
            if (clipped && clipped.geometry && clipped.geometry.coordinates.length > 0) {
              clippedGeometry = clipped.geometry;
            }
          } catch (e) {
            console.error('Failed to clip geometry', e);
          }
        }

        const popupContent = `
          <div style="font-family: 'Inter', sans-serif;">
            <strong style="display: block; margin-bottom: 4px; color: #334155;">
              ${au.waterbody_name || au.assessment_unit_id}
            </strong>
            <div style="font-size: 12px; color: #64748b; margin-bottom: 4px;">
              ID: ${au.assessment_unit_id}
            </div>
            <div style="font-size: 12px; font-weight: 600; color: ${saturatedStyle.color};">
              ${au.overall_status}
            </div>
          </div>
        `;

        return (
          <React.Fragment key={au.assessment_unit_id}>
            {/* Base unsaturated layer (full extent) */}
            <GeoJSON
              data={au.geometry}
              style={unsaturatedStyle}
              onEachFeature={(_feature, layer) => layer.bindPopup(popupContent)}
            />
            {/* Clipped saturated layer (inside points) rendered on top */}
            {clippedGeometry && (
              <GeoJSON
                data={clippedGeometry}
                style={saturatedStyle}
                onEachFeature={(_feature, layer) => layer.bindPopup(popupContent)}
              />
            )}
          </React.Fragment>
        );
      })}
    </>
  );
};
