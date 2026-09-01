import React, { useState } from 'react';
import { Search, Loader2, Compass, MapPin } from 'lucide-react';
import styles from './SearchBar.module.css';
import { MapSelectorModal, MapSelectionPayload } from '../MapSelectorModal/MapSelectorModal';

interface SearchBarProps {
  onSearch: (payload: {
    query: string;
    lat?: number;
    lng?: number;
    start_lat?: number;
    start_lng?: number;
    end_lat?: number;
    end_lng?: number;
  }) => void;
  isLoading: boolean;
}

const DEMO_EXAMPLES = [
  'Mississippi River near New Orleans',
  'Lake Tahoe',
  'Chesapeake Bay near Annapolis',
  'Colorado River near Grand Canyon',
  'Hudson River near Poughkeepsie',
];

export const SearchBar: React.FC<SearchBarProps> = ({ onSearch, isLoading }) => {
  const [query, setQuery] = useState('');
  const [isMapOpen, setIsMapOpen] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch({ query: query.trim() });
    }
  };

  const handleChipClick = (example: string) => {
    if (!isLoading) {
      setQuery(example);
      onSearch({ query: example });
    }
  };

  const handleMapConfirm = (payload: MapSelectionPayload) => {
    setIsMapOpen(false);
    if (payload.mode === 'segment' && payload.start_lat && payload.end_lat) {
      const segmentQuery = `Waterbody Corridor: (${payload.start_lat.toFixed(3)}, ${payload.start_lng?.toFixed(3)}) ➔ (${payload.end_lat.toFixed(3)}, ${payload.end_lng?.toFixed(3)})`;
      setQuery(segmentQuery);
      onSearch({
        query: segmentQuery,
        start_lat: payload.start_lat,
        start_lng: payload.start_lng,
        end_lat: payload.end_lat,
        end_lng: payload.end_lng
      });
    } else if (payload.lat && payload.lng) {
      const mapQuery = `Map Selection: ${payload.lat.toFixed(4)}, ${payload.lng.toFixed(4)}`;
      setQuery(mapQuery);
      onSearch({ query: mapQuery, lat: payload.lat, lng: payload.lng });
    }
  };

  return (
    <div className={styles.container}>
      <form onSubmit={handleSubmit} className={styles.searchForm}>
        <Search className={styles.icon} size={20} />
        <input
          type="text"
          className={styles.input}
          placeholder="Enter water body name or click the Map Pin to select a Waterbody Corridor (Point A ➔ Point B)..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isLoading}
        />
        <button 
          type="button" 
          onClick={() => setIsMapOpen(true)}
          style={{ 
            background: 'transparent', border: 'none', color: 'var(--text-muted)', 
            cursor: 'pointer', padding: '0 8px', display: 'flex', alignItems: 'center', gap: '4px' 
          }}
          title="Select Waterbody Corridor or Location on Map"
        >
          <MapPin size={20} style={{ color: '#38bdf8' }} />
        </button>
        <button type="submit" className={styles.button} disabled={isLoading || (!query.trim() && !isMapOpen)}>
          {isLoading ? (
            <>
              <Loader2 className="animate-spin" size={16} />
              <span>Analyzing...</span>
            </>
          ) : (
            <>
              <Compass size={16} />
              <span>Assess Waterbody</span>
            </>
          )}
        </button>
      </form>

      {/* Demonstration Examples */}
      <div className={styles.examplesWrapper}>
        <span className={styles.examplesLabel}>Examples:</span>
        <div className={styles.chipsContainer}>
          {DEMO_EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              className={styles.chip}
              onClick={() => handleChipClick(example)}
              disabled={isLoading}
            >
              {example}
            </button>
          ))}
        </div>
      </div>

      <MapSelectorModal 
        isOpen={isMapOpen} 
        onClose={() => setIsMapOpen(false)} 
        onConfirm={handleMapConfirm} 
      />
    </div>
  );
};
