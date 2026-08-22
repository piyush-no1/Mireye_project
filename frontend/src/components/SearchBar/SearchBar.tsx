import React, { useState } from 'react';
import { Search, Loader2, Compass, MapPin } from 'lucide-react';
import styles from './SearchBar.module.css';
import { MapSelectorModal } from '../MapSelectorModal';

interface SearchBarProps {
  onSearch: (payload: { query: string; lat?: number; lng?: number }) => void;
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

  const handleMapConfirm = (lat: number, lng: number) => {
    setIsMapOpen(false);
    const mapQuery = `Map Selection: ${lat.toFixed(4)}, ${lng.toFixed(4)}`;
    setQuery(mapQuery);
    onSearch({ query: mapQuery, lat, lng });
  };

  return (
    <div className={styles.container}>
      <form onSubmit={handleSubmit} className={styles.searchForm}>
        <Search className={styles.icon} size={20} />
        <input
          type="text"
          className={styles.input}
          placeholder="Enter any water body name in the United States (River, Lake, Bay, Estuary, Sound, Reservoir)..."
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
          title="Select Location on Map"
        >
          <MapPin size={20} />
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
