import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, Polyline, useMapEvents, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { X, Check, MapPin, ArrowRight, RotateCcw } from 'lucide-react';

// Custom Map Pins for Start (A) and End (B)
const startIcon = new L.DivIcon({
  className: 'custom-start-pin',
  html: `<div style="background:#10b981; color:white; border-radius:50%; width:28px; height:28px; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:14px; border:2px solid white; box-shadow:0 2px 6px rgba(0,0,0,0.3);">A</div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14]
});

const endIcon = new L.DivIcon({
  className: 'custom-end-pin',
  html: `<div style="background:#ef4444; color:white; border-radius:50%; width:28px; height:28px; display:flex; align-items:center; justify-content:center; font-weight:bold; font-size:14px; border:2px solid white; box-shadow:0 2px 6px rgba(0,0,0,0.3);">B</div>`,
  iconSize: [28, 28],
  iconAnchor: [14, 14]
});

const singleIcon = new L.DivIcon({
  className: 'custom-single-pin',
  html: `<div style="background:#3b82f6; color:white; border-radius:50%; width:24px; height:24px; display:flex; align-items:center; justify-content:center; border:2px solid white; box-shadow:0 2px 6px rgba(0,0,0,0.3);"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg></div>`,
  iconSize: [24, 24],
  iconAnchor: [12, 12]
});

export interface MapSelectionPayload {
  mode: 'single' | 'segment';
  lat?: number;
  lng?: number;
  start_lat?: number;
  start_lng?: number;
  end_lat?: number;
  end_lng?: number;
}

interface MapSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (payload: MapSelectionPayload) => void;
}

const MapClickHandler = ({
  mode,
  singlePos,
  setSinglePos,
  startPos,
  setStartPos,
  endPos,
  setEndPos
}: {
  mode: 'single' | 'segment';
  singlePos: L.LatLng | null;
  setSinglePos: (p: L.LatLng) => void;
  startPos: L.LatLng | null;
  setStartPos: (p: L.LatLng) => void;
  endPos: L.LatLng | null;
  setEndPos: (p: L.LatLng) => void;
}) => {
  useMapEvents({
    click(e) {
      if (mode === 'single') {
        setSinglePos(e.latlng);
      } else {
        if (!startPos) {
          setStartPos(e.latlng);
        } else if (!endPos) {
          setEndPos(e.latlng);
        } else {
          // If both are set, reset start
          setStartPos(e.latlng);
          setEndPos(null as any);
        }
      }
    }
  });

  return (
    <>
      {mode === 'single' && singlePos && (
        <Marker position={singlePos} icon={singleIcon}>
          <Tooltip permanent>Selected Location</Tooltip>
        </Marker>
      )}

      {mode === 'segment' && startPos && (
        <Marker position={startPos} icon={startIcon}>
          <Tooltip permanent>Point A (Start / Upstream)</Tooltip>
        </Marker>
      )}

      {mode === 'segment' && endPos && (
        <Marker position={endPos} icon={endIcon}>
          <Tooltip permanent>Point B (End / Downstream)</Tooltip>
        </Marker>
      )}

      {mode === 'segment' && startPos && endPos && (
        <Polyline
          positions={[
            [startPos.lat, startPos.lng],
            [endPos.lat, endPos.lng]
          ]}
          pathOptions={{ color: '#38bdf8', weight: 3, dashArray: '6, 8', opacity: 0.9 }}
        />
      )}
    </>
  );
};

export const MapSelectorModal: React.FC<MapSelectorModalProps> = ({ isOpen, onClose, onConfirm }) => {
  const [mode, setMode] = useState<'single' | 'segment'>('segment');
  const [singlePos, setSinglePos] = useState<L.LatLng | null>(null);
  const [startPos, setStartPos] = useState<L.LatLng | null>(null);
  const [endPos, setEndPos] = useState<L.LatLng | null>(null);

  if (!isOpen) return null;

  const handleReset = () => {
    setSinglePos(null);
    setStartPos(null);
    setEndPos(null);
  };

  const handleConfirm = () => {
    if (mode === 'single' && singlePos) {
      onConfirm({
        mode: 'single',
        lat: singlePos.lat,
        lng: singlePos.lng
      });
    } else if (mode === 'segment' && startPos && endPos) {
      onConfirm({
        mode: 'segment',
        start_lat: startPos.lat,
        start_lng: startPos.lng,
        end_lat: endPos.lat,
        end_lng: endPos.lng
      });
    }
  };

  const isValid = (mode === 'single' && singlePos !== null) || (mode === 'segment' && startPos !== null && endPos !== null);

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
      backgroundColor: 'rgba(0,0,0,0.6)', zIndex: 9999, backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div style={{
        background: 'var(--bg-card)',
        padding: '24px',
        borderRadius: 'var(--radius-lg)',
        width: '90%',
        maxWidth: '850px',
        border: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '18px', color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <MapPin size={20} style={{ color: '#38bdf8' }} />
              Select Assessment Geometry on Map
            </h3>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Choose a single point or define a custom waterbody corridor (Point A ➔ Point B).
            </span>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={24} />
          </button>
        </div>

        {/* Mode Selector Tabs */}
        <div style={{ display: 'flex', gap: '8px', background: 'var(--bg-surface)', padding: '4px', borderRadius: 'var(--radius-md)', width: 'fit-content' }}>
          <button
            type="button"
            onClick={() => { setMode('segment'); handleReset(); }}
            style={{
              padding: '6px 14px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: mode === 'segment' ? 'var(--primary-color)' : 'transparent',
              color: mode === 'segment' ? '#ffffff' : 'var(--text-secondary)',
              fontWeight: 500,
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            <span>Point A ➔ Point B Corridor</span>
            <span style={{ fontSize: '10px', background: 'rgba(255,255,255,0.2)', padding: '2px 6px', borderRadius: '10px' }}>Recommended</span>
          </button>
          <button
            type="button"
            onClick={() => { setMode('single'); handleReset(); }}
            style={{
              padding: '6px 14px',
              borderRadius: 'var(--radius-sm)',
              border: 'none',
              background: mode === 'single' ? 'var(--primary-color)' : 'transparent',
              color: mode === 'single' ? '#ffffff' : 'var(--text-secondary)',
              fontWeight: 500,
              fontSize: '13px',
              cursor: 'pointer'
            }}
          >
            Single Location (15km Radius)
          </button>
        </div>

        {/* Dynamic Instructions Banner */}
        <div style={{
          padding: '10px 14px',
          background: 'rgba(56, 189, 248, 0.08)',
          border: '1px solid rgba(56, 189, 248, 0.2)',
          borderRadius: 'var(--radius-md)',
          fontSize: '13px',
          color: 'var(--text-primary)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          {mode === 'segment' ? (
            <span>
              {!startPos && <>👉 <strong>Step 1:</strong> Click on the waterbody to drop 🟢 <strong>Point A (Start)</strong>.</>}
              {startPos && !endPos && <>👉 <strong>Step 2:</strong> Click downstream on the waterbody to drop 🔴 <strong>Point B (End)</strong>.</>}
              {startPos && endPos && <>✅ <strong>Corridor Defined:</strong> Point A ({startPos.lat.toFixed(3)}, {startPos.lng.toFixed(3)}) ➔ Point B ({endPos.lat.toFixed(3)}, {endPos.lng.toFixed(3)})</>}
            </span>
          ) : (
            <span>
              {!singlePos ? <>👉 Click anywhere on the waterbody to drop a pin.</> : <>✅ Point Selected: ({singlePos.lat.toFixed(4)}, {singlePos.lng.toFixed(4)})</>}
            </span>
          )}

          {(singlePos || startPos || endPos) && (
            <button
              type="button"
              onClick={handleReset}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
                fontSize: '12px'
              }}
            >
              <RotateCcw size={13} />
              Reset Pins
            </button>
          )}
        </div>

        {/* Leaflet Map */}
        <div style={{ height: '420px', width: '100%', borderRadius: 'var(--radius-md)', overflow: 'hidden', border: '1px solid var(--border-color)' }}>
          <MapContainer 
            center={[38.9, -84.5]} 
            zoom={6} 
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapClickHandler 
              mode={mode}
              singlePos={singlePos}
              setSinglePos={setSinglePos}
              startPos={startPos}
              setStartPos={setStartPos}
              endPos={endPos}
              setEndPos={setEndPos}
            />
          </MapContainer>
        </div>

        {/* Footer Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button 
            type="button"
            onClick={onClose}
            style={{
              padding: '8px 16px', background: 'transparent', border: '1px solid var(--border-color)', 
              color: 'var(--text-primary)', borderRadius: 'var(--radius-md)', cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button 
            type="button"
            onClick={handleConfirm}
            disabled={!isValid}
            style={{
              padding: '8px 20px', background: isValid ? 'var(--primary-color)' : 'rgba(56, 189, 248, 0.3)', border: 'none', 
              color: 'white', borderRadius: 'var(--radius-md)', cursor: isValid ? 'pointer' : 'not-allowed',
              fontWeight: 500, display: 'flex', alignItems: 'center', gap: '8px', boxShadow: isValid ? '0 4px 12px rgba(56, 189, 248, 0.3)' : 'none'
            }}
          >
            <Check size={16} />
            {mode === 'segment' ? 'Assess Waterbody Corridor' : 'Assess Location'}
          </button>
        </div>
      </div>
    </div>
  );
};
