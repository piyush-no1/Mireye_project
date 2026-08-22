import React, { useEffect } from 'react';
import { MapContainer, TileLayer, useMap } from 'react-leaflet';
import { FlowlineLayer } from './FlowlineLayer';
import { PolluterMarkers } from './PolluterMarkers';
import { WaterQualityMarkers } from './WaterQualityMarkers';
import { LandRiskOverlay } from './LandRiskOverlay';
import { AssessmentResult } from '../../types/assessment';
import styles from './MapView.module.css';

interface MapViewProps {
  result: AssessmentResult | null;
}

// Controller to auto-center/fit map bounds on location resolution
const MapBoundsController: React.FC<{ result: AssessmentResult | null }> = ({ result }) => {
  const map = useMap();

  useEffect(() => {
    if (!result) return;
    
    if (result.resolved_location) {
      map.setView([result.resolved_location.lat, result.resolved_location.lng], 13);
    }
  }, [result, map]);

  return null;
};

export const MapView: React.FC<MapViewProps> = ({ result }) => {
  const defaultCenter: [number, number] = result?.resolved_location
    ? [result.resolved_location.lat, result.resolved_location.lng]
    : [38.9986, -77.2538];

  return (
    <div className={styles.mapContainer}>
      <MapContainer
        center={defaultCenter}
        zoom={12}
        className={styles.map}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url={import.meta.env.VITE_MAP_TILE_URL || 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png'}
        />

        <MapBoundsController result={result} />

        {result?.hydrology?.flowline_geojson && (
          <FlowlineLayer geojson={result.hydrology.flowline_geojson} />
        )}

        {result?.polluters && (
          <PolluterMarkers polluters={result.polluters} />
        )}

        {result?.water_quality_samples && (
          <WaterQualityMarkers
            samples={result.water_quality_samples}
            bankPoints={result.hydrology?._bank_points}
            baseLat={result.resolved_location?.lat}
            baseLng={result.resolved_location?.lng}
          />
        )}

        {result?.land_risk_points && (
          <LandRiskOverlay points={result.land_risk_points} />
        )}
      </MapContainer>

      {/* Map Legend Overlay */}
      <div className={styles.legend}>
        <div className={styles.legendTitle}>Map Layers & Legend</div>
        <div className={styles.legendItem}>
          <div className={styles.legendDot} style={{ background: '#38bdf8' }} />
          <span>USGS NHDPlus Stream Flowline</span>
        </div>
        <div className={styles.legendItem}>
          <div className={styles.legendDot} style={{ background: '#10b981' }} />
          <span>EPA Water Quality Sample Points</span>
        </div>
        <div className={styles.legendItem}>
          <div className={styles.legendDot} style={{ background: '#ef4444' }} />
          <span>EPA ECHO NPDES Polluters</span>
        </div>
        <div className={styles.legendItem}>
          <div className={styles.legendDot} style={{ background: '#8b5cf6' }} />
          <span>Mireye Riparian Land Risk Buffer</span>
        </div>
      </div>
    </div>
  );
};
