import React from 'react';
import { GeoJSON } from 'react-leaflet';

interface FlowlineLayerProps {
  geojson: any;
}

export const FlowlineLayer: React.FC<FlowlineLayerProps> = ({ geojson }) => {
  if (!geojson) return null;

  return (
    <GeoJSON
      key={JSON.stringify(geojson)}
      data={geojson}
      style={(feature) => {
        const type = feature?.geometry?.type || 'LineString';
        const isPolygon = type === 'Polygon' || type === 'MultiPolygon';

        if (isPolygon) {
          return {
            color: '#00F2FE',
            weight: 4,
            opacity: 0.95,
            fillColor: '#38bdf8',
            fillOpacity: 0.35,
            dashArray: '6, 6'
          };
        }

        return {
          color: '#38bdf8',
          weight: 5,
          opacity: 0.85,
          lineCap: 'round',
          lineJoin: 'round'
        };
      }}
    />
  );
};
