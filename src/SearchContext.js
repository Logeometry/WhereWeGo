// SearchContext.js
import React, { createContext, useState, useEffect } from 'react';

export const SearchContext = createContext();

export const SearchProvider = ({ children }) => {
  const [recentSearches, setRecentSearches] = useState([]);

  useEffect(() => {
    const saved = localStorage.getItem('sharedRecentSearches');
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved));
      } catch (error) {
        console.error("Failed to parse recent searches from localStorage", error);
        localStorage.removeItem('sharedRecentSearches');
      }
    }
  }, []);

  const updateSearches = (newSearch) => {
    if (newSearch && newSearch.trim()) {
      const trimmedSearch = newSearch.trim();
      setRecentSearches(prevSearches => {
        const updated = [trimmedSearch, ...prevSearches.filter(s => s !== trimmedSearch)].slice(0, 5);
        localStorage.setItem('sharedRecentSearches', JSON.stringify(updated));
        return updated;
      });
      return true;
    }
    return false;
  };

  const removeSearch = (index) => {
    setRecentSearches(prevSearches => {
      const updated = [...prevSearches];
      updated.splice(index, 1);
      localStorage.setItem('sharedRecentSearches', JSON.stringify(updated));
      return updated;
    });
  };

  const clearAllSearches = () => {
    setRecentSearches([]);
    localStorage.removeItem('sharedRecentSearches');
  };

  return (
    <SearchContext.Provider value={{ recentSearches, updateSearches, removeSearch, clearAllSearches }}>
      {children}
    </SearchContext.Provider>
  );
};