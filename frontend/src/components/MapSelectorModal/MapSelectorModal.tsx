import React, { useState } from 'react';
import { MapContainer, TileLayer, Marker, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { X, Check } from 'lucide-react';

// Fix leafet default icon issue in React
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

interface MapSelectorModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (lat: number, lng: number) => void;
}

const LocationMarker = ({ position, setPosition }: { position: L.LatLng | null, setPosition: (p: L.LatLng) => void }) => {
  useMapEvents({
    click(e) {
      setPosition(e.latlng);
    },
  });
  return position === null ? null : <Marker position={position} />;
};

export const MapSelectorModal: React.FC<MapSelectorModalProps> = ({ isOpen, onClose, onConfirm }) => {
  const [position, setPosition] = useState<L.LatLng | null>(null);

  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh',
      backgroundColor: 'rgba(0,0,0,0.5)', zIndex: 9999,
      display: 'flex', alignItems: 'center', justifyContent: 'center'
    }}>
      <div style={{
        background: 'var(--bg-card)',
        padding: '20px',
        borderRadius: 'var(--radius-lg)',
        width: '90%',
        maxWidth: '800px',
        border: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        gap: '16px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3 style={{ margin: 0, color: 'var(--text-primary)' }}>Select Location on Map</h3>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={24} />
          </button>
        </div>
        
        <p style={{ margin: 0, fontSize: '14px', color: 'var(--text-muted)' }}>
          Click anywhere on the map to drop a pin on the waterbody you want to assess.
        </p>

        <div style={{ height: '400px', width: '100%', borderRadius: 'var(--radius-md)', overflow: 'hidden' }}>
          <MapContainer 
            center={[39.8283, -98.5795]} 
            zoom={4} 
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <LocationMarker position={position} setPosition={setPosition} />
          </MapContainer>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px' }}>
          <button 
            onClick={onClose}
            style={{
              padding: '8px 16px', background: 'transparent', border: '1px solid var(--border-color)', 
              color: 'var(--text-primary)', borderRadius: 'var(--radius-md)', cursor: 'pointer'
            }}
          >
            Cancel
          </button>
          <button 
            onClick={() => position && onConfirm(position.lat, position.lng)}
            disabled={!position}
            style={{
              padding: '8px 16px', background: 'var(--primary-color)', border: 'none', 
              color: 'white', borderRadius: 'var(--radius-md)', cursor: position ? 'pointer' : 'not-allowed',
              opacity: position ? 1 : 0.5, display: 'flex', alignItems: 'center', gap: '8px'
            }}
          >
            <Check size={16} />
            Assess Location
          </button>
        </div>
      </div>
    </div>
  );
};
