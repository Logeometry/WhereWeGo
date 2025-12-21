// src/api/nearby.js
const API_BASE = "http://localhost:8000/api/v1";

// 주변 관광지 조회
export async function getNearbyPlaces(placeId, maxDistance = 5.0, includeCrowding = false) {
  try {
    const url = `${API_BASE}/nearby/${placeId}?max_distance=${maxDistance}${
      includeCrowding ? "&include_crowding=true" : ""
    }`;
    const res = await fetch(url);
    return await res.json();
  } catch (err) {
    console.error("getNearbyPlaces error:", err);
    return [];
  }
}

// 주변 카페 조회
export async function getNearbyCafes(placeId, maxDistance = 5.0) {
  try {
    const res = await fetch(`${API_BASE}/nearby/cafes/${placeId}?max_distance=${maxDistance}`);
    return await res.json();
  } catch (err) {
    console.error("getNearbyCafes error:", err);
    return [];
  }
}

// 주변 음식점 조회
export async function getNearbyRestaurants(placeId, maxDistance = 5.0) {
  try {
    const res = await fetch(`${API_BASE}/nearby/restaurants/${placeId}?max_distance=${maxDistance}`);
    return await res.json();
  } catch (err) {
    console.error("getNearbyRestaurants error:", err);
    return [];
  }
}

// 혼잡도 조회
export async function getPlaceCrowding(placeId) {
  try {
    const res = await fetch(`${API_BASE}/place/crowding/${placeId}`);
    return await res.json();
  } catch (err) {
    console.error("getPlaceCrowding error:", err);
    return null;
  }
}
