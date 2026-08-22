import React, { useState } from 'react';
import { Search, Loader2, Compass } from 'lucide-react';
import styles from './SearchBar.module.css';

interface SearchBarProps {
  onSearch: (query: string) => void;
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

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSearch(query.trim());
    }
  };

  const handleChipClick = (example: string) => {
    if (!isLoading) {
      setQuery(example);
      onSearch(example);
    }
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
        <button type="submit" className={styles.button} disabled={isLoading || !query.trim()}>
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
    </div>
  );
};
