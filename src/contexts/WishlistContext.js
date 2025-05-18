// src/contexts/WishlistContext.js
import React, { createContext, useState, useEffect, useContext }
from 'react';

// touristDetails 객체를 불러옵니다. 경로가 다를 경우 수정해주세요.
// 실제로는 API 호출이나 중앙 데이터 저장소에서 가져올 수 있습니다.
import { touristDetails } from '../pages/TouristDetailPage'; // 경로 주의!

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

  const addToWishlist = (itemId) => {
    if (!wishlistIds.includes(itemId)) {
      setWishlistIds((prevIds) => [...prevIds, itemId]);
    }
  };

  const removeFromWishlist = (itemId) => {
    setWishlistIds((prevIds) => prevIds.filter((id) => id !== itemId));
  };

  const isWishlisted = (itemId) => {
    return wishlistIds.includes(itemId);
  };

  // ID 배열을 기반으로 실제 관광지 객체 배열을 만듭니다.
  const wishlistItems = wishlistIds.map(id => touristDetails[id]).filter(item => item); // ID에 해당하는 아이템이 없을 경우 필터링

  const value = {
    wishlistItems, // 실제 아이템 객체 배열
    wishlistIds,   // 아이템 ID 배열
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