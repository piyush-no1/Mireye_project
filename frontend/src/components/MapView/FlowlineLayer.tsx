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
      style={() => ({
        color: '#38bdf8',
        weight: 5,
        opacity: 0.85,
        lineCap: 'round',
        lineJoin: 'round'
      })}
    />
  );
};
