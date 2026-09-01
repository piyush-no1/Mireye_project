import React, { useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { FlowlineLayer } from './FlowlineLayer';
import { PolluterMarkers } from './PolluterMarkers';
import { WaterQualityMarkers } from './WaterQualityMarkers';
import { LandRiskOverlay } from './LandRiskOverlay';
import { AttainsLayers } from './AttainsLayers';
import { AssessmentResult } from '../../types/assessment';
import styles from './MapView.module.css';

interface MapViewProps {
  result: AssessmentResult | null;
}

const startPinIcon = new L.DivIcon({
  className: 'mapview-start-pin',
  html: `<div style="background:#10b981; color:white; border-radius:50%; width:30px; height:30px; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:15px; border:2px solid white; box-shadow:0 3px 8px rgba(0,0,0,0.4);">A</div>`,
  iconSize: [30, 30],
  iconAnchor: [15, 15]
});

const endPinIcon = new L.DivIcon({
  className: 'mapview-end-pin',
  html: `<div style="background:#ef4444; color:white; border-radius:50%; width:30px; height:30px; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:15px; border:2px solid white; box-shadow:0 3px 8px rgba(0,0,0,0.4);">B</div>`,
  iconSize: [30, 30],
  iconAnchor: [15, 15]
});

// Controller to auto-center/fit map bounds on location resolution
const MapBoundsController: React.FC<{ result: AssessmentResult | null }> = ({ result }) => {
  const map = useMap();

  useEffect(() => {
    if (!result) return;
    
    if (result.hydrology?.bbox && Array.isArray(result.hydrology.bbox) && result.hydrology.bbox.length === 4) {
      const [minLng, minLat, maxLng, maxLat] = result.hydrology.bbox;
      if (minLat !== 0 && minLng !== 0) {
        const bounds = L.latLngBounds([minLat, minLng], [maxLat, maxLng]);
        map.fitBounds(bounds, { padding: [40, 40] });
        return;
      }
    }

    if (result.start_point && result.end_point) {
      const bounds = L.latLngBounds(
        [result.start_point.lat, result.start_point.lng],
        [result.end_point.lat, result.end_point.lng]
      );
      map.fitBounds(bounds, { padding: [50, 50] });
    } else if (result.resolved_location) {
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

        {result?.attains_status && (
          <AttainsLayers 
            attains_status={result.attains_status} 
            start_point={result.start_point || undefined}
            end_point={result.end_point || undefined}
            flowline_geojson={result.hydrology?.flowline_geojson}
          />
        )}

        {result?.hydrology?.flowline_geojson && (
          <FlowlineLayer geojson={result.hydrology.flowline_geojson} />
        )}

        {/* Start Point A Marker with Magnetic Snapping */}
        {result?.start_point && (() => {
          let pos: [number, number] = [Number(result.start_point.lat), Number(result.start_point.lng)];
          try {
            const geom = result.hydrology?.flowline_geojson?.features?.[0]?.geometry;
            if (geom?.type === 'LineString' && geom.coordinates?.length > 0) {
              const first = geom.coordinates[0];
              if (typeof first[1] === 'number' && typeof first[0] === 'number') {
                pos = [first[1], first[0]];
              }
            } else if (geom?.type === 'Polygon' && geom.coordinates?.[0]?.length > 0) {
              const first = geom.coordinates[0][0];
              if (typeof first[1] === 'number' && typeof first[0] === 'number') {
                pos = [first[1], first[0]];
              }
            }
          } catch (e) {
            console.debug('Magnetic snap A notice:', e);
          }
          const latStr = typeof pos[0] === 'number' && !isNaN(pos[0]) ? pos[0].toFixed(4) : String(pos[0]);
          const lngStr = typeof pos[1] === 'number' && !isNaN(pos[1]) ? pos[1].toFixed(4) : String(pos[1]);
          return (
            <Marker position={pos} icon={startPinIcon}>
              <Popup>
                <div style={{ color: '#0f172a', fontSize: '13px' }}>
                  <strong style={{ display: 'block', color: '#10b981', marginBottom: '4px' }}>🟢 Waterbody Start (Point A)</strong>
                  <div><strong>Location:</strong> {result.start_point.matched_name}</div>
                  <div><strong>Snapped Coordinates:</strong> {latStr}, {lngStr}</div>
                </div>
              </Popup>
            </Marker>
          );
        })()}

        {/* End Point B Marker with Magnetic Snapping */}
        {result?.end_point && (() => {
          let pos: [number, number] = [Number(result.end_point.lat), Number(result.end_point.lng)];
          try {
            const geom = result.hydrology?.flowline_geojson?.features?.[0]?.geometry;
            if (geom?.type === 'LineString' && geom.coordinates?.length > 0) {
              const last = geom.coordinates[geom.coordinates.length - 1];
              if (typeof last[1] === 'number' && typeof last[0] === 'number') {
                pos = [last[1], last[0]];
              }
            } else if (geom?.type === 'Polygon' && geom.coordinates?.[0]?.length > 0) {
              const ring = geom.coordinates[0];
              const last = ring[ring.length - 1];
              if (typeof last[1] === 'number' && typeof last[0] === 'number') {
                pos = [last[1], last[0]];
              }
            }
          } catch (e) {
            console.debug('Magnetic snap B notice:', e);
          }
          const latStr = typeof pos[0] === 'number' && !isNaN(pos[0]) ? pos[0].toFixed(4) : String(pos[0]);
          const lngStr = typeof pos[1] === 'number' && !isNaN(pos[1]) ? pos[1].toFixed(4) : String(pos[1]);
          return (
            <Marker position={pos} icon={endPinIcon}>
              <Popup>
                <div style={{ color: '#0f172a', fontSize: '13px' }}>
                  <strong style={{ display: 'block', color: '#ef4444', marginBottom: '4px' }}>🔴 Waterbody End (Point B)</strong>
                  <div><strong>Location:</strong> {result.end_point.matched_name}</div>
                  <div><strong>Snapped Coordinates:</strong> {latStr}, {lngStr}</div>
                </div>
              </Popup>
            </Marker>
          );
        })()}

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
        {result?.start_point && (
          <div className={styles.legendItem}>
            <div className={styles.legendDot} style={{ background: '#10b981' }} />
            <span>Point A (Waterbody Start)</span>
          </div>
        )}
        {result?.end_point && (
          <div className={styles.legendItem}>
            <div className={styles.legendDot} style={{ background: '#ef4444' }} />
            <span>Point B (Waterbody End)</span>
          </div>
        )}
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
        <div className={styles.legendItem}>
          <div className={styles.legendDot} style={{ border: '2px solid #ef4444', background: 'rgba(239, 68, 68, 0.2)' }} />
          <span>EPA ATTAINS Impaired Unit</span>
        </div>
        <div className={styles.legendItem}>
          <div className={styles.legendDot} style={{ border: '2px solid #22c55e', background: 'rgba(34, 197, 94, 0.2)' }} />
          <span>EPA ATTAINS Supporting Unit</span>
        </div>
      </div>
    </div>
  );
};
