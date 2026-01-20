// utils/googlePhoto.js
const GOOGLE_API_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;

export function getGooglePlacePhoto(place) {
  if (!GOOGLE_API_KEY) return '';

  // Google Place Photo API는 photo_reference가 필요하지만,
  // 단순히 이름으로 검색해도 대표 이미지가 나오는 unofficial endpoint 활용 가능:
  const query = encodeURIComponent(place.name || place.address || '');
  return `https://maps.googleapis.com/maps/api/place/findplacefromtext/json?input=${query}&inputtype=textquery&fields=photos&key=${GOOGLE_API_KEY}`;
}
