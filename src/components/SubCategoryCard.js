import React, { memo, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Card, CardMedia, CardContent, Typography, Box, IconButton, Chip } from '@mui/material';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import FavoriteIcon from '@mui/icons-material/Favorite';
import { Link } from 'react-router-dom';
import { useWishlist } from '../contexts/WishlistContext';

// Google 키 (Places + Street View 활성화 필요)
const GMAPS_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;

// ---- Google Places Photo: place_id → photo URL ----
async function resolvePlacePhotoUrl({ name, address, region }) {
  if (!GMAPS_KEY) return '';

  // 1) Find Place From Text (정확도 높은 장소 ID 찾기)
  // fields에 photos 포함해서 바로 photo_reference도 받도록 함
  const query =
    [name, address || '', region || ''].filter(Boolean).join(' ').trim();

  if (!query) return '';

  const findUrl = new URL('https://maps.googleapis.com/maps/api/place/findplacefromtext/json');
  findUrl.searchParams.set('input', query);
  findUrl.searchParams.set('inputtype', 'textquery');
  findUrl.searchParams.set('fields', 'place_id,photos');
  findUrl.searchParams.set('language', 'ko');
  findUrl.searchParams.set('key', GMAPS_KEY);

  try {
    const res = await fetch(findUrl.toString(), { credentials: 'omit' });
    const json = await res.json();

    if (json.status !== 'OK' || !json.candidates?.length) return '';

    const photos = json.candidates[0]?.photos;
    if (!photos?.length) return '';

    const photoRef = photos[0].photo_reference;
    if (!photoRef) return '';

    // 2) Place Photo URL (img src에 직접 사용 가능)
    const photoUrl = new URL('https://maps.googleapis.com/maps/api/place/photo');
    photoUrl.searchParams.set('maxwidth', '960');
    photoUrl.searchParams.set('photo_reference', photoRef);
    photoUrl.searchParams.set('key', GMAPS_KEY);
    return photoUrl.toString();
  } catch {
    return '';
  }
}

// ---- Google Street View (좌표 실사) 사용 가능 여부 체크 ----
async function resolveStreetViewUrlIfAvailable(coords) {
  if (!GMAPS_KEY) return '';
  if (!Array.isArray(coords) || coords.length < 2) return '';

  const [lng, lat] = coords; // [lng, lat]

  // 먼저 메타데이터 확인 (정확도/가용성 체크)
  const metaUrl = new URL('https://maps.googleapis.com/maps/api/streetview/metadata');
  metaUrl.searchParams.set('location', `${lat},${lng}`);
  metaUrl.searchParams.set('key', GMAPS_KEY);

  try {
    const metaRes = await fetch(metaUrl.toString(), { credentials: 'omit' });
    const meta = await metaRes.json();
    if (meta.status !== 'OK') return '';

    // OK면 실제 이미지 URL 생성
    const svUrl = new URL('https://maps.googleapis.com/maps/api/streetview');
    svUrl.searchParams.set('size', '640x426'); // 카드 비율 근사(3:2)
    svUrl.searchParams.set('location', `${lat},${lng}`);
    svUrl.searchParams.set('fov', '80');
    svUrl.searchParams.set('key', GMAPS_KEY);
    return svUrl.toString();
  } catch {
    return '';
  }
}

const SubCategoryCard = ({ place, subCategoryLabel }) => {
  const { isWishlisted, addToWishlist, removeFromWishlist } = useWishlist();

  // 안전한 id
  const placeId = place.id || place._id;
  const wished  = isWishlisted(placeId);

  const handleWishlistToggle = useCallback((e) => {
    e.preventDefault();
    e.stopPropagation();
    wished ? removeFromWishlist(placeId) : addToWishlist(placeId);
  }, [wished, placeId, addToWishlist, removeFromWishlist]);

  // 1) DB 명시 이미지 (가장 정확)
  const explicitImage =
    (place.image_url && String(place.image_url).trim()) ||
    (place.image && String(place.image).trim()) ||
    (Array.isArray(place.images) && place.images[0]) ||
    '';

  // 최종 이미지 상태
  const [imageSrc, setImageSrc] = useState(explicitImage || '');
  const [resolved, setResolved] = useState(!!explicitImage);
  const abortRef = useRef(false);

  // 2) Places Photo → 3) Street View(메타데이터 OK일 때만) 순차 시도
  useEffect(() => {
    abortRef.current = false;
    let mounted = true;

    async function resolveImage() {
      // 이미 명시 이미지가 있으면 종료
      if (explicitImage) {
        setResolved(true);
        return;
      }

      // 2) Google Places Photo (정확한 장소 사진)
      const photoUrl = await resolvePlacePhotoUrl({
        name: place?.name,
        address: place?.address,
        region: place?.region,
      });

      if (mounted && !abortRef.current && photoUrl) {
        setImageSrc(photoUrl);
        setResolved(true);
        return;
      }

      // 3) Street View (실사) — 메타데이터 확인 후 사용
      const svUrl = await resolveStreetViewUrlIfAvailable(place?.location?.coordinates);
      if (mounted && !abortRef.current && svUrl) {
        setImageSrc(svUrl);
        setResolved(true);
        return;
      }

      // 끝: 이미지 없음 → 플레이스홀더 표시
      if (mounted && !abortRef.current) {
        setImageSrc('');
        setResolved(true);
      }
    }

    resolveImage();

    return () => {
      abortRef.current = true;
      mounted = false;
    };
    // place 변경 시 재시도
  }, [explicitImage, place?.name, place?.address, place?.region, place?.location?.coordinates]);

  const showPlaceholder = resolved && !imageSrc;

  return (
    <Card
      component={Link}
      to={`/tourist/${encodeURIComponent(placeId)}`}
      sx={{
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        textDecoration: 'none',
        color: 'inherit',
        transition: 'all 0.3s ease-in-out',
        '&:hover': { transform: 'translateY(-4px)', boxShadow: '0 8px 25px rgba(0,0,0,0.15)' },
      }}
    >
      {/* 이미지 영역 */}
      <Box sx={{ position: 'relative', width: '100%', aspectRatio: '3 / 2', overflow: 'hidden' }}>
        {!showPlaceholder && imageSrc ? (
          <CardMedia
            component="img"
            image={imageSrc}
            alt={place.name}
            sx={{ objectFit: 'cover', width: '100%', height: '100%' }}
            onError={() => {
              // 현재 소스 로딩 실패 → 이미지 제거(플레이스홀더 표시)
              setImageSrc('');
            }}
          />
        ) : (
          <Box
            sx={{
              width: '100%',
              height: '100%',
              backgroundColor: '#f5f5f5',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#666',
              border: '2px dashed #ccc',
            }}
          >
            <Typography variant="body2" sx={{ textAlign: 'center', mb: 1 }}>📷</Typography>
            <Typography variant="caption" sx={{ textAlign: 'center', fontSize: '12px' }}>
              이미지를 업로드 해주세요
            </Typography>
          </Box>
        )}

        {/* 위시리스트 버튼 */}
        <IconButton
          onClick={handleWishlistToggle}
          sx={{
            position: 'absolute',
            top: 8,
            right: 8,
            backgroundColor: 'rgba(255, 255, 255, 0.9)',
            '&:hover': { backgroundColor: 'rgba(255, 255, 255, 1)' },
            width: 36, height: 36,
          }}
        >
          {wished
            ? <FavoriteIcon sx={{ color: '#e91e63', fontSize: 20 }} />
            : <FavoriteBorderIcon sx={{ color: '#666', fontSize: 20 }} />
          }
        </IconButton>

        {/* 카테고리 태그 */}
        {subCategoryLabel && (
          <Chip
            label={subCategoryLabel}
            size="small"
            sx={{
              position: 'absolute',
              bottom: 8,
              left: 8,
              backgroundColor: 'rgba(102, 126, 234, 0.9)',
              color: 'white',
              fontSize: '10px',
              height: 24,
            }}
          />
        )}
      </Box>

      {/* 텍스트 영역 */}
      <CardContent sx={{ flexGrow: 1, p: 3 }}>
        <Typography
          variant="h6"
          component="h3"
          sx={{
            fontWeight: 'bold',
            fontSize: '18px',
            lineHeight: 1.3,
            mb: 1.5,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
          }}
        >
          {place.name}
        </Typography>

        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ fontSize: '14px', mb: 1.5, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
        >
          {place.address || place.region || '주소 정보 없음'}
        </Typography>

        {Number(place.rating) > 0 && (
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', mt: 'auto' }}>
            <Typography variant="caption" color="primary" sx={{ fontWeight: 'bold' }}>
              ⭐ {Number(place.rating).toFixed(1)}
            </Typography>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default memo(SubCategoryCard, (prev, next) => {
  return (
    (prev.place._id || prev.place.id) === (next.place._id || next.place.id) &&
    prev.place.name === next.place.name &&
    prev.subCategoryLabel === next.subCategoryLabel
  );
});
