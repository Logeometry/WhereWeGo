// src/pages/TravelPlanSamplePage.jsx
import React, { useMemo, useState, useCallback, useRef, useEffect } from "react";
import {
  AppBar, Toolbar, Typography, Button, Box, Paper, Stack, Avatar,
  TextField, Chip, Grid, IconButton, Badge, Collapse, Tabs, Tab,
  Rating, Divider, CircularProgress, GlobalStyles, FormControlLabel, Switch,
  ToggleButton, ToggleButtonGroup, Tooltip
} from "@mui/material";
import {
  Add as AddIcon, Share as ShareIcon, Save as SaveIcon,
  FlightTakeoff as FlightTakeoffIcon, LocationOn as LocationOnIcon,
  Restaurant as RestaurantIcon, BeachAccess as BeachAccessIcon, Museum as MuseumIcon,
  ShoppingCart as ShoppingCartIcon, ExpandMore as ExpandMoreIcon, ExpandLess as ExpandLessIcon,
  Search as SearchIcon, Close as CloseIcon, Directions as DirectionsIcon, Star as StarIcon,
  Route as RouteIcon, Layers as LayersIcon
} from "@mui/icons-material";
import { styled } from "@mui/material/styles";
import {
  GoogleMap, Marker, useLoadScript, StandaloneSearchBox,
  DirectionsRenderer, MarkerClustererF
} from "@react-google-maps/api";

// ──────────────────────────────────────────────────────────────────────────────
// 공통 no-wrap 스타일 (말줄임)
const noWrapSx = { whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" };

// 스타일
const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  borderRadius: theme.spacing(2),
  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
}));

const MapShell = styled(Box)(({ theme }) => ({
  height: "78vh",          // 지도 크게
  minHeight: 640,
  borderRadius: theme.spacing(1.5),
  overflow: "hidden",
  position: "relative",
}));

// 지도 밖(왼쪽) 장소 패널
const LeftPlacePanel = styled(Box)(({ theme }) => ({
  width: 420,
  maxWidth: 520,
  background: "#fff",
  borderRadius: theme.spacing(2),
  boxShadow: "0 2px 12px rgba(0,0,0,.12)",
  border: "1px solid #eee",
  overflow: "hidden",
  display: "flex",
  flexDirection: "column",
}));

const PanelHeaderImage = styled("div")({
  width: "100%",
  height: 220,
  backgroundSize: "cover",
  backgroundPosition: "center",
  backgroundColor: "#f1f1f1",
});

const DayTabContainer = styled(Box)(({ theme }) => ({
  maxHeight: 360,          // 일정 리스트 영역 키움
  overflowY: "auto",
  overflowX: "hidden",
  "&::-webkit-scrollbar": { width: "6px" },
  "&::-webkit-scrollbar-track": { background: "#f6f6f6", borderRadius: "4px" },
  "&::-webkit-scrollbar-thumb": { background: "#c1c1c1", borderRadius: "4px" },
  "&::-webkit-scrollbar-thumb:hover": { background: "#a8a8a8" },
}));

// 일정 Day 버튼(칸) 더 크게 + DOM으로 active prop 전달 방지
const CompactDayButton = styled(
  Button,
  { shouldForwardProp: (prop) => prop !== "active" }
)(({ theme, active }) => ({
  width: "100%",
  justifyContent: "space-between",
  textAlign: "left",
  padding: theme.spacing(2),
  marginBottom: theme.spacing(0.8),
  borderRadius: theme.spacing(1.25),
  backgroundColor: active ? "#2196f3" : "transparent",
  color: active ? "white" : theme.palette.text.primary,
  border: `1px solid ${active ? "#2196f3" : "#e0e0e0"}`,
  "&:hover": { backgroundColor: active ? "#1976d2" : "#f5f7f9" },
}));

// ──────────────────────────────────────────────────────────────────────────────
// 좌표 샘플 (데모용)
const BUSAN_CENTER = { lat: 35.1796, lng: 129.0756 };
const SPOT_COORDS = {
  "해운대 해수욕장": { lat: 35.1587, lng: 129.1604 },
  "광안리 해변": { lat: 35.1532, lng: 129.1186 },
  "감천문화마을": { lat: 35.0975, lng: 129.0106 },
  "자갈치 시장": { lat: 35.0979, lng: 129.0303 },
  "국제시장": { lat: 35.1009, lng: 129.0260 },
  "태종대": { lat: 35.0586, lng: 129.0860 },
  "오륙도": { lat: 35.1048, lng: 129.1231 },
  "동백섬": { lat: 35.1582, lng: 129.1517 },
  "범어사": { lat: 35.2759, lng: 129.0897 },
  "금강공원": { lat: 35.2424, lng: 129.0666 },
  "송도해상케이블카": { lat: 35.0768, lng: 129.0183 },
  "송도해수욕장": { lat: 35.0754, lng: 129.0177 },
  "부산타워": { lat: 35.1003, lng: 129.0321 },
  "용두산공원": { lat: 35.1008, lng: 129.0326 },
  "해동용궁사": { lat: 35.1885, lng: 129.2239 },
  "기장시장": { lat: 35.2445, lng: 129.2223 },
};

// ──────────────────────────────────────────────────────────────────────────────
// 간단 유틸
const toLatLng = (g) => ({ lat: g.lat(), lng: g.lng() });
const haversine = (a, b) => {
  const R = 6371e3; // m
  const φ1 = a.lat * Math.PI/180, φ2 = b.lat * Math.PI/180;
  const Δφ = (b.lat - a.lat) * Math.PI/180;
  const Δλ = (b.lng - a.lng) * Math.PI/180;
  const s = Math.sin(Δφ/2)**2 + Math.cos(φ1)*Math.cos(φ2)*Math.sin(Δλ/2)**2;
  return 2 * R * Math.asin(Math.sqrt(s)); // meters
};
const debounce = (fn, ms=300) => {
  let t;
  return (...args) => { clearTimeout(t); t = setTimeout(() => fn(...args), ms); };
};

// ──────────────────────────────────────────────────────────────────────────────
export default function TravelPlanSamplePage() {
  const [activeDay, setActiveDay] = useState(0);
  const [expandedDays, setExpandedDays] = useState(new Set([0]));
  const [panelTab, setPanelTab] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");

  // 선택된 장소(패널용)
  const [selectedPlace, setSelectedPlace] = useState(null); // { name, position, details, photoUrl, placeId? }
  const [nearbyFoods, setNearbyFoods] = useState([]);
  const [loadingFoods, setLoadingFoods] = useState(false);

  // 음식점 필터
  const [openNowOnly, setOpenNowOnly] = useState(false);
  const [priceLevels, setPriceLevels] = useState([0,1,2,3,4]); // ₩ ~ ₩₩₩₩

  // Day 경로
  const [route, setRoute] = useState(null);
  const [showRoute, setShowRoute] = useState(false);

  // Google 객체/서비스
  const mapRef = useRef(null);
  const placesServiceRef = useRef(null);
  const searchBoxRef = useRef(null);

  // 캐시
  const detailCacheRef = useRef(new Map());  // key: placeId, val: detail
  const idCacheRef = useRef(new Map());      // key: placeName, val: placeId
  const inFlightRef = useRef(new Set());     // key: placeId or name

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY || "",
    libraries: ["places"],
    language: "ko",
    region: "KR",
  });

  // 일정 데이터 (placeId는 데모상 일부 비워둡니다. 실서비스에서는 채워두면 정확도↑)
  const itineraryData = useMemo(() => ([
    { date: "2026. 8. 21.", dayName: "Day 1", places: [
      { id: "1", name: "감천문화마을", placeId: null, time: "14:00", icon: <MuseumIcon/> },
      { id: "2", name: "해운대 해수욕장", placeId: null, time: "16:00", icon: <BeachAccessIcon/> },
    ]},
    { date: "2026. 8. 22.", dayName: "Day 2", places: [
      { id: "3", name: "광안리 해변", placeId: null, time: "10:00", icon: <BeachAccessIcon/> },
      { id: "4", name: "자갈치 시장", placeId: null, time: "14:00", icon: <RestaurantIcon/> },
      { id: "5", name: "국제시장", placeId: null, time: "16:00", icon: <ShoppingCartIcon/> },
    ]},
    { date: "2026. 8. 23.", dayName: "Day 3", places: [
      { id: "6", name: "태종대", placeId: null, time: "09:00", icon: <MuseumIcon/> },
      { id: "7", name: "오륙도", placeId: null, time: "12:00", icon: <BeachAccessIcon/> },
      { id: "8", name: "동백섬", placeId: null, time: "15:00", icon: <MuseumIcon/> },
    ]},
    { date: "2026. 8. 24.", dayName: "Day 4", places: [
      { id: "9", name: "범어사", placeId: null, time: "10:00", icon: <MuseumIcon/> },
      { id: "10", name: "금강공원", placeId: null, time: "14:00", icon: <MuseumIcon/> },
    ]},
    { date: "2026. 8. 25.", dayName: "Day 5", places: [
      { id: "11", name: "송도해상케이블카", placeId: null, time: "11:00", icon: <FlightTakeoffIcon/> },
      { id: "12", name: "송도해수욕장", placeId: null, time: "14:00", icon: <BeachAccessIcon/> },
    ]},
    { date: "2026. 8. 26.", dayName: "Day 6", places: [
      { id: "13", name: "부산타워", placeId: null, time: "10:00", icon: <MuseumIcon/> },
      { id: "14", name: "용두산공원", placeId: null, time: "12:00", icon: <MuseumIcon/> },
    ]},
    { date: "2026. 8. 27.", dayName: "Day 7", places: [
      { id: "15", name: "해동용궁사", placeId: null, time: "09:00", icon: <MuseumIcon/> },
      { id: "16", name: "기장시장", placeId: null, time: "13:00", icon: <RestaurantIcon/> },
    ]},
  ]), []);

  const touristSpots = useMemo(() => ([
    { name: "해운대 해수욕장", location: "부산광역시 해운대구", icon: <BeachAccessIcon/>, color: "#FF6B6B" },
    { name: "광안리 해변", location: "부산 해수욕장 중 하나", icon: <BeachAccessIcon/>, color: "#FF6B6B" },
    { name: "감천문화마을", location: "한국의 마추픽추", icon: <MuseumIcon/>, color: "#FF6B6B" },
    { name: "자갈치 시장", location: "신선한 수산물", icon: <RestaurantIcon/>, color: "#FF6B6B" },
  ]), []);

  const handleDaySelect = (i) => {
    setActiveDay(i);
    setExpandedDays((prev) => new Set([...prev, i]));
    setShowRoute(false); // Day 바꾸면 경로 끔
    setRoute(null);
  };

  const toggleDayExpansion = (i, e) => {
    e.stopPropagation();
    setExpandedDays((prev) => {
      const n = new Set(prev);
      n.has(i) ? n.delete(i) : n.add(i);
      return n;
    });
  };

  const handleAddPlace = useCallback((spot) => {
    openPanel({ name: spot.name, placeId: null }); // 데모: placeId 미지정
  }, []);

  // 지도에 표시할 마커
  const activeDayMarkers = useMemo(() => {
    const list = itineraryData[activeDay]?.places || [];
    return list
      .map((p, idx) => ({ key: `day-${p.id}`, title: p.name, order: idx + 1, position: SPOT_COORDS[p.name], placeId: p.placeId }))
      .filter((m) => !!m.position);
  }, [activeDay, itineraryData]);

  const quickSpotMarkers = useMemo(() => {
    return touristSpots
      .map((s, idx) => ({ key: `quick-${idx}`, title: s.name, order: idx + 1, position: SPOT_COORDS[s.name], placeId: null }))
      .filter((m) => !!m.position);
  }, [touristSpots]);

  // 지도 옵션/센터
  const mapOptions = useMemo(() => ({
    disableDefaultUI: false,
    zoomControl: true,
    mapTypeControl: false,
    fullscreenControl: false,
    streetViewControl: false,
  }), []);
  const mapCenter = useMemo(() => activeDayMarkers[0]?.position || BUSAN_CENTER, [activeDayMarkers]);

  // ────────────────────────────────────────────────────────────────────────────
  // Places API 유틸
  const ensurePlacesService = () => {
    if (!placesServiceRef.current && mapRef.current && window.google) {
      placesServiceRef.current = new window.google.maps.places.PlacesService(mapRef.current);
    }
    return placesServiceRef.current;
  };

  const getDetailsByPlaceId = (placeId) =>
    new Promise((resolve) => {
      if (!placeId) return resolve(null);
      const cache = detailCacheRef.current.get(placeId);
      if (cache) return resolve(cache);

      const svc = ensurePlacesService();
      if (!svc) return resolve(null);

      // 중복 호출 방지
      const key = `id:${placeId}`;
      if (inFlightRef.current.has(key)) return resolve(null);
      inFlightRef.current.add(key);

      svc.getDetails(
        {
          placeId,
          language: "ko",
          fields: [
            "name","formatted_address","geometry","rating","user_ratings_total",
            "opening_hours","photos","url","website","price_level"
          ],
        },
        (detail, status) => {
          inFlightRef.current.delete(key);
          if (detail) {
            detailCacheRef.current.set(placeId, detail);
          }
          resolve(detail || null);
        }
      );
    });

  const textSearchToDetails = (name, position) =>
    new Promise((resolve) => {
      const svc = ensurePlacesService();
      if (!svc) return resolve(null);

      const cachedId = idCacheRef.current.get(name);
      if (cachedId) return getDetailsByPlaceId(cachedId).then(resolve);

      const key = `name:${name}`;
      if (inFlightRef.current.has(key)) return resolve(null);
      inFlightRef.current.add(key);

      const request = {
        query: name,
        location: position || mapCenter,
        radius: 3000,
        language: "ko",
      };

      // 세션 토큰을 사용하려면 AutocompleteSessionToken을 생성해서 request.sessionToken에 전달
      // (여기서는 간단화를 위해 생략)

      svc.textSearch(request, (results) => {
        inFlightRef.current.delete(key);
        const first = Array.isArray(results) && results.length ? results[0] : null;
        if (!first) return resolve(null);
        idCacheRef.current.set(name, first.place_id);
        getDetailsByPlaceId(first.place_id).then(resolve);
      });
    });

  const fetchNearbyFoods = (centerLatLng) =>
    new Promise((resolve) => {
      const svc = ensurePlacesService();
      if (!svc) return resolve([]);

      const request = {
        location: centerLatLng,
        radius: 900,
        type: "restaurant",
        language: "ko",
        openNow: openNowOnly || undefined,
        // price_level: 0~4, min/max만 지원
        minPriceLevel: Math.min(...priceLevels),
        maxPriceLevel: Math.max(...priceLevels),
      };

      svc.nearbySearch(request, (results) => {
        const arr = (results || []).slice(0, 20);
        resolve(arr);
      });
    });

  // Day 마커에 맞춰 지도 자동 맞춤
  const fitToMarkers = useCallback((markers) => {
    if (!mapRef.current || !window.google || markers.length === 0) return;
    const bounds = new window.google.maps.LatLngBounds();
    markers.forEach(m => bounds.extend(m.position));
    mapRef.current.fitBounds(bounds, 80); // padding
  }, []);

  useEffect(() => {
    if (!isLoaded) return;
    fitToMarkers(activeDayMarkers);
  }, [activeDay, isLoaded, fitToMarkers, activeDayMarkers]);

  // Day 경로 그리기 (Directions API)
  const buildRouteFromActiveDay = async () => {
    const list = itineraryData[activeDay]?.places || [];
    const coords = list.map(p => SPOT_COORDS[p.name]).filter(Boolean);
    if (coords.length < 2) {
      setRoute(null);
      setShowRoute(false);
      return;
    }
    const ds = new window.google.maps.DirectionsService();
    const origin = coords[0];
    const destination = coords[coords.length - 1];
    const wp = coords.slice(1, -1).map((c) => ({ location: c, stopover: true }));
    ds.route(
      {
        origin,
        destination,
        waypoints: wp,
        travelMode: window.google.maps.TravelMode.DRIVING,
        optimizeWaypoints: false,
        region: "KR",
      },
      (res, status) => {
        if (res) {
          setRoute(res);
          setShowRoute(true);
          // 경로로 bounds 자동 맞춤
          const bounds = new window.google.maps.LatLngBounds();
          res.routes[0].overview_path.forEach(p => bounds.extend(p));
          mapRef.current?.fitBounds(bounds, 80);
        } else {
          setRoute(null);
          setShowRoute(false);
        }
      }
    );
  };

  // 패널 열기 (placeId 우선, 없으면 textSearch → details)
  const openPanel = async ({ name, placeId, position }) => {
    setPanelTab(0);
    setSelectedPlace({ name, position: position || SPOT_COORDS[name] || mapCenter, loading: true, placeId });

    // 지도 이동
    if (mapRef.current?.panTo) mapRef.current.panTo(position || SPOT_COORDS[name] || mapCenter);

    // 상세 조회
    const detail = placeId
      ? await getDetailsByPlaceId(placeId)
      : await textSearchToDetails(name, position || mapCenter);

    const pos = detail?.geometry?.location
      ? toLatLng(detail.geometry.location)
      : (position || SPOT_COORDS[name] || mapCenter);

    const photoUrl = detail?.photos?.[0]?.getUrl({ maxWidth: 1200, maxHeight: 900 });

    setLoadingFoods(true);
    const foods = await fetchNearbyFoods(detail?.geometry?.location || pos);
    // Straight-line 거리 계산 후 가까운 순으로 상위 10개
    const withDist = foods.map(f => ({
      ...f,
      _distM: f?.geometry?.location ? haversine(pos, toLatLng(f.geometry.location)) : Number.POSITIVE_INFINITY,
    }));
    withDist.sort((a,b) => a._distM - b._distM);
    setNearbyFoods(withDist.slice(0, 10));
    setLoadingFoods(false);

    setSelectedPlace({
      name: detail?.name || name,
      position: pos,
      details: detail || null,
      photoUrl,
      placeId: detail?.place_id || placeId || idCacheRef.current.get(name) || null,
    });
  };

  const onClickItineraryPlace = (p) => openPanel({ name: p.name, placeId: p.placeId });

  // 음식점 필터 변경 시 리스트 갱신 (선택지 기준)
  const refreshFoods = useCallback(debounce(async () => {
    if (!selectedPlace?.position) return;
    setLoadingFoods(true);
    const foods = await fetchNearbyFoods(new window.google.maps.LatLng(selectedPlace.position.lat, selectedPlace.position.lng));
    const pos = selectedPlace.position;
    const withDist = foods.map(f => ({
      ...f,
      _distM: f?.geometry?.location ? haversine(pos, toLatLng(f.geometry.location)) : Number.POSITIVE_INFINITY,
    }));
    withDist.sort((a,b) => a._distM - b._distM);
    setNearbyFoods(withDist.slice(0, 10));
    setLoadingFoods(false);
  }, 300), [selectedPlace, openNowOnly, priceLevels]);

  useEffect(() => {
    refreshFoods();
  }, [openNowOnly, priceLevels, refreshFoods]);

  // ────────────────────────────────────────────────────────────────────────────
  // 패널 컴포넌트
  const Panel = () => {
    if (!selectedPlace) return null;
    const d = selectedPlace.details;

    return (
      <LeftPlacePanel>
        <PanelHeaderImage
          style={{
            backgroundImage: `url(${selectedPlace.photoUrl || ""})`,
            filter: selectedPlace.photoUrl ? "none" : "grayscale(10%)",
          }}
        />
        <Box sx={{ p: 2 }}>
          <Box sx={{ display: "flex", alignItems: "start", gap: 1 }}>
            <Avatar sx={{ bgcolor: "#FF6B6B", width: 30, height: 30 }}>
              <LocationOnIcon fontSize="small" />
            </Avatar>
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Typography variant="h6" sx={{ fontWeight: 800, lineHeight: 1.2, ...noWrapSx }}>
                {selectedPlace.name}
              </Typography>
              {typeof d?.rating === "number" ? (
                <Box sx={{ display: "flex", alignItems: "center", gap: .5 }}>
                  <Rating size="small" value={Number(d.rating)} precision={0.1} readOnly />
                  <Typography variant="caption" sx={noWrapSx}>
                    {d.rating} ({d.user_ratings_total?.toLocaleString()})
                  </Typography>
                </Box>
              ) : null}
              <Typography variant="body2" sx={{ color: "text.secondary", mt: .5, ...noWrapSx }}>
                {d?.formatted_address || "주소 정보 없음"}
              </Typography>
            </Box>
            <IconButton onClick={() => setSelectedPlace(null)} size="small" aria-label="닫기">
              <CloseIcon />
            </IconButton>
          </Box>

          <Box sx={{ display: "flex", gap: 1, mt: 1 }}>
            <Button
              variant="contained"
              size="small"
              startIcon={<DirectionsIcon />}
              onClick={() => {
                const { lat, lng } = selectedPlace.position || BUSAN_CENTER;
                window.open(`https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`, "_blank");
              }}
              sx={{ bgcolor: "#1976d2", ...noWrapSx }}
            >
              경로
            </Button>
            {d?.website && (
              <Button variant="outlined" size="small" onClick={() => window.open(d.website, "_blank")} sx={noWrapSx}>
                공식 사이트
              </Button>
            )}
            {d?.url && (
              <Button variant="outlined" size="small" onClick={() => window.open(d.url, "_blank")} sx={noWrapSx}>
                Google 상세
              </Button>
            )}
          </Box>
        </Box>

        <Divider />

        <Tabs value={panelTab} onChange={(_, v) => setPanelTab(v)} variant="fullWidth">
          <Tab label="개요" />
          <Tab label="음식점" />
        </Tabs>

        <Box sx={{ flex: 1, overflowY: "auto" }}>
          {panelTab === 0 && (
            <Box sx={{ p: 2 }}>
              <Typography variant="subtitle2" sx={{ mb: 1, ...noWrapSx }}>소개</Typography>
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                {d?.opening_hours?.weekday_text
                  ? `영업시간: ${d.opening_hours.weekday_text.join(" / ")}`
                  : "영업정보가 제공되지 않았습니다."}
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Chip size="small" icon={<StarIcon fontSize="small" />} label="여행지" sx={{ mr: 1 }} />
                {typeof d?.price_level === "number" && (
                  <Chip size="small" label={`가격대 ₩${"₩".repeat(d.price_level)}`} />
                )}
              </Box>
            </Box>
          )}

          {panelTab === 1 && (
            <Box sx={{ p: 2 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5, flexWrap: "wrap" }}>
                <FormControlLabel
                  control={
                    <Switch
                      size="small"
                      checked={openNowOnly}
                      onChange={(e) => setOpenNowOnly(e.target.checked)}
                    />
                  }
                  label="지금 영업중"
                />
                <ToggleButtonGroup
                  value={priceLevels}
                  onChange={(_, val) => val?.length && setPriceLevels(val)}
                  aria-label="가격대"
                  size="small"
                >
                  {[0,1,2,3,4].map((lvl) => (
                    <ToggleButton key={lvl} value={lvl} aria-label={`₩${"₩".repeat(lvl)}`}>
                      ₩{"₩".repeat(lvl)}
                    </ToggleButton>
                  ))}
                </ToggleButtonGroup>
              </Box>

              {loadingFoods ? (
                <Box sx={{ py: 6, textAlign: "center" }}>
                  <CircularProgress size={24} />
                  <Typography variant="caption" sx={{ display: "block", mt: 1 }}>주변 맛집 불러오는 중…</Typography>
                </Box>
              ) : nearbyFoods.length === 0 ? (
                <Typography variant="body2" color="text.secondary">조건에 맞는 음식점을 찾지 못했습니다.</Typography>
              ) : (
                nearbyFoods.map((r) => (
                  <Box key={r.place_id} sx={{ mb: 1.5, p: 1.25, border: "1px solid #eee", borderRadius: 1.5 }}>
                    <Typography variant="subtitle2" sx={{ fontWeight: 700, ...noWrapSx }}>{r.name}</Typography>
                    {typeof r.rating === "number" && (
                      <Box sx={{ display: "flex", alignItems: "center", gap: .5 }}>
                        <Rating size="small" value={Number(r.rating)} precision={0.1} readOnly />
                        <Typography variant="caption" sx={noWrapSx}>
                          {r.rating} ({r.user_ratings_total?.toLocaleString?.() || 0})
                        </Typography>
                      </Box>
                    )}
                    <Typography variant="caption" sx={{ color: "text.secondary", ...noWrapSx }}>
                      {r.vicinity}
                    </Typography>
                    {typeof r._distM === "number" && isFinite(r._distM) && (
                      <Typography variant="caption" sx={{ display: "block", mt: .25, color: "text.secondary" }}>
                        약 {(r._distM/1000).toFixed(2)} km
                      </Typography>
                    )}
                  </Box>
                ))
              )}
            </Box>
          )}
        </Box>
      </LeftPlacePanel>
    );
  };

  // ────────────────────────────────────────────────────────────────────────────
  // 검색창 (Places Autocomplete)
  const SearchBox = () => (
    <StandaloneSearchBox
      onLoad={(ref) => (searchBoxRef.current = ref)}
      onPlacesChanged={() => {
        const [p] = searchBoxRef.current.getPlaces();
        if (!p) return;
        openPanel({
          name: p.name,
          placeId: p.place_id,
          position: p.geometry?.location ? toLatLng(p.geometry.location) : undefined,
        });
      }}
    >
      <TextField
        fullWidth
        placeholder="장소 검색 (예: 감천문화마을)"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        InputProps={{ startAdornment: <SearchIcon sx={{ color: "text.secondary", mr: 1 }} /> }}
        size="small"
      />
    </StandaloneSearchBox>
  );

  // ────────────────────────────────────────────────────────────────────────────
  return (
    <Box sx={{ bgcolor: "#f8f9fa", minHeight: "100vh" }}>
      {/* 전역: 한글 단어 나눔 방지 */}
      <GlobalStyles styles={{
        "*, *::before, *::after": { wordBreak: "keep-all" }
      }} />

      {/* Header */}
      <AppBar position="static" sx={{ bgcolor: "white", color: "black", boxShadow: 1 }}>
        <Toolbar sx={{ px: { xs: 2, md: 3, xl: 6 } }}>
          <Box sx={{ display: "flex", alignItems: "center", flexGrow: 1, minWidth: 0 }}>
            <Avatar sx={{ bgcolor: "#FF6B6B", mr: 1.5, width: 34, height: 34 }}>
              <LocationOnIcon fontSize="small" />
            </Avatar>
            <Typography variant="h6" component="div" sx={{ fontWeight: 700, ...noWrapSx }}>
              TripMaker
            </Typography>
          </Box>
          <Stack direction="row" spacing={1}>
            <Button variant="outlined" startIcon={<ShareIcon />} size="small" sx={noWrapSx}>공유</Button>
            <Button variant="contained" startIcon={<SaveIcon />} sx={{ bgcolor: "#FF6B6B", ...noWrapSx }} size="small">저장</Button>
          </Stack>
        </Toolbar>
      </AppBar>

      {/* Main: 패널(왼쪽) + 지도(가운데) + 일정(오른쪽) */}
      <Box
        sx={{
          display: "flex",
          flexDirection: { xs: "column", lg: "row" },
          gap: 3,
          px: { xs: 2, md: 3, xl: 6 },
          py: 3,
          width: "100%",
          maxWidth: "100%",
          mx: "auto",
        }}
      >
        {/* 왼쪽: 장소 패널 (선택 시 표시) */}
        {selectedPlace && (
          <Box sx={{ flex: "0 0 auto" }}>
            <Panel />
          </Box>
        )}

        {/* 가운데: 지도 */}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <StyledPaper sx={{ mb: 3 }}>
            <Box sx={{ mb: 2, display: "grid", gridTemplateColumns: "1fr auto auto", gap: 8, alignItems: "center" }}>
              <Box>
                <Typography variant="h5" sx={{ fontWeight: 800, mb: 1, ...noWrapSx }}>
                  부산 여행 지도
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={{ ...noWrapSx }}>
                  마커/일정 클릭 → 왼쪽 패널에서 상세보기
                </Typography>
              </Box>
              <Tooltip title="현재 Day 경로 그리기">
                <Button
                  variant={showRoute ? "contained" : "outlined"}
                  size="small"
                  startIcon={<RouteIcon />}
                  onClick={() => (showRoute ? (setShowRoute(false), setRoute(null)) : buildRouteFromActiveDay())}
                >
                  동선 보기
                </Button>
              </Tooltip>
              <Tooltip title="활성 Day 마커로 화면 맞춤">
                <Button
                  variant="outlined"
                  size="small"
                  startIcon={<LayersIcon />}
                  onClick={() => fitToMarkers(activeDayMarkers)}
                >
                  맞춤
                </Button>
              </Tooltip>
            </Box>

            {/* 검색창 */}
            <Box sx={{ mb: 2 }}>
              {isLoaded ? <SearchBox /> : (
                <TextField fullWidth size="small" placeholder="장소 검색 준비 중…" disabled />
              )}
            </Box>

            <Chip label={`${itineraryData.length}일 ${itineraryData.length - 1}박`} size="small"
                  sx={{ bgcolor: "#e3f2fd", color: "#1976d2", mb: 2, ...noWrapSx }} />

            <MapShell>
              {loadError && (
                <Box sx={{ p: 2, color: "error.main" }}>지도를 불러오는 중 오류가 발생했습니다. API 키/권한을 확인하세요.</Box>
              )}
              {!isLoaded && !loadError && (
                <Box sx={{ p: 2 }}>지도를 불러오는 중…</Box>
              )}
              {isLoaded && (
                <GoogleMap
                  center={(selectedPlace?.position) || mapCenter}
                  zoom={selectedPlace ? 14 : 12}
                  mapContainerStyle={{ width: "100%", height: "100%" }}
                  options={mapOptions}
                  onLoad={(map) => { mapRef.current = map; ensurePlacesService(); }}
                >
                  {/* 마커 클러스터링 */}
                  <MarkerClustererF>
                    {(clusterer) => (
                      <>
                        {activeDayMarkers.map((m) => (
                          <Marker
                            key={m.key}
                            position={m.position}
                            label={`${m.order}`}
                            title={m.title}
                            clusterer={clusterer}
                            onClick={() => openPanel({ name: m.title, placeId: m.placeId, position: m.position })}
                          />
                        ))}
                        {quickSpotMarkers.map((m) => (
                          <Marker
                            key={m.key}
                            position={m.position}
                            title={m.title}
                            clusterer={clusterer}
                            onClick={() => openPanel({ name: m.title, placeId: m.placeId, position: m.position })}
                          />
                        ))}
                      </>
                    )}
                  </MarkerClustererF>

                  {/* Day 경로 */}
                  {showRoute && route && (
                    <DirectionsRenderer
                      directions={route}
                      options={{ suppressMarkers: true, preserveViewport: true }}
                    />
                  )}
                </GoogleMap>
              )}
            </MapShell>
          </StyledPaper>

          {/* 지도 아래 부가 섹션 (선택) */}
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper sx={{ cursor: "pointer", transition: "all .2s", "&:hover": { transform: "translateY(-2px)", boxShadow: 4 }, p: 3, textAlign: "center" }}>
                <FlightTakeoffIcon sx={{ fontSize: 44, mb: 1.5, color: "#666" }} />
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5, ...noWrapSx }}>갈 곳을</Typography>
                <Typography variant="body2" color="text.secondary" sx={noWrapSx}>직접 검색 입력</Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper sx={{ cursor: "pointer", transition: "all .2s", "&:hover": { transform: "translateY(-2px)", boxShadow: 4 }, p: 3, textAlign: "center" }}>
                <RestaurantIcon sx={{ fontSize: 44, mb: 1.5, color: "#666" }} />
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5, ...noWrapSx }}>음식스팟</Typography>
                <Typography variant="body2" color="text.secondary" sx={noWrapSx}>인기 많은 장소</Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>

        {/* 오른쪽: 여행 일정표(더 크게) */}
        <Paper
          sx={{
            width: { xs: "100%", lg: 440 },
            borderRadius: 2,
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
            maxHeight: "calc(100vh - 120px)",
            display: "flex",
            flexDirection: "column",
            flex: "0 0 auto",
          }}
        >
          <Box sx={{ p: 3, borderBottom: "1px solid #e0e0e0" }}>
            <Typography variant="h6" sx={{ fontWeight: 800, mb: 2, ...noWrapSx }}>부산 여행 일정</Typography>
            <TextField
              fullWidth
              placeholder="검색어 입력하세요"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{ startAdornment: <SearchIcon sx={{ color: "text.secondary", mr: 1 }} /> }}
              sx={{ mb: 3 }}
              size="medium"
            />
            <Grid container spacing={1.5}>
              {touristSpots.map((spot, idx) => (
                <Grid item xs={6} key={idx}>
                  <Paper
                    onClick={() => handleAddPlace(spot)}
                    sx={{
                      cursor: "pointer",
                      bgcolor: spot.color, color: "white",
                      transition: "all .2s",
                      "&:hover": { transform: "translateY(-1px)" },
                      p: 1.8, borderRadius: 2
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", mb: 0.8 }}>
                      {spot.icon}
                      <Box sx={{ ml: 1, flex: 1, minWidth: 0 }}>
                        <Typography variant="body2" sx={{ fontWeight: 700, ...noWrapSx }}>{spot.name}</Typography>
                        <Typography variant="caption" sx={{ opacity: 0.9, ...noWrapSx }}>{spot.location}</Typography>
                      </Box>
                      <Chip label="추가" size="small" sx={{ bgcolor: "rgba(255,255,255,0.2)", color: "white", height: 22, fontSize: ".7rem" }} />
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Box>

          <Box sx={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <Box sx={{ p: 3, pb: 1 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1, ...noWrapSx }}>여행 일정표</Typography>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: "block", ...noWrapSx }}>
                목록에서 장소를 누르면 왼쪽 패널에 상세가 열립니다.
              </Typography>
            </Box>

            <Box sx={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
              <DayTabContainer sx={{ px: 2 }}>
                {itineraryData.map((day, index) => (
                  <Box key={index}>
                    <CompactDayButton active={activeDay === index} onClick={() => handleDaySelect(index)}>
                      <Box sx={{ display: "flex", alignItems: "center", flex: 1, minWidth: 0 }}>
                        <Avatar
                          sx={{
                            width: 28, height: 28, fontSize: 13, mr: 1.5,
                            bgcolor: activeDay === index ? "white" : "#2196f3",
                            color: activeDay === index ? "#2196f3" : "white",
                          }}
                        >
                          {index + 1}
                        </Avatar>
                        <Box sx={{ minWidth: 0 }}>
                          <Typography variant="body1" sx={{ fontWeight: 700, ...noWrapSx }}>{day.dayName}</Typography>
                          <Typography variant="caption" sx={{ opacity: 0.75, ...noWrapSx }}>{day.date}</Typography>
                        </Box>
                      </Box>
                      <Box sx={{ display: "flex", alignItems: "center" }}>
                        <Badge badgeContent={day.places.length} color="primary" sx={{ mr: 1 }} />
                        <IconButton size="small" onClick={(e) => toggleDayExpansion(index, e)} sx={{ color: "inherit" }}>
                          {expandedDays.has(index) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                      </Box>
                    </CompactDayButton>

                    <Collapse in={expandedDays.has(index)}>
                      <Box sx={{ ml: 3, mb: 1 }}>
                        {day.places.map((place, placeIndex) => (
                          <Box
                            key={place.id}
                            onClick={() => onClickItineraryPlace(place)}
                            sx={{
                              display: "flex", alignItems: "center", py: 0.9, px: 1.2, cursor: "pointer",
                              bgcolor: activeDay === index ? "rgba(33, 150, 243, 0.06)" : "transparent",
                              borderRadius: 1.2, mb: 0.6, "&:hover": { bgcolor: "rgba(33,150,243,.09)" }
                            }}
                          >
                            <Avatar sx={{ width: 20, height: 20, fontSize: 11, bgcolor: "#2196f3", mr: 1.1 }}>{placeIndex + 1}</Avatar>
                            <Box sx={{ flex: 1, minWidth: 0 }}>
                              <Typography variant="body2" sx={{ fontWeight: 600, ...noWrapSx }}>{place.name}</Typography>
                              <Typography variant="caption" color="text.secondary" sx={{ display: "block", ...noWrapSx }}>{place.time}</Typography>
                            </Box>
                          </Box>
                        ))}
                      </Box>
                    </Collapse>
                  </Box>
                ))}
              </DayTabContainer>

              <Box sx={{ p: 2.2 }}>
                <Button
                  fullWidth
                  variant="outlined"
                  startIcon={<AddIcon />}
                  sx={{
                    height: 44,
                    borderStyle: "dashed",
                    borderColor: "#ddd",
                    color: "#666",
                    ...noWrapSx,
                    "&:hover": { borderColor: "#2196f3", color: "#2196f3", bgcolor: "rgba(33,150,243,.05)" }
                  }}
                >
                  일정 추가
                </Button>
              </Box>
            </Box>
          </Box>
        </Paper>
      </Box>
    </Box>
  );
}
