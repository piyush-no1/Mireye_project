import React from 'react';
import { CircleMarker, Popup } from 'react-leaflet';
import { WaterQualitySample } from '../../types/assessment';

interface WaterQualityMarkersProps {
  samples: WaterQualitySample[] | null;
  bankPoints?: Array<{ lat: number; lng: number }> | null;
  baseLat?: number;
  baseLng?: number;
}

export const WaterQualityMarkers: React.FC<WaterQualityMarkersProps> = ({
  samples,
  bankPoints,
  baseLat = 38.9986,
  baseLng = -77.2538
}) => {
  if (!samples || samples.length === 0) return null;

  return (
    <>
      {samples.map((sample, idx) => {
        let lat = baseLat;
        let lng = baseLng;

        // Use actual river bank/channel points if available
        if (bankPoints && bankPoints.length > 0) {
          const pt = bankPoints[idx % bankPoints.length];
          lat = pt.lat;
          lng = pt.lng;
        } else if (sample.lat && sample.lng) {
          lat = sample.lat;
          lng = sample.lng;
        }

        if (typeof lat !== 'number' || isNaN(lat) || typeof lng !== 'number' || isNaN(lng)) {
          return null;
        }

        return (
          <CircleMarker
            key={`wqp-${sample.monitoring_location_id}-${idx}`}
            center={[lat, lng]}
            radius={7}
            pathOptions={{
              color: '#10b981',
              fillColor: '#10b981',
              fillOpacity: 0.85,
              weight: 2
            }}
          >
            <Popup>
              <div style={{ color: '#0f172a', fontSize: '13px', lineHeight: '1.5' }}>
                <strong style={{ fontSize: '14px', display: 'block', color: '#065f46' }}>
                  🧪 WQP Station: {sample.monitoring_location_id}
                </strong>
                <div><strong>Parameter:</strong> {sample.characteristic_name}</div>
                <div><strong>Result:</strong> {sample.result_value !== null ? `${sample.result_value} ${sample.unit_code || ''}` : 'N/A'}</div>
                {sample.activity_start_date && <div><strong>Sample Date:</strong> {sample.activity_start_date}</div>}
              </div>
            </Popup>
          </CircleMarker>
        );
      })}
    </>
  );
};
