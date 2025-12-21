// src/pages/TravelPlanSamplePage.jsx
import React, { useMemo, useState, useCallback, useRef, useEffect } from "react";
import {
  Typography, Button, Box, Paper, Stack, Avatar,
  TextField, Chip, Grid, IconButton, Badge, Collapse, Tabs, Tab,
  Rating, Divider, CircularProgress, GlobalStyles, FormControlLabel, Switch,
  ToggleButton, ToggleButtonGroup, Tooltip, Dialog, DialogTitle, DialogContent,
  DialogActions, Snackbar, Alert
} from "@mui/material";
import {
  Add as AddIcon, Share as ShareIcon, Save as SaveIcon,
  FlightTakeoff as FlightTakeoffIcon, LocationOn as LocationOnIcon,
  Restaurant as RestaurantIcon, BeachAccess as BeachAccessIcon, Museum as MuseumIcon,
  ShoppingCart as ShoppingCartIcon, ExpandMore as ExpandMoreIcon, ExpandLess as ExpandLessIcon,
  Search as SearchIcon, Close as CloseIcon, Directions as DirectionsIcon, Star as StarIcon,
  Route as RouteIcon, Layers as LayersIcon, FolderOpen as FolderOpenIcon,
  DeleteOutline as DeleteOutlineIcon, Favorite as FavoriteIcon
} from "@mui/icons-material";
import { styled } from "@mui/material/styles";
import {
  GoogleMap, Marker, useLoadScript, StandaloneSearchBox,
  DirectionsRenderer, MarkerClustererF
} from "@react-google-maps/api";
import { useLocation, useNavigate } from "react-router-dom";
import axios from "axios";
import { listPlans, savePlan, getPlan, deletePlan } from "../utils/planStorage";

// ──────────────────────────────────────────────────────────────────────────────
// 공통 no-wrap 스타일
const noWrapSx = { whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" };

// 스타일
const StyledPaper = styled(Paper)(({ theme }) => ({
  padding: theme.spacing(3),
  borderRadius: theme.spacing(2),
  boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
}));

// ★ 고정 vh 제거 → 반응형 높이로 교체
const MapShell = styled(Box)(({ theme }) => ({
  height: "clamp(420px, 62dvh, 72dvh)", // 화면에 맞게 유연하게
  borderRadius: theme.spacing(1.5),
  overflow: "hidden",
  position: "relative",
  display: "flex",
  flexDirection: "column",
}));

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
  // 작은 화면에서 가로 꽉 차게
  [theme.breakpoints.down("md")]: {
    width: "100%",
    maxWidth: "100%",
  },
}));

const PanelHeaderImage = styled("div")({
  width: "100%",
  height: 220,
  backgroundSize: "cover",
  backgroundPosition: "center",
  backgroundColor: "#f1f1f1",
});

const DayTabContainer = styled(Box)(({ theme }) => ({
  maxHeight: 360,
  overflowY: "auto",
  overflowX: "hidden",
  "&::-webkit-scrollbar": { width: "6px" },
  "&::-webkit-scrollbar-track": { background: "#f6f6f6", borderRadius: "4px" },
  "&::-webkit-scrollbar-thumb": { background: "#c1c1c1", borderRadius: "4px" },
  "&::-webkit-scrollbar-thumb:hover": { background: "#a8a8a8" },
}));

// Day 버튼
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
const BUSAN_CENTER = { lat: 35.1796, lng: 129.0756 };
const SPOT_COORDS = {
  "해운대 해수욕장": { lat: 35.1587, lng: 129.1604 },
  "광안리 해변": { lat: 35.1532, lng: 129.1186 },
  "감천문화마을": { lat: 35.0975, lng: 129.0106 },
  "자갈치 시장": { lat: 35.0979, lng: 129.0303 },
  "국제시장": { lat: 35.1009, lng: 129.026 },
  "태종대": { lat: 35.0586, lng: 129.086 },
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

const BACKEND_IDS = {
  "태종대": "681891fa77e67d6ebadae372",
};

// ──────────────────────────────────────────────────────────────────────────────
const toLatLng = (g) => ({ lat: g.lat(), lng: g.lng() });
const haversine = (a, b) => {
  const R = 6371e3;
  const φ1 = (a.lat * Math.PI) / 180, φ2 = (b.lat * Math.PI) / 180;
  const Δφ = ((b.lat - a.lat) * Math.PI) / 180;
  const Δλ = ((b.lng - a.lng) * Math.PI) / 180;
  const s = Math.sin(Δφ / 2) ** 2 + Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(s));
};

// ──────────────────────────────────────────────────────────────────────────────
// 백엔드 연동
const API_PREFIX =
  process.env.REACT_APP_API_PREFIX ||
  (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_API_PREFIX) ||
  "http://localhost:8000";
const API_BASE = `${API_PREFIX.replace(/\/$/, "")}/api/v1`;

async function generateItinerary(requestData) {
  try {
    const res = await fetch(`${API_BASE}/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestData),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("여행 일정을 생성하는 중 오류 발생:", err);
    throw err;
  }
}

async function safeFetchJson(url) {
  try {
    const r = await fetch(url, { mode: "cors", credentials: "include" });
    if (!r.ok) return null;
    return await r.json();
  } catch {
    return null;
  }
}
async function getNearbyCafesBE(placeId, maxDistance = 2.0) {
  return (await safeFetchJson(`${API_BASE}/nearby/cafes/${placeId}?max_distance=${maxDistance}`)) || [];
}
async function getNearbyRestaurantsBE(placeId, maxDistance = 1.5) {
  return (await safeFetchJson(`${API_BASE}/nearby/restaurants/${placeId}?max_distance=${maxDistance}`)) || [];
}
async function getNearbyPlacesBE(placeId, maxDistance = 5.0, includeCrowding = false) {
  const url = `${API_BASE}/nearby/${placeId}?max_distance=${maxDistance}` +
              (includeCrowding ? `&include_crowding=true` : "");
  return (await safeFetchJson(url)) || [];
}
async function getCrowding(placeId) {
  return await safeFetchJson(`${API_BASE}/place/crowding/${placeId}`);
}

function normalizeBackendPlaces(rows = [], center) {
  const out = [];
  for (const r of rows) {
    const coords = r?.location?.coordinates; // [lng, lat]
    if (!coords || coords.length < 2) continue;
    const pos = { lat: coords[1], lng: coords[0] };
    const distM = haversine(center, pos);
    out.push({
      place_id: r._id,
      name: r.name,
      rating: r.rating ?? null,
      user_ratings_total: r.review_count ?? null,
      vicinity: r.address ?? r.region ?? "",
      geometry: { location: { lat: () => pos.lat, lng: () => pos.lng } },
      _distM: distM,
    });
  }
  out.sort((a, b) => a._distM - b._distM);
  return out;
}
function normalizeGooglePlaces(rows = [], center) {
  const out = [];
  for (const r of rows) {
    const gloc = r?.geometry?.location;
    if (!gloc) continue;
    const pos = toLatLng(gloc);
    const distM = haversine(center, pos);
    out.push({
      place_id: r.place_id,
      name: r.name,
      rating: r.rating ?? null,
      user_ratings_total: r.user_ratings_total ?? null,
      vicinity: r.vicinity || r.formatted_address || "",
      geometry: { location: { lat: () => pos.lat, lng: () => pos.lng } },
      _distM: distM,
    });
  }
  out.sort((a, b) => a._distM - b._distM);
  return out;
}
function normalizeNearbySights(rows = [], center) {
  return normalizeBackendPlaces(rows, center).map(r => ({ ...r, isSight: true }));
}
async function getNearbySightsGoogle(placesService, centerLatLng, radiusKm = 5.0) {
  if (!placesService || !centerLatLng) return [];
  const request = {
    location: centerLatLng,
    radius: Math.max(500, Math.floor(radiusKm * 1000)),
    type: "tourist_attraction",
    language: "ko",
  };
  return await new Promise((resolve) => {
    placesService.nearbySearch(request, (results) => resolve(results || []));
  });
}

// 코스 API
export const saveCourse = async (payload) => {
  const { data } = await axios.post(`${API_BASE}/save`, payload);
  return data;
};
export const listUserCourses = async (userId) => {
  const { data } = await axios.get(`${API_BASE}/user/${userId}`);
  return data;
};
export const getCourse = async (courseId) => {
  const { data } = await axios.get(`${API_BASE}/course/${courseId}`);
  return data;
};
export const getCourseAlt = async (courseId) => {
  const { data } = await axios.get(`${API_BASE}/courses/${courseId}`);
  return data;
};
export const addPlaceToCourse = async ({ course_id, day, place }) => {
  const { data } = await axios.post(`${API_BASE}/courses/add-place`, { course_id, day, place });
  return data;
};
export const updatePlaceInCourse = async ({ course_id, day, place_id, updates }) => {
  const { data } = await axios.put(`${API_BASE}/courses/update-place`, { course_id, day, place_id, updates });
  return data;
};
export const removePlaceFromCourse = async ({ course_id, day, place_id }) => {
  const { data } = await axios.delete(`${API_BASE}/courses/remove-place`, { data: { course_id, day, place_id } });
  return data;
};

// ──────────────────────────────────────────────────────────────────────────────
export default function TravelPlanSamplePage() {
  const location = useLocation();
  const navigate = useNavigate();

  // 상태
  const [activeDay, setActiveDay] = useState(0);
  const [expandedDays, setExpandedDays] = useState(new Set([0]));
  const [panelTab, setPanelTab] = useState(0);
  const [searchTerm, setSearchTerm] = useState("");

  // 일정 데이터 (샘플 초기값)
  const [itineraryData, setItineraryData] = useState([
    { date: "2026. 8. 21.", dayName: "Day 1", places: [
      { id: "1", name: "감천문화마을", placeId: null, time: "14:00", icon: <MuseumIcon/> },
      { id: "2", name: "해운대 해수욕장", placeId: null, time: "16:00", icon: <BeachAccessIcon/> },
    ]},
    { date: "2026. 8. 22.", dayName: "Day 2", places: [
      { id: "3", name: "광안리 해변", placeId: null, time: "10:00", icon: <BeachAccessIcon/> },
      { id: "4", name: "자갈치 시장", placeId: null, time: "14:00", icon: <RestaurantIcon/> },
      { id: "5", name: "국제시장", placeId: null, time: "16:00", icon: <ShoppingCartIcon/> },
    ]},
  ]);

  // 주변 관광지/혼잡도
  const [nearbySights, setNearbySights] = useState([]);
  const [loadingSights, setLoadingSights] = useState(false);
  const [crowding, setCrowding] = useState(null);

  // 선택 장소/주변 음식점
  const [selectedPlace, setSelectedPlace] = useState(null);
  const [nearbyFoods, setNearbyFoods] = useState([]);
  const [loadingFoods, setLoadingFoods] = useState(false);
  const [foodSource, setFoodSource] = useState("google");
  const loadSeqRef = useRef(0);

  // 무한 스크롤
  const [displayCount, setDisplayCount] = useState(5);
  const sentinelRef = useRef(null);
  useEffect(() => { setDisplayCount(5); }, [nearbyFoods, panelTab, selectedPlace?.backendId, foodSource]);
  useEffect(() => {
    if (panelTab !== 1) return;
    const el = sentinelRef.current;
    if (!el) return;
    const io = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting) setDisplayCount((c) => Math.min(c + 5, nearbyFoods.length));
    }, { root: null, rootMargin: "120px", threshold: 0 });
    io.observe(el);
    return () => io.disconnect();
  }, [panelTab, nearbyFoods.length]);

  // 필터
  const [openNowOnly, setOpenNowOnly] = useState(false);
  const [priceLevels, setPriceLevels] = useState([0,1,2,3,4]);

  // 경로
  const [route, setRoute] = useState(null);
  const [showRoute, setShowRoute] = useState(false);

  // Google
  const mapRef = useRef(null);
  const placesServiceRef = useRef(null);
  const searchBoxRef = useRef(null);

  // 캐시
  const detailCacheRef = useRef(new Map());
  const idCacheRef = useRef(new Map());
  const inFlightRef = useRef(new Set());

  // 동적 좌표/ID 저장
  const [dynamicBackendIds, setDynamicBackendIds] = useState({});
  const spotCoordsRef = useRef({ ...SPOT_COORDS });

  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY || "",
    libraries: ["places"],
    language: "ko",
    region: "KR",
  });

  // planId로 불러오기
  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const planId = params.get("planId");
    if (planId) {
      const plan = getPlan(planId);
      if (plan?.days) {
        setItineraryData(plan.days);
        setActiveDay(0);
        setExpandedDays(new Set([0]));
        setShowRoute(false);
        setRoute(null);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // 저장/불러오기
  const [openLoadDlg, setOpenLoadDlg] = useState(false);
  const [plans, setPlans] = useState([]);
  const [snack, setSnack] = useState({ open: false, msg: "" });
  const refreshPlans = () => setPlans(listPlans());
  useEffect(() => { refreshPlans(); }, []);
  const handleSavePlan = () => {
    const title = window.prompt("코스 이름을 입력하세요 (예: 부산 5박6일 핵심)");
    if (!title) return;
    const cover = selectedPlace?.photoUrl || null;
    savePlan({ title, days: itineraryData, cover });
    refreshPlans();
    setSnack({ open: true, msg: "코스가 저장되었습니다." });
  };
  const handleLoadPlan = (planId) => {
    const plan = getPlan(planId);
    if (!plan) return;
    setItineraryData(plan.days);
    setActiveDay(0);
    setExpandedDays(new Set([0]));
    setShowRoute(false);
    setRoute(null);
    setOpenLoadDlg(false);
  };
  const handleDeletePlan = (planId) => {
    if (!window.confirm("이 코스를 삭제할까요?")) return;
    deletePlan(planId);
    refreshPlans();
  };

  // (샘플) 빠른 스팟 카드
  const touristSpots = useMemo(() => ([
    { name: "해운대 해수욕장", location: "부산광역시 해운대구", icon: <BeachAccessIcon/>, color: "#FF6B6B" },
    { name: "광안리 해변", location: "부산 해수욕장 중 하나", icon: <BeachAccessIcon/>, color: "#FF6B6B" },
    { name: "감천문화마을", location: "한국의 마추픽추", icon: <MuseumIcon/>, color: "#FF6B6B" },
    { name: "자갈치 시장", location: "신선한 수산물", icon: <RestaurantIcon/>, color: "#FF6B6B" },
  ]), []);

  const handleDaySelect = (i) => {
    setActiveDay(i);
    setExpandedDays((prev) => new Set([...prev, i]));
    setShowRoute(false);
    setRoute(null);
  };

  // Places 서비스
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
        (detail) => {
          inFlightRef.current.delete(key);
          if (detail) detailCacheRef.current.set(placeId, detail);
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
      const request = { query: name, location: position || mapCenter, radius: 3000, language: "ko" };
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
        location: centerLatLng, radius: 900, type: "restaurant", language: "ko",
        openNow: openNowOnly || undefined,
        minPriceLevel: Math.min(...priceLevels),
        maxPriceLevel: Math.max(...priceLevels),
      };
      svc.nearbySearch(request, (results) => resolve((results || []).slice(0, 20)));
    });

  // ▼ 추천에서 넘어온 관광지(spots)를 일정에 반영
  async function enrichSpotsWithDetails(spots, center) {
    const out = [];
    for (const s of spots) {
      let pos = spotCoordsRef.current[s.name];
      let placeId = null;
      let detail = null;

      if (!pos) {
        detail = await textSearchToDetails(s.name, center);
        if (detail?.geometry?.location) {
          const g = detail.geometry.location;
          pos = { lat: g.lat(), lng: g.lng() };
        }
        if (detail?.place_id) placeId = detail.place_id;
      }

      if (pos) spotCoordsRef.current[s.name] = pos;

      out.push({
        id: s.id ?? `spot-${s.name}`,
        name: s.name,
        time: "",
        placeId: placeId || null,
        backendId: s.backendId || s.id || null, // ✅ 오타 수정 (ackendId → backendId)
        address: s.address || detail?.formatted_address || "",
        rating: typeof s.rating === "number" ? s.rating : (detail?.rating ?? null),
      });
    }
    return out;
  }

  // 하루 최대 6개로 분배
  function distributeIntoDays(items, days) {
    if (!days || days < 1) days = 1;
    const MAX_PER_DAY = 6;
    const arr = [];
    let idx = 0;
    for (let d = 0; d < days; d++) {
      const slice = items.slice(idx, idx + MAX_PER_DAY);
      arr.push(slice);
      idx += MAX_PER_DAY;
    }
    while (idx < items.length) {
      arr.push(items.slice(idx, idx + MAX_PER_DAY));
      days += 1;
      idx += MAX_PER_DAY;
    }
    return arr;
  }
  function timeForIndex(i) {
    const base = 10 * 60;
    const mins = base + i * 120;
    const hh = String(Math.floor(mins / 60)).padStart(2, "0");
    const mm = String(mins % 60).padStart(2, "0");
    return `${hh}:${mm}`;
  }

  // ★ 동적 좌표 참조(백엔드 우선)
  const activeDayMarkers = useMemo(() => {
    const list = itineraryData[activeDay]?.places || [];
    return list
      .map((p, idx) => {
        const pos = spotCoordsRef.current[p.name];
        return {
          key: `day-${p.id}`,
          title: p.name,
          order: idx + 1,
          position: pos,
          placeId: p.placeId,
          backendId: p.backendId || null,
        };
      })
      .filter((m) => !!m.position);
  }, [activeDay, itineraryData]);

  const quickSpotMarkers = useMemo(() => {
    const spots = [ "해운대 해수욕장", "광안리 해변", "감천문화마을", "자갈치 시장" ];
    return spots
      .map((name, idx) => ({
        key: `quick-${idx}`,
        title: name,
        order: idx + 1,
        position: spotCoordsRef.current[name],
        placeId: null
      }))
      .filter((m) => !!m.position);
  }, []);

  // 지도 옵션/중심/맞춤
  const mapOptions = useMemo(() => ({
    disableDefaultUI: false, zoomControl: true, mapTypeControl: false,
    fullscreenControl: false, streetViewControl: false,
  }), []);
  const mapCenter = useMemo(() => activeDayMarkers[0]?.position || BUSAN_CENTER, [activeDayMarkers]);
  const fitToMarkers = useCallback((markers) => {
    if (!mapRef.current || !window.google || markers.length === 0) return;
    const bounds = new window.google.maps.LatLngBounds();
    markers.forEach((m) => bounds.extend(m.position));
    mapRef.current.fitBounds(bounds, 80);
  }, []);
  useEffect(() => { if (isLoaded) fitToMarkers(activeDayMarkers); }, [activeDay, isLoaded, fitToMarkers, activeDayMarkers]);

  // 경로
  const buildRouteFromActiveDay = async () => {
    const list = itineraryData[activeDay]?.places || [];
    const coords = list.map((p) => spotCoordsRef.current[p.name]).filter(Boolean);
    if (coords.length < 2) { setRoute(null); setShowRoute(false); return; }
    const ds = new window.google.maps.DirectionsService();
    const origin = coords[0];
    const destination = coords[coords.length - 1];
    const wp = coords.slice(1, -1).map((c) => ({ location: c, stopover: true }));
    ds.route(
      { origin, destination, waypoints: wp, travelMode: window.google.maps.TravelMode.DRIVING, optimizeWaypoints: false, region: "KR" },
      (res) => {
        if (res) {
          setRoute(res);
          const bounds = new window.google.maps.LatLngBounds();
          res.routes[0].overview_path.forEach((p) => bounds.extend(p));
          mapRef.current?.fitBounds(bounds, 80);
          setShowRoute(true);
        } else {
          setRoute(null); setShowRoute(false);
        }
      }
    );
  };

  // 패널 열기 + 혼잡도/주변관광
  const openPanel = async ({ name, placeId, position, backendId: passedBackendId }) => {
    const backendId = passedBackendId || BACKEND_IDS[name] || dynamicBackendIds[name] || null;

    setPanelTab(0);
    setSelectedPlace({
      name,
      position: position || spotCoordsRef.current[name] || mapCenter,
      loading: true,
      placeId,
      backendId,
    });

    if (mapRef.current?.panTo) mapRef.current.panTo(position || spotCoordsRef.current[name] || mapCenter);

    const detail = placeId
      ? await getDetailsByPlaceId(placeId)
      : await textSearchToDetails(name, position || mapCenter);

    const pos = detail?.geometry?.location
      ? toLatLng(detail.geometry.location)
      : (position || spotCoordsRef.current[name] || mapCenter);

    const photoUrl = detail?.photos?.[0]?.getUrl({ maxWidth: 1200, maxHeight: 900 });

    const final = {
      name: detail?.name || name,
      position: pos,
      details: detail || null,
      photoUrl,
      placeId: detail?.place_id || placeId || idCacheRef.current.get(name) || null,
      backendId,
    };
    setSelectedPlace(final);

    if (backendId) getCrowding(backendId).then(setCrowding);
    else setCrowding(null);

    // 주변 관광지: 백엔드 → 구글 폴백
    setLoadingSights(true);
    const svc = ensurePlacesService();
    if (backendId) {
      getNearbyPlacesBE(backendId, 5.0, true)
        .then((rows) => {
          const norm = normalizeNearbySights(rows || [], final.position);
          if (norm.length > 0) {
            setNearbySights(norm);
            return null;
          }
          return getNearbySightsGoogle(svc, new window.google.maps.LatLng(final.position.lat, final.position.lng), 5.0)
            .then((gRows) => setNearbySights(normalizeGooglePlaces(gRows, final.position)));
        })
        .finally(() => setLoadingSights(false));
    } else {
      getNearbySightsGoogle(svc, new window.google.maps.LatLng(final.position.lat, final.position.lng), 5.0)
        .then((gRows) => setNearbySights(normalizeGooglePlaces(gRows, final.position)))
        .finally(() => setLoadingSights(false));
    }
  };

  // 음식점 로딩: 백엔드 우선 → 구글 폴백
  useEffect(() => {
    if (!selectedPlace?.position) return;
    let cancelled = false;
    const seq = ++loadSeqRef.current;

    const loadFoods = async () => {
      setLoadingFoods(true);

      if (selectedPlace.backendId) {
        const [cafes, restos] = await Promise.all([
          getNearbyCafesBE(selectedPlace.backendId, 2.0),
          getNearbyRestaurantsBE(selectedPlace.backendId, 1.5),
        ]);
        const merged = [...cafes, ...restos];
        if (!cancelled && loadSeqRef.current === seq && merged.length > 0) {
          const norm = normalizeBackendPlaces(merged, selectedPlace.position);
          setNearbyFoods(norm);
          setFoodSource("backend");
          setLoadingFoods(false);
          return;
        }
      }

      if (window.google?.maps?.places) {
        const foods = await fetchNearbyFoods(
          new window.google.maps.LatLng(selectedPlace.position.lat, selectedPlace.position.lng)
        );
        if (cancelled || loadSeqRef.current !== seq) return;
        const pos = selectedPlace.position;
        const withDist = foods.map((f) => ({
          ...f,
          _distM: f?.geometry?.location ? haversine(pos, toLatLng(f.geometry.location)) : Number.POSITIVE_INFINITY,
        }));
        withDist.sort((a, b) => a._distM - b._distM);
        setNearbyFoods(withDist);
        setFoodSource("google");
        setLoadingFoods(false);
      } else {
        if (!cancelled && loadSeqRef.current === seq) {
          setNearbyFoods([]);
          setFoodSource("google");
          setLoadingFoods(false);
        }
      }
    };

    loadFoods();
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedPlace, openNowOnly, priceLevels]);

  // 검색창
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

  // 설문에서 들어온 파라미터 기반 자동 일정 생성
  useEffect(() => {
    const navState = location.state;
    if (!navState) return;

    const {
      departureCity, otherCity, travelDuration, travelStartDate,
      startingPoint, surveyAttractions = [], preferences = {},
    } = navState || {};

    if (!travelDuration || !travelStartDate) return;

    const requestPayload = {
      departureCity, otherCity, travelDuration, travelStartDate, startingPoint, preferences,
      surveyAttractions: surveyAttractions.map(a => a.name),
    };

    (async () => {
      try {
        const data = await generateItinerary(requestPayload);
        if (!data?.dailySchedule?.length) return;

        const nextCoords = { ...spotCoordsRef.current };
        const nextBackendIds = { ...dynamicBackendIds };

        data.dailySchedule.forEach(day => {
          (day.places || []).forEach(p => {
            const coords = p?.location?.coordinates; // [lng, lat]
            if (Array.isArray(coords) && coords.length >= 2) {
              nextCoords[p.name] = { lat: coords[1], lng: coords[0] };
            }
            if (p?._id) nextBackendIds[p.name] = p._id;
          });
        });

        spotCoordsRef.current = nextCoords;
        setDynamicBackendIds(nextBackendIds);

        const toTime = (i) => {
          const base = 10 * 60;
          const mins = base + i * 120;
          const hh = String(Math.floor(mins / 60)).padStart(2, "0");
          const mm = String(mins % 60).padStart(2, "0");
          return `${hh}:${mm}`;
        };

        const nextItin = data.dailySchedule.map((day) => {
          const places = (day.places || []).map((place, idx) => ({
            id: place.id || place._id,
            name: place.name,
            placeId: null,
            time: toTime(idx),
            backendId: place._id || null,
            icon: <MuseumIcon />,
            description: place.description,
            duration: place.estimated_duration,
            locX: place.location?.coordinates?.[0],
            locY: place.location?.coordinates?.[1],
            address: place.address,
            rating: typeof place.rating === "number" ? place.rating : null,
          }));

          const d = new Date(day.date || travelStartDate);
          const dateStr = `${d.getFullYear()}. ${d.getMonth() + 1}. ${d.getDate()}.`;

          return { date: dateStr, dayName: `Day ${day.day}`, places };
        });

        setItineraryData(nextItin);
        setActiveDay(0);
        setExpandedDays(new Set([0]));
        setShowRoute(false);
        setRoute(null);
      } catch (err) {
        console.error("일정 생성 실패(샘플 페이지):", err);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state]);

  // 추천 페이지에서 넘어온 선택 관광지만으로 일정 구성
  useEffect(() => {
    const navState = location.state;
    const picked = navState?.spots;
    if (!picked || !Array.isArray(picked) || picked.length === 0) return;

    (async () => {
      try {
        const center = activeDayMarkers[0]?.position || BUSAN_CENTER;

        const enriched = await enrichSpotsWithDetails(picked, center);

        const days = Number(navState?.travelDuration) > 0 ? Number(navState.travelDuration) : 1;

        const buckets = distributeIntoDays(enriched, days);
        const baseDate = new Date(navState?.travelStartDate || Date.now());

        const nextItin = buckets.map((list, di) => {
          const date = new Date(baseDate);
          date.setDate(baseDate.getDate() + di);
          const dateStr = `${date.getFullYear()}. ${date.getMonth() + 1}. ${date.getDate()}.`;

          return {
            date: dateStr,
            dayName: `Day ${di + 1}`,
            places: list.map((p, i) => ({
              ...p,
              time: timeForIndex(i),
              icon: <MuseumIcon />,
            })),
          };
        });

        setItineraryData(nextItin);
        setActiveDay(0);
        setExpandedDays(new Set([0]));
        setShowRoute(false);
        setRoute(null);
      } catch (e) {
        console.error("선택 관광지로 일정 구성 실패:", e);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.state]);

  const handleSaveCourseToServer = async () => {
    try {
      const navState = location.state || {};
      const payload = { user_id: navState.userId || "demo-user", title: navState.title || "부산 여행", dailySchedule: itineraryData };
      const res = await saveCourse(payload);
      alert("서버 저장 성공! course_id: " + res.course_id);
    } catch (e) {
      console.error(e);
      alert("서버 저장 실패");
    }
  };

  const addPlaceToDay = async (dayIndex, place) => {
    const dayId = dayIndex + 1;
    setItineraryData((prev) =>
      prev.map((d, i) => (i === dayIndex ? { ...d, places: [...d.places, place] } : d))
    );
    try {
      const navState = location.state || {};
      if (navState.courseId) {
        await addPlaceToCourse({
          course_id: navState.courseId,
          day: dayId,
          place: {
            id: place.id,
            name: place.name,
            description: place.description,
            estimated_duration: place.duration,
            location: { type: "Point", coordinates: [place.locX, place.locY] },
            address: place.address,
            rating: place.rating,
          },
        });
      }
    } catch (e) {
      console.error(e);
      setItineraryData((prev) =>
        prev.map((d, i) =>
          i === dayIndex ? { ...d, places: d.places.filter((p) => p.id !== place.id) } : d
        )
      );
      alert("장소 추가에 실패했습니다.");
    }
  };

  const removePlaceFromDay = async (dayIndex, placeId) => {
    const prev = itineraryData;
    const dayId = dayIndex + 1;
    setItineraryData((curr) =>
      curr.map((d, i) =>
        i === dayIndex ? { ...d, places: d.places.filter((p) => p.id !== placeId) } : d
      )
    );
    try {
      const navState = location.state || {};
      if (navState.courseId) {
        await removePlaceFromCourse({ course_id: navState.courseId, day: dayId, place_id: placeId });
      }
    } catch (e) {
      console.error(e);
      setItineraryData(prev);
      alert("장소 제거에 실패했습니다.");
    }
  };

  const onReorderPlace = async (dayIndex, sourceIndex, destIndex) => {
    if (destIndex < 0) return;
    let movedItem = null;
    setItineraryData((prev) =>
      prev.map((d, i) => {
        if (i !== dayIndex) return d;
        const arr = Array.from(d.places);
        [movedItem] = arr.splice(sourceIndex, 1);
        arr.splice(destIndex, 0, movedItem);
        return { ...d, places: arr };
      })
    );
    try {
      const navState = location.state || {};
      if (navState.courseId && movedItem?.id != null) {
        await updatePlaceInCourse({
          course_id: navState.courseId,
          day: dayIndex + 1,
          place_id: movedItem.id,
          updates: { order: destIndex },
        });
      }
    } catch (e) { console.error(e); }
  };

  // ────────────────────────────────────────────────────────────────────────────
  return (
    <Box sx={{ bgcolor: "#f8f9fa", minHeight: "100dvh" }}>
      {/* Safari/모바일에서 100vh 깜빡임 방지 */}
      <GlobalStyles
        styles={{
          "html, body, #root": { minHeight: "100dvh" },
        }}
      />

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
        {/* 왼쪽 패널 (선택 시 표시) */}
        {selectedPlace && (
          <Box sx={{ flex: "0 0 auto" }}>
            <LeftPlacePanel
              sx={{
                maxHeight: "calc(100dvh - 120px)", // 화면에 맞춤
                overflowY: "auto",
              }}
            >
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

                    {typeof selectedPlace?.details?.rating === "number" ? (
                      <Box sx={{ display: "flex", alignItems: "center", gap: .5 }}>
                        <Rating size="small" value={Number(selectedPlace.details.rating)} precision={0.1} readOnly />
                        <Typography variant="caption" sx={noWrapSx}>
                          {selectedPlace.details.rating} ({selectedPlace.details.user_ratings_total?.toLocaleString()})
                        </Typography>
                      </Box>
                    ) : null}

                    <Typography variant="body2" sx={{ color: "text.secondary", mt: .5, ...noWrapSx }}>
                      {selectedPlace?.details?.formatted_address || "주소 정보 없음"}
                    </Typography>

                    {/* 혼잡도 표시 */}
                    {crowding && (
                      <Box sx={{ mt: 0.75, display: "flex", alignItems: "center", gap: .5, flexWrap: "wrap" }}>
                        <Chip size="small" color="warning" label={`혼잡도: ${crowding.level ?? "정보없음"}`} />
                        {crowding.updated_at && (
                          <Typography variant="caption" color="text.secondary">
                            업데이트: {new Date(crowding.updated_at).toLocaleString()}
                          </Typography>
                        )}
                      </Box>
                    )}
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
                  {selectedPlace?.details?.website && (
                    <Button variant="outlined" size="small" onClick={() => window.open(selectedPlace.details.website, "_blank")} sx={noWrapSx}>
                      공식 사이트
                    </Button>
                  )}
                  {selectedPlace?.details?.url && (
                    <Button variant="outlined" size="small" onClick={() => window.open(selectedPlace.details.url, "_blank")} sx={noWrapSx}>
                      Google 상세
                    </Button>
                  )}
                </Box>
              </Box>

              <Divider />

              {/* 탭 3개: 개요/음식점/주변관광 */}
              <Tabs value={panelTab} onChange={(_, v) => setPanelTab(v)} variant="fullWidth">
                <Tab label="개요" />
                <Tab label="음식점" />
                <Tab label="주변관광" />
              </Tabs>

              <Box sx={{ flex: 1 }}>
                {/* 개요 */}
                {panelTab === 0 && (
                  <Box sx={{ p: 2 }}>
                    <Typography variant="subtitle2" sx={{ mb: 1, ...noWrapSx }}>소개</Typography>
                    <Typography variant="body2" sx={{ color: "text.secondary" }}>
                      {selectedPlace?.details?.opening_hours?.weekday_text
                        ? `영업시간: ${selectedPlace.details.opening_hours.weekday_text.join(" / ")}`
                        : "영업정보가 제공되지 않았습니다."}
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      <Chip size="small" icon={<StarIcon fontSize="small" />} label="여행지" sx={{ mr: 1 }} />
                      {typeof selectedPlace?.details?.price_level === "number" && (
                        <Chip size="small" label={`가격대 ₩${"₩".repeat(selectedPlace.details.price_level)}`} />
                      )}
                    </Box>
                  </Box>
                )}

                {/* 음식점 */}
                {panelTab === 1 && (
                  <Box sx={{ p: 2 }}>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
                      <Chip
                        size="small"
                        variant="outlined"
                        label={foodSource === "backend" ? "출처: Backend" : "출처: Google"}
                        color={foodSource === "backend" ? "success" : "primary"}
                      />
                    </Box>

                    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1.5, flexWrap: "wrap" }}>
                      <FormControlLabel
                        control={<Switch size="small" checked={openNowOnly} onChange={(e) => setOpenNowOnly(e.target.checked)} />}
                        label="지금 영업중"
                      />
                      <ToggleButtonGroup value={priceLevels} onChange={(_, val) => val?.length && setPriceLevels(val)} aria-label="가격대" size="small">
                        {[0,1,2,3,4].map((lvl) => (
                          <ToggleButton key={lvl} value={lvl} aria-label={`₩${"₩".repeat(lvl)}`}>₩{"₩".repeat(lvl)}</ToggleButton>
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
                      <>
                        {nearbyFoods.slice(0, displayCount).map((r) => (
                          <Box key={r.place_id || r.placeId} sx={{ mb: 1.5, p: 1.25, border: "1px solid #eee", borderRadius: 1.5 }}>
                            <Typography variant="subtitle2" sx={{ fontWeight: 700, ...noWrapSx }}>{r.name}</Typography>
                            {typeof r.rating === "number" && (
                              <Box sx={{ display: "flex", alignItems: "center", gap: .5 }}>
                                <Rating size="small" value={Number(r.rating)} precision={0.1} readOnly />
                                <Typography variant="caption" sx={noWrapSx}>
                                  {r.rating} ({r.user_ratings_total?.toLocaleString?.() || 0})
                                </Typography>
                              </Box>
                            )}
                            <Typography variant="caption" sx={{ color: "text.secondary", ...noWrapSx }}>{r.vicinity}</Typography>
                            {typeof r._distM === "number" && isFinite(r._distM) && (
                              <Typography variant="caption" sx={{ display: "block", mt: .25, color: "text.secondary" }}>
                                약 {(r._distM / 1000).toFixed(2)} km
                              </Typography>
                            )}
                          </Box>
                        ))}
                        <Box ref={sentinelRef} sx={{ height: 1 }} />
                      </>
                    )}
                  </Box>
                )}

                {/* 주변 관광지 탭 */}
                {panelTab === 2 && (
                  <Box sx={{ p: 2 }}>
                    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1, flexWrap: "wrap" }}>
                      <Chip size="small" variant="outlined" label="반경 5km 기준" />
                      {selectedPlace?.backendId ? (
                        <Chip size="small" color="success" label="출처: Backend" />
                      ) : (
                        <Chip size="small" color="warning" label="백엔드 장소ID 없음 (Google 폴백)" />
                      )}
                    </Box>

                    {loadingSights ? (
                      <Box sx={{ py: 6, textAlign: "center" }}>
                        <CircularProgress size={24} />
                        <Typography variant="caption" sx={{ display: "block", mt: 1 }}>
                          주변 관광지 불러오는 중…
                        </Typography>
                      </Box>
                    ) : nearbySights.length === 0 ? (
                      <Typography variant="body2" color="text.secondary">
                        조건에 맞는 주변 관광지를 찾지 못했습니다.
                      </Typography>
                    ) : (
                      <Stack spacing={1.2}>
                        {nearbySights.map((s) => {
                          const lat =
                            typeof s.geometry?.location?.lat === "function"
                              ? s.geometry.location.lat()
                              : undefined;
                          const lng =
                            typeof s.geometry?.location?.lng === "function"
                              ? s.geometry.location.lng()
                              : undefined;
                          const pos =
                            lat != null && lng != null ? { lat, lng } : undefined;

                          return (
                            <Paper key={s.place_id || s._id || s.name} sx={{ p: 1.25, border: "1px solid #eee" }}>
                              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                                <Avatar sx={{ width: 28, height: 28, fontSize: 12, bgcolor: "#1976d2", color: "white" }}>
                                  <MuseumIcon sx={{ fontSize: 16 }} />
                                </Avatar>
                                <Box sx={{ flex: 1, minWidth: 0 }}>
                                  <Typography variant="subtitle2" sx={{ fontWeight: 700, ...noWrapSx }}>
                                    {s.name}
                                  </Typography>

                                  {typeof s.rating === "number" && (
                                    <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
                                      <Rating size="small" value={Number(s.rating)} precision={0.1} readOnly />
                                      <Typography variant="caption" sx={noWrapSx}>
                                        {s.rating} ({s.user_ratings_total?.toLocaleString?.() || 0})
                                      </Typography>
                                    </Box>
                                  )}

                                  <Typography variant="caption" sx={{ color: "text.secondary", ...noWrapSx }}>
                                    {s.vicinity}
                                  </Typography>

                                  {typeof s._distM === "number" && isFinite(s._distM) && (
                                    <Typography variant="caption" sx={{ display: "block", mt: 0.25, color: "text.secondary" }}>
                                      약 {(s._distM / 1000).toFixed(2)} km
                                    </Typography>
                                  )}
                                </Box>

                                <Button
                                  size="small"
                                  variant="outlined"
                                  onClick={() => {
                                    openPanel({
                                      name: s.name,
                                      placeId: s.place_id || null,
                                      position: pos,
                                    });
                                  }}
                                >
                                  자세히
                                </Button>
                              </Box>
                            </Paper>
                          );
                        })}
                      </Stack>
                    )}
                  </Box>
                )}
              </Box>
            </LeftPlacePanel>
          </Box>
        )}

        {/* 가운데: 지도 */}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <StyledPaper sx={{ mb: 3, display: "flex", flexDirection: "column" }}>
            <Box
              sx={{
                mb: 2,
                display: "grid",
                gridTemplateColumns: "1fr auto auto",
                gap: 8,
                alignItems: "center",
              }}
            >
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
                  onClick={() =>
                    showRoute ? (setShowRoute(false), setRoute(null)) : buildRouteFromActiveDay()
                  }
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
              {isLoaded ? (
                <SearchBox />
              ) : (
                <TextField fullWidth size="small" placeholder="장소 검색 준비 중…" disabled />
              )}
            </Box>

            <Chip
              label={`${itineraryData.length}일 ${Math.max(itineraryData.length - 1, 0)}박`}
              size="small"
              sx={{ bgcolor: "#e3f2fd", color: "#1976d2", mb: 2, ...noWrapSx }}
            />

            {/* ★ 지도 영역: 남는 공간 자동 채우기 */}
            <MapShell>
              {loadError && (
                <Box sx={{ p: 2, color: "error.main" }}>
                  지도를 불러오는 중 오류가 발생했습니다. API 키/권한을 확인하세요.
                </Box>
              )}
              {!isLoaded && !loadError && <Box sx={{ p: 2 }}>지도를 불러오는 중…</Box>}
              {isLoaded && (
                <GoogleMap
                  center={selectedPlace?.position || mapCenter}
                  zoom={selectedPlace ? 14 : 12}
                  mapContainerStyle={{ width: "100%", height: "100%" }}
                  options={mapOptions}
                  onLoad={(map) => {
                    mapRef.current = map;
                    ensurePlacesService();
                  }}
                >
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
                            onClick={() => openPanel({ name: m.title, placeId: m.placeId, position: m.position, backendId: m.backendId })}
                          />
                        ))}
                        {quickSpotMarkers.map((m) => (
                          <Marker
                            key={m.key}
                            position={m.position}
                            title={m.title}
                            clusterer={clusterer}
                            onClick={() => openPanel({ name: m.title, placeId: m.placeId, position: m.position, backendId: m.backendId })}
                          />
                        ))}
                      </>
                    )}
                  </MarkerClustererF>

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

          {/* 아래 카드 영역 (페이지 스크롤 허용) */}
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Paper
                sx={{
                  cursor: "pointer",
                  transition: "all .2s",
                  "&:hover": { transform: "translateY(-2px)", boxShadow: 4 },
                  p: 3,
                  textAlign: "center",
                }}
              >
                <FlightTakeoffIcon sx={{ fontSize: 44, mb: 1.5, color: "#666" }} />
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5, ...noWrapSx }}>
                  갈 곳을
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={noWrapSx}>
                  직접 검색 입력
                </Typography>
              </Paper>
            </Grid>
            <Grid item xs={12} md={6}>
              <Paper
                sx={{
                  cursor: "pointer",
                  transition: "all .2s",
                  "&:hover": { transform: "translateY(-2px)", boxShadow: 4 },
                  p: 3,
                  textAlign: "center",
                }}
              >
                <RestaurantIcon sx={{ fontSize: 44, mb: 1.5, color: "#666" }} />
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 0.5, ...noWrapSx }}>
                  음식스팟
                </Typography>
                <Typography variant="body2" color="text.secondary" sx={noWrapSx}>
                  인기 많은 장소
                </Typography>
              </Paper>
            </Grid>
          </Grid>
        </Box>

        {/* 오른쪽: 여행 일정표 */}
        <Paper
          sx={{
            width: { xs: "100%", lg: 440 },
            borderRadius: 2,
            boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
            maxHeight: "calc(100dvh - 120px)",   // ★ dvh 사용
            display: "flex",
            flexDirection: "column",
            flex: "0 0 auto",
            overflow: "hidden", // 내부 컨텐츠만 스크롤
          }}
        >
          <Box sx={{ p: 3, borderBottom: "1px solid #e0e0e0" }}>
            <Typography variant="h6" sx={{ fontWeight: 800, mb: 2, ...noWrapSx }}>
              부산 여행 일정
            </Typography>
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
              {[
                { name: "해운대 해수욕장", location: "부산광역시 해운대구", icon: <BeachAccessIcon />, color: "#FF6B6B" },
                { name: "광안리 해변", location: "부산 해수욕장 중 하나", icon: <BeachAccessIcon />, color: "#FF6B6B" },
                { name: "감천문화마을", location: "한국의 마추픽추", icon: <MuseumIcon />, color: "#FF6B6B" },
                { name: "자갈치 시장", location: "신선한 수산물", icon: <RestaurantIcon />, color: "#FF6B6B" },
              ].map((spot, idx) => (
                <Grid item xs={6} key={idx}>
                  <Paper
                    onClick={() =>
                      openPanel({
                        name: spot.name,
                        placeId: null,
                        position: spotCoordsRef.current[spot.name],
                      })
                    }
                    sx={{
                      cursor: "pointer",
                      bgcolor: spot.color,
                      color: "white",
                      transition: "all .2s",
                      "&:hover": { transform: "translateY(-1px)" },
                      p: 1.8,
                      borderRadius: 2,
                    }}
                  >
                    <Box sx={{ display: "flex", alignItems: "center", mb: 0.8 }}>
                      {spot.icon}
                      <Box sx={{ ml: 1, flex: 1, minWidth: 0 }}>
                        <Typography variant="body2" sx={{ fontWeight: 700, ...noWrapSx }}>
                          {spot.name}
                        </Typography>
                        <Typography variant="caption" sx={{ opacity: 0.9, ...noWrapSx }}>
                          {spot.location}
                        </Typography>
                      </Box>
                      <Chip
                        label="상세"
                        size="small"
                        sx={{
                          bgcolor: "rgba(255,255,255,0.2)",
                          color: "white",
                          height: 22,
                          fontSize: ".7rem",
                        }}
                      />
                    </Box>
                  </Paper>
                </Grid>
              ))}
            </Grid>
          </Box>

          <Box sx={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>
            <Box sx={{ p: 3, pb: 1 }}>
              <Typography variant="subtitle1" sx={{ fontWeight: 700, mb: 1, ...noWrapSx }}>
                여행 일정표
              </Typography>
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{ mb: 2, display: "block", ...noWrapSx }}
              >
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
                            width: 28,
                            height: 28,
                            fontSize: 13,
                            mr: 1.5,
                            bgcolor: activeDay === index ? "white" : "#2196f3",
                            color: activeDay === index ? "#2196f3" : "white",
                          }}
                        >
                          {index + 1}
                        </Avatar>
                        <Box sx={{ minWidth: 0 }}>
                          <Typography variant="body1" sx={{ fontWeight: 700, ...noWrapSx }}>
                            {day.dayName}
                          </Typography>
                          <Typography variant="caption" sx={{ opacity: 0.75, ...noWrapSx }}>
                            {day.date}
                          </Typography>
                        </Box>
                      </Box>
                      <Box sx={{ display: "flex", alignItems: "center" }}>
                        <Badge badgeContent={day.places.length} color="primary" sx={{ mr: 1 }} />
                        <IconButton
                          size="small"
                          onClick={(e) => (
                            e.stopPropagation(),
                            setExpandedDays((p) => {
                              const n = new Set(p);
                              n.has(index) ? n.delete(index) : n.add(index);
                              return n;
                            })
                          )}
                          sx={{ color: "inherit" }}
                        >
                          {expandedDays.has(index) ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                        </IconButton>
                      </Box>
                    </CompactDayButton>

                    <Collapse in={expandedDays.has(index)}>
                      <Box sx={{ ml: 3, mb: 1 }}>
                        {day.places.map((place, placeIndex) => (
                          <Box
                            key={place.id}
                            onClick={() =>
                              openPanel({
                                name: place.name,
                                placeId: place.placeId,
                                position: spotCoordsRef.current[place.name],
                              })
                            }
                            sx={{
                              display: "flex",
                              alignItems: "center",
                              py: 0.9,
                              px: 1.2,
                              cursor: "pointer",
                              bgcolor:
                                activeDay === index ? "rgba(33, 150, 243, 0.06)" : "transparent",
                              borderRadius: 1.2,
                              mb: 0.6,
                              "&:hover": { bgcolor: "rgba(33,150,243,.09)" },
                            }}
                          >
                            <Avatar
                              sx={{
                                width: 20,
                                height: 20,
                                fontSize: 11,
                                bgcolor: "#2196f3",
                                mr: 1.1,
                              }}
                            >
                              {placeIndex + 1}
                            </Avatar>
                            <Box sx={{ flex: 1, minWidth: 0 }}>
                              <Typography variant="body2" sx={{ fontWeight: 600, ...noWrapSx }}>
                                {place.name}
                              </Typography>
                              <Typography
                                variant="caption"
                                color="text.secondary"
                                sx={{ display: "block", ...noWrapSx }}
                              >
                                {place.time}
                              </Typography>
                              {place.address && (
                                <Typography
                                  variant="caption"
                                  color="text.secondary"
                                  sx={{ display: "block", ...noWrapSx }}
                                >
                                  {place.address}
                                </Typography>
                              )}
                              {typeof place.rating === "number" && (
                                <Typography variant="caption" color="text.secondary">
                                  ★ {place.rating.toFixed(1)}
                                </Typography>
                              )}
                            </Box>
                            <Button
                              size="small"
                              variant="outlined"
                              onClick={(e) => {
                                e.stopPropagation();
                                removePlaceFromDay(index, place.id);
                              }}
                            >
                              삭제
                            </Button>
                            <Box sx={{ ml: 1, display: "flex", gap: 0.5 }}>
                              <Button
                                size="small"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onReorderPlace(index, placeIndex, placeIndex - 1);
                                }}
                              >
                                ↑
                              </Button>
                              <Button
                                size="small"
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onReorderPlace(index, placeIndex, placeIndex + 1);
                                }}
                              >
                                ↓
                              </Button>
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
                    "&:hover": {
                      borderColor: "#2196f3",
                      color: "#2196f3",
                      bgcolor: "rgba(33,150,243,.05)",
                    },
                  }}
                  onClick={() => {
                    const name = window.prompt("추가할 장소 이름?");
                    if (!name) return;
                    const pos = spotCoordsRef.current[name] || BUSAN_CENTER;
                    const newPlace = {
                      id: `temp-${Date.now()}`,
                      name,
                      description: "",
                      duration: 2,
                      locX: pos.lng,
                      locY: pos.lat,
                      address: "",
                      rating: null,
                      time: "10:00",
                      placeId: null,
                      icon: <MuseumIcon />,
                    };
                    addPlaceToDay(activeDay, newPlace);
                  }}
                >
                  일정 추가
                </Button>
              </Box>
            </Box>
          </Box>

          {/* 하단 액션 바 */}
          <Box
            sx={{
              position: "sticky",
              bottom: 0,
              bgcolor: "#fff",
              borderTop: "1px solid #e0e0e0",
              p: 1.5,
              zIndex: 1,
            }}
          >
            <Stack direction="row" spacing={1} justifyContent="flex-end">
              <Button
                variant="outlined"
                startIcon={<FavoriteIcon />}
                size="small"
                onClick={() => navigate("/wishlist")}
                sx={noWrapSx}
              >
                위시리스트
              </Button>
              <Button
                variant="outlined"
                startIcon={<FolderOpenIcon />}
                size="small"
                onClick={() => setOpenLoadDlg(true)}
                sx={noWrapSx}
              >
                불러오기
              </Button>
              <Button variant="outlined" startIcon={<ShareIcon />} size="small" sx={noWrapSx}>
                공유
              </Button>
              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={handleSavePlan}
                sx={{ bgcolor: "#FF6B6B", ...noWrapSx }}
                size="small"
              >
                저장(로컬)
              </Button>
              {/* <Button variant="contained" color="primary" onClick={handleSaveCourseToServer} size="small">서버 저장</Button> */}
            </Stack>
          </Box>
        </Paper>
      </Box>

      {/* 저장된 코스 불러오기 Dialog */}
      <Dialog open={openLoadDlg} onClose={() => setOpenLoadDlg(false)} fullWidth maxWidth="sm">
        <DialogTitle>저장된 코스 불러오기</DialogTitle>
        <DialogContent dividers>
          {plans.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              아직 저장된 코스가 없습니다.
            </Typography>
          ) : (
            <Stack spacing={1.2}>
              {plans.map((p) => (
                <Paper
                  key={p.id}
                  sx={{ p: 1.5, display: "flex", alignItems: "center", gap: 1.5 }}
                >
                  <Avatar variant="rounded" src={p.cover || undefined} sx={{ width: 56, height: 40 }}>
                    <RouteIcon fontSize="small" />
                  </Avatar>
                  <Box sx={{ flex: 1, minWidth: 0 }}>
                    <Typography variant="subtitle2" sx={noWrapSx}>
                      {p.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {new Date(p.createdAt).toLocaleString()}
                    </Typography>
                  </Box>
                  <Stack direction="row" spacing={1}>
                    <Button size="small" variant="outlined" onClick={() => handleLoadPlan(p.id)}>
                      불러오기
                    </Button>
                    <IconButton size="small" color="error" onClick={() => handleDeletePlan(p.id)}>
                      <DeleteOutlineIcon />
                    </IconButton>
                  </Stack>
                </Paper>
              ))}
            </Stack>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenLoadDlg(false)}>닫기</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snack.open}
        autoHideDuration={2000}
        onClose={() => setSnack({ ...snack, open: false })}
        anchorOrigin={{ vertical: "top", horizontal: "center" }}
      >
        <Alert severity="success" onClose={() => setSnack({ ...snack, open: false })}>
          {snack.msg}
        </Alert>
      </Snackbar>
    </Box>
  );
}
