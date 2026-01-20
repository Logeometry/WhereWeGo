// src/pages/TravelPlanKakaoPage.js
import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import {
  Box, Paper, Typography, Stack, Button, Select, MenuItem, Alert, Divider, Chip,
  IconButton, CircularProgress, Grid, TextField, Tooltip, Snackbar, ToggleButton, ToggleButtonGroup
} from "@mui/material";
import DirectionsIcon from "@mui/icons-material/Directions";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import MapIcon from "@mui/icons-material/Map";
import SearchIcon from "@mui/icons-material/Search";
import FamilyRestroomIcon from "@mui/icons-material/FamilyRestroom";
import LandscapeIcon from "@mui/icons-material/Landscape";
import MuseumIcon from "@mui/icons-material/Museum";
import BeachAccessIcon from "@mui/icons-material/BeachAccess";
import CloseIcon from "@mui/icons-material/Close";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import FullscreenExitIcon from "@mui/icons-material/FullscreenExit";
import DeleteOutlineIcon from "@mui/icons-material/DeleteOutline";
import ReplayIcon from "@mui/icons-material/Replay";
import VisibilityIcon from "@mui/icons-material/Visibility";
// import TuneIcon from "@mui/icons-material/Tune"; // 일정 옵션 UI 제거로 불필요
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import SmartToyIcon from "@mui/icons-material/SmartToy";
import MapOutlinedIcon from "@mui/icons-material/MapOutlined";
import HandymanIcon from "@mui/icons-material/Handyman";
import { useLocation, useNavigate } from "react-router-dom";

/** ENV */
const API_PREFIX =
  process.env.REACT_APP_API_PREFIX ||
  (typeof import.meta !== "undefined" && import.meta.env && (import.meta.env.VITE_API_PREFIX || import.meta.env.VITE_API_BASE_URL)) ||
  "http://localhost:8000";
const API_BASE_URL = `${API_PREFIX.replace(/\/$/, "")}`;

const KAKAO_APPKEY =
  process.env.REACT_APP_KAKAO_MAP_APPKEY ||
  (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_KAKAO_MAP_APPKEY) ||
  "";

const GOOGLE_API_KEY =
  process.env.REACT_APP_GOOGLE_MAPS_KEY ||
  (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_GOOGLE_MAPS_KEY) ||
  "";

/** Helpers */
function iconFor(place) {
  const name = (place?.name || "").toLowerCase();
  const cat = (place?.category_type || place?.category_group || place?.category || "").toLowerCase();
  if (name.includes("해수욕장") || name.includes("beach")) return "🏖️";
  if (name.includes("공원")) return "🌳";
  if (name.includes("시장")) return "🐟";
  if (name.includes("사찰") || name.includes("절")) return "⛩️";
  if (name.includes("타워")) return "🗼";
  if (name.includes("대교") || name.includes("bridge")) return "🌉";
  if (name.includes("아쿠아리움")) return "🐠";
  if (name.includes("감천") || name.includes("마을") || name.includes("village")) return "🎨";
  if (cat.includes("문화")) return "🎨";
  if (cat.includes("자연")) return "🌲";
  if (cat.includes("레포츠")) return "⚽";
  if (cat.includes("쇼핑")) return "🛍️";
  if (cat.includes("음식") || cat.includes("restaurant") || cat.includes("food")) return "🍽️";
  if (cat.includes("숙박") || cat.includes("hotel")) return "🏨";
  return "📍";
}
const VEH_ICON = { BUS: "🚌", SUBWAY: "🚇", TRAIN: "🚆", TRAM: "🚊", RAIL: "🚄", FERRY: "⛴️" };
const vehicleIcon = (t) => VEH_ICON[t] || "🚍";
function stripHTML(html = "") {
  const d = document.createElement("div");
  d.innerHTML = html;
  return d.textContent || d.innerText || "";
}
const dayColor = (i) => `hsl(${(i * 65) % 360}, 70%, 45%)`;

/** Kakao loader */
async function ensureKakaoMaps(appkey) {
  if (!appkey) throw new Error("Kakao appkey is missing");
  if (window.kakao?.maps) return window.kakao;

  const EXISTING_ID = "kakao-sdk";
  document.getElementById(EXISTING_ID)?.remove();

  const loadOnce = (src, timeout = 15000) =>
    new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.id = EXISTING_ID;
      s.src = src.includes("autoload") ? src : `${src}?autoload=false`;
      s.async = true;
      s.defer = true;

      const timer = setTimeout(() => {
        s.remove();
        reject(new Error("Kakao SDK load timeout"));
      }, timeout);

      s.onload = () => {
        try {
          if (!window.kakao?.maps) {
            clearTimeout(timer);
            reject(new Error("Kakao SDK loaded but kakao.maps missing"));
            return;
          }
          window.kakao.maps.load(() => {
            clearTimeout(timer);
            resolve(window.kakao);
          });
        } catch (e) {
          clearTimeout(timer);
          reject(e);
        }
      };
      s.onerror = () => {
        clearTimeout(timer);
        s.remove();
        reject(new Error("Failed to load Kakao SDK"));
      };
      document.head.appendChild(s);
    });

  const base = "https://dapi.kakao.com/v2/maps/sdk.js";
  const q = `?autoload=false&appkey=${encodeURIComponent(appkey)}&libraries=services,clusterer,drawing`;
  try {
    return await loadOnce(base + q);
  } catch {
    return loadOnce("//dapi.kakao.com/v2/maps/sdk.js" + q);
  }
}

/** Haversine (fallback) */
function haversineKm(a, b) {
  const R = 6371;
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad((b?.lat ?? 0) - (a?.lat ?? 0));
  const dLng = toRad((b?.lng ?? 0) - (a?.lng ?? 0));
  const la1 = toRad(a?.lat ?? 0), la2 = toRad(b?.lat ?? 0);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(la1) * Math.cos(la2) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(h));
}

/** 일정 옵션을 상수로만 사용 (UI 제거) */
const AVG_STAY_MINS = 80;          // 평균 체류시간(분)
const BUDGET_MINS_PER_DAY = 8 * 60; // 하루 예산(분)

/** Component */
export default function TravelPlanKakaoPage() {
  const navigate = useNavigate();
  const location = useLocation();

  // 장소
  const [places, setPlaces] = useState([]);
  const [loadingPlaces, setLoadingPlaces] = useState(true);
  const [placesError, setPlacesError] = useState("");

  // 프리셋
  const [presets, setPresets] = useState({ classic: [], history: [], nature: [], family: [] });

  // 계획 모드: 'manual' | 'ai'
  const [planningMode, setPlanningMode] = useState("manual");

  // 수동 선택 / 모드
  const [selectedNames, setSelectedNames] = useState([]);
  const [nameToIdMap, setNameToIdMap] = useState({});
  const [mode, setMode] = useState("transit");
  const [searchQuery, setSearchQuery] = useState("");

  // 지도
  const [sdkError, setSdkError] = useState("");
  const [kakaoLoaded, setKakaoLoaded] = useState(false);
  const mapRef = useRef(null);
  const mapElRef = useRef(null);
  const markersRef = useRef([]);
  const polylinesRef = useRef([]);
  const overlaysRef = useRef([]);

  // 수동 경로/일정
  const [routeData, setRouteData] = useState(null);
  const [dayRecords, setDayRecords] = useState([]);
  const [generating, setGenerating] = useState(false);

  // 여행 날짜
  const [startDate, setStartDate] = useState("");  // "YYYY-MM-DD"
  const [endDate, setEndDate] = useState("");      // "YYYY-MM-DD"
  const tripDays = useMemo(() => {
    if (!startDate || !endDate) return 0;
    const s = new Date(startDate);
    const e = new Date(endDate);
    const diff = Math.floor((e - s) / (1000 * 60 * 60 * 24)) + 1;
    return Math.max(0, diff);
  }, [startDate, endDate]);
  const dateError = useMemo(() => {
    if (!startDate || !endDate) return "";
    return new Date(endDate) < new Date(startDate) ? "종료일은 시작일 이후여야 합니다." : "";
  }, [startDate, endDate]);

  // AI 상태
  const [aiGenerating, setAiGenerating] = useState(false);
  const [aiPlan, setAiPlan] = useState(null); // {dailySchedule:[...]}

  // UI
  const [mapFull, setMapFull] = useState(false);
  const [toast, setToast] = useState({ open: false, msg: "", sev: "info" });

  /** 초기 로딩 */
  useEffect(() => {
    (async () => {
      try {
        const incoming = Array.isArray(location.state?.spots) ? location.state.spots : [];
        if (incoming.length) {
          const mapped = incoming.map((s) => ({
            id: s.id || s._id,
            name: s.name || "이름 없음",
            category: s.category || s.category_group || "관광지",
            icon: iconFor(s),
            address: s.address || "",
            rating: typeof s.rating === "number" ? s.rating : 0,
            lat: s.lat,
            lng: s.lng,
          }));
          const n2i = {};
          mapped.forEach((p) => (n2i[p.name] = p.id));
          setPlaces(mapped);
          setNameToIdMap(n2i);
          setupPresets(mapped);
        } else {
          await loadPlacesFromDB();
        }
      } catch (e) {
        console.error(e);
        setPlacesError(e?.message || "장소 로드 실패");
      } finally {
        setLoadingPlaces(false);
      }

      try {
        const kakao = await ensureKakaoMaps(KAKAO_APPKEY);
        setKakaoLoaded(true);
        if (mapElRef.current) {
          mapRef.current = new kakao.maps.Map(
            mapElRef.current,
            { center: new kakao.maps.LatLng(35.1796, 129.0756), level: 8 }
          );
        }
      } catch (e) {
        console.error(e);
        setSdkError(
          (e?.message || "Kakao SDK 로딩 실패") +
          "\n- 카카오 개발자 콘솔 > 내 애플리케이션 > 플랫폼에 웹 도메인 등록" +
          "\n- JavaScript 키 사용(REST 키 X)" +
          "\n- dapi.kakao.com 차단 여부 확인"
        );
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /** DB 로딩 */
  const loadPlacesFromDB = async () => {
    const res = await fetch(`${API_BASE_URL}/api/v1/simple_detail`);
    if (!res.ok) throw new Error(`API 오류: ${res.status}`);
    const all = await res.json();
    if (!Array.isArray(all) || all.length === 0) throw new Error("DB에 장소 데이터가 없습니다");

    const popular = all.slice(0, 30);
    const mapped = popular.map((p) => ({
      id: p.id || p._id,
      name: p.name || "이름 없음",
      category: p.category_group || p.category || "기타",
      icon: iconFor(p),
      rating: p.rating || 0,
      address: p.address || "",
      lat: p.lat,
      lng: p.lng,
    }));
    const n2i = {};
    mapped.forEach((p) => (n2i[p.name] = p.id));
    setPlaces(mapped);
    setNameToIdMap(n2i);
    setupPresets(mapped);
  };

  /** 프리셋 */
  const setupPresets = (arr) => {
    if (!arr?.length) return;
    const byName = (names) => {
      const hit = [];
      names.forEach((q) => {
        const f = arr.find((p) => p.name.includes(q) || q.includes(p.name));
        if (f) hit.push(f.name);
      });
      return hit;
    };

    let classic = byName(["해운대", "광안리", "감천"]);
    if (classic.length < 3 && arr.length >= 3) classic = arr.slice(0, 3).map((p) => p.name);

    let history = arr.length >= 6 ? arr.slice(3, 6).map((p) => p.name) : arr.slice(0, Math.min(3, arr.length)).map((p) => p.name);
    let nature = arr.length >= 9 ? arr.slice(6, 9).map((p) => p.name) : arr.slice(0, Math.min(3, arr.length)).map((p) => p.name);
    let family = arr.length >= 12 ? arr.slice(9, 12).map((p) => p.name) : arr.slice(0, Math.min(3, arr.length)).map((p) => p.name);

    setPresets({ classic, history, nature, family });
  };

  /** 수동 선택 */
  const togglePlace = (name) => setSelectedNames((prev) => (prev.includes(name) ? prev.filter((n) => n !== name) : [...prev, name]));
  const removePlace = (name) => setSelectedNames((prev) => prev.filter((n) => n !== name));
  const clearSelection = () => { setSelectedNames([]); setRouteData(null); clearMap(); };

  /** 이름→ObjectId */
  const getPlaceIds = async (names) => {
    const ids = [];
    const misses = [];
    for (const nm of names) {
      if (nameToIdMap[nm]) { ids.push(nameToIdMap[nm]); continue; }
      const local = places.find((p) => p.name === nm);
      if (local?.id) { ids.push(local.id); setNameToIdMap((prev) => ({ ...prev, [nm]: local.id })); continue; }
      try {
        const r = await fetch(`${API_BASE_URL}/api/v1/simple_detail?query=${encodeURIComponent(nm)}`);
        if (!r.ok) throw new Error(`search ${nm} http ${r.status}`);
        const data = await r.json();
        if (Array.isArray(data) && data[0]) {
          const oid = data[0].id || data[0]._id;
          if (oid) { ids.push(oid); setNameToIdMap((prev) => ({ ...prev, [nm]: oid })); continue; }
        }
        misses.push(nm);
      } catch (e) { console.warn("검색 실패:", nm, e); misses.push(nm); }
    }
    if (misses.length) throw new Error(`다음 장소를 찾지 못했습니다:\n- ${misses.join("\n- ")}`);
    return ids;
  };

  /** 지도 클리어/그리기 */
  const clearMap = useCallback(() => {
    markersRef.current.forEach(({ marker }) => marker.setMap(null));
    polylinesRef.current.forEach((p) => p.setMap(null));
    overlaysRef.current.forEach((o) => o.setMap(null));
    markersRef.current = [];
    polylinesRef.current = [];
    overlaysRef.current = [];
  }, []);

  const drawOnMap = useCallback(
    (data) => {
      const kakao = window.kakao;
      if (!kakao || !mapRef.current) return;
      clearMap();

      if (data?.center) mapRef.current.setCenter(new kakao.maps.LatLng(data.center.lat, data.center.lng));
      if (data?.zoom != null) mapRef.current.setLevel(Number(data.zoom));

      (data?.markers || []).forEach((m) => {
        const pos = new kakao.maps.LatLng(m.lat, m.lng);
        const marker = new kakao.maps.Marker({ position: pos, map: mapRef.current });
        const infowindow = new kakao.maps.InfoWindow({
          content: `<div style="padding:10px; min-width:150px;"><strong>${m.order}. ${m.name}</strong><br/><small style="color:#666;">${m.address ?? ""}</small></div>`,
        });
        kakao.maps.event.addListener(marker, "click", () => infowindow.open(mapRef.current, marker));
        markersRef.current.push({ marker, infowindow });
      });

      (data?.segments || []).forEach((seg) => {
        const path = (seg.polyline || []).map((p) => new kakao.maps.LatLng(p.lat, p.lng));
        if (path.length) {
          const polyline = new kakao.maps.Polyline({
            path,
            strokeWeight: 5,
            strokeColor: seg.color || "#667eea",
            strokeOpacity: 0.7,
            strokeStyle: "solid",
          });
          polyline.setMap(mapRef.current);
          polylinesRef.current.push(polyline);
        }
        (seg.steps || []).forEach((step, idx) => {
          const total = seg.polyline?.length || 0;
          if (!total) return;
          const midIdx = Math.floor(total * ((idx + 1) / ((seg.steps?.length || 1) + 1)));
          const mid = seg.polyline?.[midIdx] || seg.polyline?.[0];
          if (!mid) return;
          const pos = new kakao.maps.LatLng(mid.lat, mid.lng);
          let html = "";
          if (step.travel_mode === "TRANSIT" && step.transit_details) {
            const t = step.transit_details;
            html = `<div style="padding:8px 12px;background:#fff;border:2px solid ${seg.color || "#667eea"};border-radius:20px;box-shadow:0 2px 8px rgba(0,0,0,.2);font-weight:bold;font-size:13px;white-space:nowrap;">${vehicleIcon(t.vehicle_type)} ${t.line_short_name || t.line_name || ""}</div>`;
          } else if (step.travel_mode === "WALKING") {
            html = `<div style="padding:6px 10px;background:#52b788;color:#fff;border-radius:14px;box-shadow:0 2px 6px rgba(0,0,0,.15);font-weight:bold;font-size:12px;white-space:nowrap;">🚶 ${step.duration || ""}</div>`;
          } else return;
          const overlay = new kakao.maps.CustomOverlay({ position: pos, content: html, yAnchor: 0.5 });
          overlay.setMap(mapRef.current);
          overlaysRef.current.push(overlay);
        });
      });
    },
    [clearMap]
  );

  /** 수동 경로 생성 */
  const preplanNames = async (names) => {
    if (names.length < 2) return names;
    const pts = names.map((nm) => places.find((p) => p.name === nm)).filter(Boolean);
    const idxs = pts.map((p) => names.findIndex((nm) => nm === p.name));

    const nearestOrder = (() => {
      if (pts.length <= 2) return idxs.map((_, i) => i);
      const rem = idxs.map((_, i) => i);
      const route = [rem.shift()];
      while (rem.length) {
        const last = route[route.length - 1];
        let best = 0, bestDist = Infinity;
        rem.forEach((ri, i) => {
          const d = haversineKm(pts[last], pts[ri]);
          if (d < bestDist) { bestDist = d; best = i; }
        });
        route.push(rem.splice(best, 1)[0]);
      }
      return route;
    })();

    let order = nearestOrder.map((i) => i);

    // 간단한 예산 체크 (상수 사용)
    const totalLegKm = order.slice(0, -1).reduce((s, _, i) => s + haversineKm(pts[order[i]], pts[order[i + 1]]), 0);
    const moveMins = (totalLegKm / (mode === "walking" ? 4.5 : mode === "driving" ? 35 : 22)) * 60;
    const placeCount = order.length;
    const totalMins = moveMins + placeCount * AVG_STAY_MINS;
    let final = order.slice();
    if (totalMins > BUDGET_MINS_PER_DAY && placeCount >= 3) {
      final = order.slice(0, order.length - 1);
      setToast({ open: true, msg: "하루 예산 초과로 방문지 1곳을 줄였습니다.", sev: "info" });
    }
    return final.map((oi) => pts[oi]?.name).filter(Boolean);
  };

  const generateRoute = async () => {
    try {
      if (selectedNames.length < 2) { alert("최소 2개 이상의 장소를 선택해주세요."); return; }
      setGenerating(true);
      const plannedNames = await preplanNames(selectedNames);
      if (plannedNames.length < 2) { alert("일정이 2곳 미만으로 축소되어 경로를 생성할 수 없습니다."); return; }
      const finalIds = await getPlaceIds(plannedNames);
      const res = await fetch(`${API_BASE_URL}/api/v1/map/course-route`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ places: finalIds, mode }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setRouteData(data);
      drawOnMap(data);
      setDayRecords((prev) => [...prev, { day: prev.length + 1, names: plannedNames, ids: finalIds, route: data, mode }]);
    } catch (e) {
      console.error(e);
      alert(`경로 생성 실패: ${e?.message || "unknown"}`);
    } finally {
      setGenerating(false);
    }
  };

  /** 검색 추가 (수동) */
  const searchAndAdd = async () => {
    const q = searchQuery.trim();
    if (!q) return;
    try {
      const r = await fetch(`${API_BASE_URL}/api/v1/simple_detail?query=${encodeURIComponent(q)}`);
      const data = await r.json();
      if (Array.isArray(data) && data[0]) {
        const p = data[0];
        const id = p.id || p._id;
        const nm = p.name || q;
        setNameToIdMap((prev) => ({ ...prev, [nm]: id }));
        if (!places.find((x) => x.name === nm)) {
          setPlaces((prev) => [...prev, { id, name: nm, category: p.category_group || p.category || "관광지", icon: iconFor(p), lat: p.lat, lng: p.lng }]);
        }
        setSelectedNames((prev) => (prev.includes(nm) ? prev : [...prev, nm]));
        setSearchQuery("");
      } else {
        alert("검색 결과가 없습니다.");
      }
    } catch (e) {
      console.error(e);
      alert("검색 중 오류가 발생했습니다.");
    }
  };

  /** 일정/지도 조작(수동) */
  const focusDayOnMap = (idx) => { const rec = dayRecords[idx]; if (!rec) return; setRouteData(rec.route); drawOnMap(rec.route); };
  const deleteDay = (idx) => { setDayRecords((prev) => prev.filter((_, i) => i !== idx).map((r, i) => ({ ...r, day: i + 1 }))); };
  const reAddSelectionFromDay = (idx) => { const rec = dayRecords[idx]; if (!rec) return; setSelectedNames(rec.names); };

  const clearAllDays = () => setDayRecords([]);

  /** 합계(현재 지도 경로) */
  const totalDist = useMemo(() => (routeData?.segments || []).reduce((s, v) => s + (v.distance_km || 0), 0), [routeData]);
  const totalMins = useMemo(() => (routeData?.segments || []).reduce((s, v) => s + (v.duration_minutes || 0), 0), [routeData]);

  /** ── AI 자동 코스: 담아온 관광지 + 여행 날짜 반영 ── */
  const handleGenerateAIFromCaptured = async () => {
    try {
      const baseList =
        Array.isArray(location.state?.spots) && location.state.spots.length
          ? location.state.spots.map((s) => ({ name: s.name, id: s.id || s._id }))
          : places.map((p) => ({ name: p.name, id: p.id }));

      if (baseList.length < 2) { alert("담아온(또는 로드된) 관광지가 2곳 이상이어야 합니다."); return; }
      if (dateError) { alert(dateError); return; }

      setAiGenerating(true);

      const names = baseList.map((b) => b.name);
      const ids = (await getPlaceIds(names)) || baseList.map((b) => b.id).filter(Boolean);
      if (!ids.length) throw new Error("장소 ID를 확인할 수 없습니다.");

      // 날짜 기반 일수, 없으면 장소 수로 추정
      const estimatedBySpots = Math.max(1, Math.ceil(ids.length / 3));
      const travelDuration = tripDays > 0 ? tripDays : estimatedBySpots;

      const transportModeMap = { transit: "TRANSIT", driving: "DRIVE", walking: "WALK" };

      const payload = {
        spots: ids,
        user_id: null,
        travelDuration,
        travel_start_date: startDate || null,
        travel_end_date: endDate || null,
        starting_point: ids[0],
        transport_mode: transportModeMap[mode] || "DRIVE",
        is_public: false,
        description: "AI 자동 코스 (여행 날짜 기반)",
      };

      const resp = await fetch(`${API_BASE_URL}/api/v1/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify(payload),
      });
      if (!resp.ok) {
        const t = await resp.text();
        throw new Error(`/generate 오류: ${resp.status} - ${t}`);
      }
      const plan = await resp.json();
      if (!plan?.dailySchedule?.length) throw new Error("생성된 일정이 비어있습니다.");

      setAiPlan(plan);
      await drawAIDayOnMap(0, plan);
    } catch (e) {
      console.error(e);
      alert(`AI 코스 생성 실패: ${e?.message || "unknown"}`);
    } finally {
      setAiGenerating(false);
    }
  };

  const drawAIDayOnMap = async (dayIndex, plan = aiPlan) => {
    if (!plan?.dailySchedule?.[dayIndex]) return;
    try {
      const day = plan.dailySchedule[dayIndex];
      const dayNames = day.places.map((p) => p.name);
      const dayIds = (await getPlaceIds(dayNames)).filter(Boolean);

      const res = await fetch(`${API_BASE_URL}/api/v1/map/course-route`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ places: dayIds, mode }),
      });
      if (!res.ok) throw new Error(`/map/course-route HTTP ${res.status}`);
      const data = await res.json();
      setRouteData(data);
      drawOnMap(data);
    } catch (e) {
      console.error(e);
      setToast({ open: true, msg: "지도로 표시 중 문제가 발생했습니다.", sev: "warning" });
    }
  };

  /** 작은 프레젠테이셔널 컴포넌트들 */
  const PlaceItem = ({ place }) => {
    const selected = selectedNames.includes(place.name);
    return (
      <Paper
        onClick={() => planningMode === "manual" && togglePlace(place.name)}
        elevation={0}
        sx={{
          p: 1.5, mb: 1, borderRadius: 2, cursor: planningMode === "manual" ? "pointer" : "default",
          border: "2px solid", borderColor: planningMode === "manual" && selected ? "primary.main" : "divider",
          bgcolor: planningMode === "manual" && selected ? "primary.main" : "background.paper",
          color: planningMode === "manual" && selected ? "primary.contrastText" : "text.primary",
          transition: "0.18s",
          "&:hover": planningMode === "manual" ? { transform: "translateX(4px)", boxShadow: selected ? 0 : 2, borderColor: "primary.main" } : {},
          display: "flex", alignItems: "center", gap: 1.5,
          opacity: planningMode === "ai" ? 0.6 : 1,
        }}
      >
        <Box sx={{ fontSize: 22, width: 28, textAlign: "center" }}>{place.icon || "📍"}</Box>
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography noWrap fontWeight={700}>{place.name}</Typography>
          <Typography variant="body2" noWrap sx={{ opacity: 0.7 }}>{place.category}</Typography>
        </Box>
      </Paper>
    );
  };

  const PresetTile = ({ title, icon, type }) => (
    <Paper
      onClick={() => planningMode === "manual" && loadPresetCourse(type)}
      elevation={0}
      sx={{
        p: 1.5, mb: 1, borderRadius: 2, border: "2px solid", borderColor: "divider",
        cursor: planningMode === "manual" ? "pointer" : "default",
        "&:hover": planningMode === "manual" ? { transform: "translateX(4px)", borderColor: "primary.main" } : {},
        opacity: planningMode === "ai" ? 0.5 : 1,
      }}
    >
      <Typography fontWeight={700} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        {icon} {title}
      </Typography>
    </Paper>
  );

  const loadPresetCourse = async (type) => {
    const course = presets[type] || [];
    if (!course.length) {
      if (places.length >= 3) {
        const rand = places.slice(0, Math.min(10, places.length)).sort(() => Math.random() - 0.5).slice(0, 3).map((p) => p.name);
        setSelectedNames(rand);
      } else { alert("아직 장소 데이터가 부족합니다."); return; }
    } else { setSelectedNames(course); }
    setTimeout(() => generateRoute(), 250);
  };

  /** Render */
  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      {/* 헤더 */}
      <Paper sx={{ mb: 2, borderRadius: 3, overflow: "hidden", background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", color: "white" }}>
        <Box sx={{ p: 3, textAlign: "center" }}>
          <Typography variant="h4" fontWeight={800}>🧭 TravelPlan Kakao Page</Typography>
          <Typography sx={{ opacity: 0.9, mt: 1 }}>
            담아온 관광지로 <b>AI 자동코스</b> 또는 <b>직접 코스</b>를 생성하세요.
          </Typography>
        </Box>
      </Paper>

      <Grid container spacing={0}>
        {/* 좌측 패널 */}
        <Grid item xs={12} md={4} lg={4}>
          <Box sx={{ p: 3, bgcolor: "#f8f9fa", borderRight: { md: "1px solid #dee2e6" }, height: { md: "calc(100vh - 220px)" }, minHeight: 700, overflowY: "auto" }}>

            {/* 계획 모드 토글 */}
            <Paper sx={{ p: 2, mb: 2 }}>
              <Typography fontWeight={700} sx={{ mb: 1 }}>🧩 코스 생성 방식</Typography>
              <ToggleButtonGroup
                color="primary"
                exclusive
                value={planningMode}
                onChange={(_, v) => v && setPlanningMode(v)}
                fullWidth
                size="small"
              >
                <ToggleButton value="manual"><HandymanIcon fontSize="small" />&nbsp;직접 코스 짜기</ToggleButton>
                <ToggleButton value="ai"><SmartToyIcon fontSize="small" />&nbsp;AI 자동코스</ToggleButton>
              </ToggleButtonGroup>
              {planningMode === "ai" ? (
                <Alert severity="info" sx={{ mt: 1 }}>
                  AI 모드에서는 입력한 <b>여행 날짜</b>를 기준으로 <b>여행 일수</b>를 계산하고,
                  담아온/로드된 관광지에서 적합한 코스를 추천합니다. (planning_options 미사용)
                </Alert>
              ) : (
                <Alert severity="info" sx={{ mt: 1 }}>
                  수동 모드에서는 왼쪽 목록에서 장소를 선택/검색해 코스를 직접 구성할 수 있어요.
                </Alert>
              )}
            </Paper>

            {/* 이동 수단 */}
            <Paper sx={{ p: 2, mb: 2 }}>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                <Typography fontWeight={700}>🚗 이동 수단</Typography>
                <Tooltip title="대중교통은 시간대/노선에 따라 달라질 수 있어요.">
                  <InfoOutlinedIcon fontSize="small" sx={{ opacity: 0.6 }} />
                </Tooltip>
              </Stack>
              <Select fullWidth size="small" value={mode} onChange={(e) => setMode(e.target.value)}>
                <MenuItem value="transit">🚇 대중교통 (추천)</MenuItem>
                <MenuItem value="driving">🚗 자동차</MenuItem>
                <MenuItem value="walking">🚶 도보</MenuItem>
              </Select>
            </Paper>

            {/* 여행 날짜 */}
            <Paper sx={{ p: 2, mb: 2 }}>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 1 }}>
                <Typography fontWeight={700}>🗓️ 여행 날짜</Typography>
                <Tooltip title="여행 기간을 입력하면 일수로 코스를 계산합니다. (AI 자동코스에 적용)">
                  <InfoOutlinedIcon fontSize="small" sx={{ opacity: 0.6 }} />
                </Tooltip>
              </Stack>

              <Stack spacing={1.2}>
                <TextField
                  label="시작일"
                  type="date"
                  size="small"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  fullWidth
                />
                <TextField
                  label="종료일"
                  type="date"
                  size="small"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                  error={!!dateError}
                  helperText={dateError || ' '}
                  fullWidth
                />

                <Stack direction="row" spacing={1} alignItems="center">
                  <Chip
                    size="small"
                    color={tripDays > 0 ? 'primary' : 'default'}
                    label={tripDays > 0 ? `여행 ${tripDays}일` : '여행 일수 미설정'}
                  />
                  <Typography variant="body2" color="text.secondary">
                    (날짜가 없으면 장소 수 기준으로 일수를 추정합니다)
                  </Typography>
                </Stack>
              </Stack>
            </Paper>

            {/* (일정 옵션 UI 제거됨) */}

            {/* ───────── 수동 모드 전용 UI ───────── */}
            {planningMode === "manual" && (
              <>
              
            


                {/* 선택된 장소 */}
                <Box sx={{ mb: 2 }}>
                  <Typography fontWeight={700} sx={{ mb: 1 }}>📍 선택된 장소 ({selectedNames.length}개)</Typography>
                  {selectedNames.length === 0 ? (<Alert severity="info" sx={{ mb: 1 }}>💡 최소 2개 이상의 장소를 선택해주세요</Alert>) : null}
                  <Paper sx={{ p: 1.5, minHeight: 80 }}>
                    {selectedNames.length === 0 ? (
                      <Typography sx={{ color: "#999", textAlign: "center" }}>장소를 선택해주세요</Typography>
                    ) : (
                      <Stack direction="row" spacing={1} flexWrap="wrap">
                        {selectedNames.map((nm, i) => (<Chip key={nm} label={`${i + 1}. ${nm}`} onDelete={() => removePlace(nm)} sx={{ bgcolor: "primary.main", color: "primary.contrastText" }} />))}
                      </Stack>
                    )}
                  </Paper>
                </Box>

                {/* 검색 */}
                <Paper sx={{ p: 1.5, mb: 2 }}>
                  <Stack direction="row" spacing={1}>
                    <TextField fullWidth size="small" placeholder="장소명을 입력 (예: 해운대)" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} InputProps={{ startAdornment: <SearchIcon sx={{ mr: 1, color: "text.secondary" }} /> }} />
                    <Button variant="contained" onClick={searchAndAdd}>추가</Button>
                  </Stack>
                </Paper>

                {/* 장소 리스트 */}
                <Box sx={{ mb: 2 }}>
                  <Typography fontWeight={700} sx={{ mb: 1 }}>
                    🏛️ {Array.isArray(location.state?.spots) && location.state.spots.length ? "담아온 관광지 (클릭해서 선택)" : "부산 주요 관광지"}
                  </Typography>
                  {loadingPlaces ? (
                    <Paper sx={{ p: 2, textAlign: "center" }}><CircularProgress size={22} sx={{ mr: 1 }} /> 불러오는 중...</Paper>
                  ) : places.length === 0 ? (
                    <Paper sx={{ p: 2, textAlign: "center", color: "#999" }}>장소가 없습니다</Paper>
                  ) : (
                    <Box>{places.map((p) => (<PlaceItem key={p.id || p.name} place={p} />))}</Box>
                  )}
                  {!!placesError && <Alert severity="warning" sx={{ mt: 1, whiteSpace: "pre-line" }}>{placesError}</Alert>}
                </Box>

                {/* 수동 액션 */}
                <Box sx={{ mb: 2 }}>
                  <Button
                    fullWidth variant="contained" startIcon={<HandymanIcon />}
                    disabled={generating || selectedNames.length < 2 || !kakaoLoaded}
                    onClick={generateRoute}
                    sx={{ mb: 1, py: 1.2 }}
                  >
                    {generating ? "경로 생성 중…" : "직접 코스 짜기 (선택한 장소로)"}
                  </Button>

                  <Button fullWidth variant="outlined" startIcon={<RestartAltIcon />} onClick={clearSelection} sx={{ py: 1.2 }}>
                    🔄 선택 초기화
                  </Button>
                </Box>

                {/* 수동 일정 누적 */}
                <Box sx={{ mb: 2 }}>
                  <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 1 }}>
                    <Typography fontWeight={700}>🗓️ 내 일정 ({dayRecords.length}일차)</Typography>
                    <Button size="small" onClick={clearAllDays} disabled={!dayRecords.length} startIcon={<DeleteOutlineIcon />}>전체 삭제</Button>
                  </Stack>
                  {dayRecords.length === 0 ? (
                    <Paper sx={{ p: 2, color: "text.secondary" }}>아직 추가된 일정이 없습니다. 경로 생성 시 1일차부터 자동으로 쌓입니다.</Paper>
                  ) : (
                    <Stack spacing={1}>
                      {dayRecords.map((rec, idx) => (
                        <Paper key={idx} sx={{ p: 1.25, borderLeft: "4px solid #667eea" }}>
                          <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: 0.5 }}>
                            <Typography fontWeight={800}>{rec.day}일차</Typography>
                            <Stack direction="row" spacing={1}>
                              <IconButton size="small" title="이 일차 경로 지도에서 보기" onClick={() => focusDayOnMap(idx)}><VisibilityIcon fontSize="small" /></IconButton>
                              <IconButton size="small" title="이 일차를 선택 목록으로 불러오기" onClick={() => reAddSelectionFromDay(idx)}><ReplayIcon fontSize="small" /></IconButton>
                              <IconButton size="small" title="이 일차 삭제" onClick={() => deleteDay(idx)}><DeleteOutlineIcon fontSize="small" /></IconButton>
                            </Stack>
                          </Stack>
                          <Typography variant="body2" sx={{ mb: 0.5 }}>{rec.names.map((n, i) => `${i + 1}. ${n}`).join("  ·  ")}</Typography>
                          {Array.isArray(rec.route?.segments) && (
                            <Typography variant="caption" color="text.secondary">
                              총 {rec.route.segments.length}구간 · {Math.round((rec.route.segments || []).reduce((s, v) => s + (v.duration_minutes || 0), 0))}분 · {(rec.route.segments || []).reduce((s, v) => s + (v.distance_km || 0), 0).toFixed(1)}km
                            </Typography>
                          )}
                        </Paper>
                      ))}
                    </Stack>
                  )}
                </Box>
              </>
            )}

            {/* ───────── AI 모드 전용 UI ───────── */}
            {planningMode === "ai" && (
              <>
                {/* AI 실행 버튼 */}
                <Box sx={{ mb: 2 }}>
                  <Button
                    fullWidth color="secondary" variant="contained" startIcon={<SmartToyIcon />}
                    disabled={
                      aiGenerating ||
                      !kakaoLoaded ||
                      (loadingPlaces && !(location.state?.spots?.length)) ||
                      !!dateError
                    }
                    onClick={handleGenerateAIFromCaptured}
                    sx={{ mb: 1, py: 1.2 }}
                  >
                    {aiGenerating ? "AI 코스 생성 중…" : "AI로 자동코스 추천 (여행 날짜 반영)"}
                  </Button>
                </Box>

                {/* AI 추천 일정 카드 */}
                {aiPlan?.dailySchedule?.length > 0 && (
                  <Box sx={{ mb: 2 }}>
                    <Typography fontWeight={700} sx={{ mb: 1 }}>🤖 AI 추천 일정</Typography>
                    {aiPlan.dailySchedule.map((day, di) => (
                      <Paper key={di} sx={{ p: 1.5, mb: 1.5, borderLeft: `6px solid ${dayColor(di)}` }}>
                        <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ mb: .5 }}>
                          <Typography fontWeight={800} sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                            <MapOutlinedIcon fontSize="small" /> {day.day}일차
                          </Typography>
                          <Button size="small" variant="outlined" onClick={() => drawAIDayOnMap(di)} startIcon={<VisibilityIcon fontSize="small" />}>
                            지도로 보기
                          </Button>
                        </Stack>
                        <Stack spacing={1}>
                          {day.places?.map((p, pi) => (
                            <Box key={`${di}-${pi}`} sx={{ pl: 0.5 }}>
                              <Typography sx={{ fontWeight: 800, mb: .2 }}>{pi + 1}. {p.name}</Typography>
                              {!!p.address && <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.4 }}>{p.address}</Typography>}
                              <Stack direction="row" spacing={2} sx={{ mt: .2 }}>
                                {!!p.time && <Typography variant="body2">🎯 {p.time}</Typography>}
                                {!!p.estimated_duration && <Typography variant="body2">⏱️ 예상 소요시간: {p.estimated_duration}분</Typography>}
                              </Stack>
                            </Box>
                          ))}
                        </Stack>
                      </Paper>
                    ))}
                  </Box>
                )}
              </>
            )}

            {/* 현재 경로 상세(수동/AI 공용) */}
            {routeData && (
              <Box id="route-info" sx={{ mb: 2 }}>
                <Typography fontWeight={700} sx={{ mb: 1 }}>📊 현재 경로 정보</Typography>
                <Box id="route-segments">
                  {(routeData.segments || []).map((seg, idx) => (
                    <Paper key={idx} sx={{ p: 1.5, mb: 1, borderLeft: `5px solid ${seg.color || "#667eea"}`, borderRadius: 1 }}>
                      <Typography sx={{ fontWeight: 700, mb: 0.5 }}>{idx + 1}. {seg.from_place} → {seg.to_place}</Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>📏 {seg.distance_km} km | ⏱️ {Math.round(seg.duration_minutes)}분</Typography>
                      {!!seg.steps?.length && (
                        <Box sx={{ p: 1, bgcolor: "#f8f9fa", borderRadius: 1 }}>
                          <Typography variant="body2" sx={{ fontWeight: 700, mb: 0.5, color: "text.primary" }}>📋 상세 경로</Typography>
                          <Stack spacing={1}>
                            {seg.steps.map((st, j) => {
                              if (st.travel_mode === "TRANSIT" && st.transit_details) {
                                const t = st.transit_details;
                                return (
                                  <Paper key={j} sx={{ p: 1 }}>
                                    <Typography fontWeight={700} color="primary">{vehicleIcon(t.vehicle_type)} {t.line_short_name || t.line_name}{t.headsign ? ` (${t.headsign} 방면)` : ""}</Typography>
                                    <Typography variant="body2" color="text.secondary">
                                      {t.departure_stop} → {t.arrival_stop}{t.num_stops ? ` (${t.num_stops}개 정류장)` : ""} · ⏱️ {st.duration} · 📏 {st.distance}
                                    </Typography>
                                  </Paper>
                                );
                              }
                              if (st.travel_mode === "WALKING") {
                                return (
                                  <Paper key={j} sx={{ p: 1 }}>
                                    <Typography fontWeight={700} color="success.main">🚶 도보</Typography>
                                    <Typography variant="body2" color="text.secondary">{stripHTML(st.instruction || "")}</Typography>
                                    <Typography variant="body2" color="text.secondary">⏱️ {st.duration} · 📏 {st.distance}</Typography>
                                  </Paper>
                                );
                              }
                              return null;
                            })}
                          </Stack>
                        </Box>
                      )}
                    </Paper>
                  ))}
                  <Alert severity="success" sx={{ mt: 1 }}>
                    <strong>📊 총 거리:</strong> {totalDist.toFixed(1)}km &nbsp;|&nbsp;
                    <strong>⏱️ 총 소요시간:</strong> {Math.round(totalMins)}분 (약 {Math.round(totalMins / 60)}시간)
                  </Alert>
                </Box>
              </Box>
            )}
          </Box>
        </Grid>

        {/* 지도 */}
        <Grid item xs={12} md={8} lg={8}>
          <Box sx={{ position: "relative", bgcolor: "#e9ecef", height: mapFull ? "calc(100vh - 100px)" : { xs: 520, md: "calc(100vh - 180px)" }, transition: "height .2s ease" }}>
            <Box sx={{ p: 1.5, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <MapIcon />
                <Typography fontWeight={700}>지도</Typography>
                {!!routeData?.markers?.length && (
                  <Typography variant="body2" color="text.secondary">· 마커 {routeData.markers.length}개 / 구간 {routeData.segments?.length || 0}개</Typography>
                )}
              </Stack>
              <Stack direction="row" spacing={1}>
                <IconButton size="small" onClick={() => setMapFull((v) => !v)} title={mapFull ? "지도 축소" : "지도 크게 보기"}>
                  {mapFull ? <FullscreenExitIcon /> : <FullscreenIcon />}
                </IconButton>
                <IconButton size="small" onClick={() => (setRouteData(null), clearMap())} title="지도 지우기">
                  <CloseIcon />
                </IconButton>
              </Stack>
            </Box>
            <Divider />
            <Box ref={mapElRef} sx={{ width: "100%", height: "calc(100% - 56px)", borderRadius: 2, overflow: "hidden", bgcolor: "#e9ecef" }} />
            {!kakaoLoaded && !sdkError && (
              <Box sx={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Alert severity="info" icon={<CircularProgress size={14} />}>카카오맵 SDK 로딩 중…</Alert>
              </Box>
            )}
            {!!sdkError && (
              <Box sx={{ position: "absolute", top: 12, left: 12, right: 12 }}>
                <Alert severity="error" sx={{ whiteSpace: "pre-line" }}>{sdkError}</Alert>
              </Box>
            )}
          </Box>
        </Grid>
      </Grid>

      <Snackbar open={toast.open} autoHideDuration={2500} onClose={() => setToast({ ...toast, open: false })} message={toast.msg} />
    </Box>
  );
}
