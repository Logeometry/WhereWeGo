// src/contexts/ItineraryContext.jsx
import React, { createContext, useContext, useMemo, useState } from 'react';

const ItineraryContext = createContext(null);

export function ItineraryProvider({ children }) {
  const [selectedSpots, setSelectedSpots] = useState([]); // [{id, name, ...}]

  const addSpot = (spot) => {
    setSelectedSpots((prev) => (prev.some((s) => s.id === spot.id) ? prev : [...prev, spot]));
  };

  const removeSpot = (id) => setSelectedSpots((prev) => prev.filter((s) => s.id !== id));
  const clearAll = () => setSelectedSpots([]);

  const value = useMemo(
    () => ({ selectedSpots, addSpot, removeSpot, clearAll, setSelectedSpots }),
    [selectedSpots]
  );

  return <ItineraryContext.Provider value={value}>{children}</ItineraryContext.Provider>;
}

export function useItinerary() {
  const ctx = useContext(ItineraryContext);
  if (!ctx) throw new Error('useItinerary must be used within ItineraryProvider');
  return ctx;
}
