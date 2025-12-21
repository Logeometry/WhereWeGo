// src/contexts/WishlistContext.js (이전 답변과 동일하게 유지)
import React, { createContext, useState, useEffect, useContext, useCallback } from 'react';
import allTouristSpotsData from '../data/touristData'; // 모든 관광지 데이터를 가져옵니다.

export const WishlistContext = createContext();

export const useWishlist = () => {
  return useContext(WishlistContext);
};

export const WishlistProvider = ({ children }) => {
  const [wishlistIds, setWishlistIds] = useState(() => {
    const localData = localStorage.getItem('wishlistIds');
    return localData ? JSON.parse(localData) : [];
  });

  useEffect(() => {
    localStorage.setItem('wishlistIds', JSON.stringify(wishlistIds));
  }, [wishlistIds]);

  const addToWishlist = useCallback((itemId) => {
    console.log('위시리스트에 추가:', itemId);
    setWishlistIds((prevIds) => {
      if (!prevIds.includes(itemId)) {
        const newIds = [...prevIds, itemId];
        console.log('새로운 위시리스트 IDs:', newIds);
        return newIds;
      }
      return prevIds;
    });
  }, []);

  const removeFromWishlist = useCallback((itemId) => {
    console.log('위시리스트에서 제거:', itemId);
    setWishlistIds((prevIds) => {
      const newIds = prevIds.filter((id) => id !== itemId);
      console.log('새로운 위시리스트 IDs:', newIds);
      return newIds;
    });
  }, []);

  const isWishlisted = useCallback((itemId) => {
    return wishlistIds.includes(itemId);
  }, [wishlistIds]);

  const wishlistItems = wishlistIds.map(id => allTouristSpotsData[id]).filter(item => item);

  const value = {
    wishlistItems,
    wishlistIds,
    addToWishlist,
    removeFromWishlist,
    isWishlisted,
  };

  return (
    <WishlistContext.Provider value={value}>
      {children}
    </WishlistContext.Provider>
  );
};