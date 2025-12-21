// src/pages/TouristSpotRecommendPage.jsx (responsive-merged)
import React, { useState, useEffect, useRef, useCallback } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Box, Paper, Typography, Grid, Card, CardContent, CardMedia,
  Chip, Rating, Button, TextField, InputAdornment, Stack,
  Divider, IconButton, Alert, Skeleton, Accordion, AccordionSummary, AccordionDetails,
  Tooltip, useTheme, useMediaQuery
} from "@mui/material";
import {
  Search as SearchIcon,
  LocationOn as LocationOnIcon,
  Favorite as FavoriteIcon,
  FavoriteBorder as FavoriteBorderIcon,
  Share as ShareIcon,
  Museum as MuseumIcon,
  Refresh as RefreshIcon,
  Psychology as AIIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  PriorityHigh as PriorityHighIcon
} from "@mui/icons-material";
import { styled } from "@mui/material/styles";
import { useLoadScript } from "@react-google-maps/api";

// ---------- API ----------
const API_PREFIX =
  process.env.REACT_APP_API_PREFIX ||
  (typeof import.meta !== "undefined" && import.meta.env && import.meta.env.VITE_API_PREFIX) ||
  "http://localhost:8000";
const API_BASE = `${API_PREFIX.replace(/\/$/, "")}/api/v1`;

// ---------- 스타일 ----------
const StyledCard = styled(Card)(({ theme }) => ({
  height: "100%",
  transition: "all 0.3s ease",
  cursor: "pointer",
  "&:hover": { transform: "translateY(-4px)", boxShadow: theme.shadows[8] },
}));
const AIChip = styled(Chip)(({ theme }) => ({
  background: "linear-gradient(45deg, #6366F1, #06B6D4)",
  color: "white",
  fontWeight: "bold",
  "& .MuiChip-icon": { color: "white" },
}));
const SelectedCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(1.5),
  cursor: "default",
  borderRadius: 12,
  boxShadow: theme.shadows[1],
  transition: "box-shadow .2s ease",
  "&:hover": { boxShadow: theme.shadows[3] }
}));

// ---------- 유틸 ----------
const isPlaceholder = (url) => !url || url.includes("/api/placeholder");
const BUSAN_CENTER = { lat: 35.1796, lng: 129.0756 };

const toNum = (v) => {
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
};

const toMlPercent = (score) => {
  if (score == null) return null;
  const s = Number(score);
  if (!Number.isFinite(s)) return null;
  const pct = s <= 1 ? Math.round(s * 100) : Math.round(Math.min(s, 100));
  return pct > 0 ? pct : null; // 0%는 숨김
};

// ML 응답 한 항목을 공통 스키마로 정규화
const normalizeMlSpot = (p, i = 0) => {
  const id =
    p.item_id ?? p.content_id ?? p.id ?? p._id ?? String(p.ml_index ?? i + 1);
  return {
    id: String(id),
    name: p.item_name ?? p.name ?? "",
    address: p.address ?? p.road_address ?? "",
    lat: toNum(p.lat ?? p.latitude ?? p.y),
    lng: toNum(p.lng ?? p.longitude ?? p.x),
    category: p.category ?? p.category_type ?? "",
    category_type: p.category_type ?? p.categoryType ?? null,
    rating: typeof p.rating === "number" ? p.rating : null,
    image: p.photoUrl ?? p.image ?? "",
    ml_score: typeof p.score === "number" ? p.score : (p.ml_score ?? null),
    reason: p.reason ?? "",
    tags: p.tags ?? [],
    source: p.source ?? p.origin ?? "ml",
    reviews: p.reviews,
    distance: p.distance,
  };
};

// ML 추천 타입 칩 메타 (category_type 기준)
const ML_TYPE_META = {
  top_3: { label: "설문+AI 상위", color: "secondary" },
  ml_high: { label: "AI 추천", color: "primary" },
  developer: { label: "개발자 추천", color: "success" },
};
const getMlTypeMeta = (spot) => {
  const t = spot?.category_type || spot?.categoryType;
  return ML_TYPE_META[t] || null;
};

// ML 점수/플래그 유틸 (추가 사용)
const getMlScoreValue = (spot) => {
  const raw =
    spot?.ml_score ?? spot?.mlScore ?? spot?.score ??
    spot?.similarity ?? spot?.similarity_score ??
    spot?.relevance ?? spot?.model_score ??
    spot?.rankScore ?? spot?.rank ?? null;
  const num = Number(raw);
  return Number.isFinite(num) ? num : null;
};
const formatMlScore = (num) => {
  if (num == null) return null;
  if (num >= 0 && num <= 1) return `${Math.round(num * 100)}%`;
  return num.toFixed(1);
};
const isDevRecommended = (spot) => {
  const tags = (spot?.tags || []).map((t) => String(t));
  return Boolean(
    spot?.dev_recommended || spot?.curated ||
    spot?.source === "dev" || spot?.origin === "dev" ||
    tags.includes("개발자추천") || tags.includes("운영자추천") || tags.includes("추천")
  );
};

// (서버 wish API)
async function addWish({ user_id, place_id }) {
  const res = await fetch(`${API_BASE}/wish`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, place_id }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
async function removeWish({ user_id, place_id }) {
  const res = await fetch(`${API_BASE}/wish`, {
    method: "DELETE", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, place_id }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
async function getWishStatus({ user_id, place_id }) {
  const res = await fetch(
    `${API_BASE}/wish/status?user_id=${encodeURIComponent(user_id)}&place_id=${encodeURIComponent(place_id)}`
  );
  if (!res.ok) return { wished: false };
  const data = await res.json().catch(() => ({}));
  return { wished: Boolean(data.wished ?? data.is_wished ?? data.status ?? data.result) };
}

const categories = ["전체", "해변", "문화", "사찰", "시장", "자연", "전망", "체험"];

const TouristSpotRecommendPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const theme = useTheme();

  // 반응형 감지
  const isMobile = useMediaQuery(theme.breakpoints.down('sm')); // 600px 이하
  const isTablet = useMediaQuery(theme.breakpoints.down('md')); // 900px 이하

  const userId = location.state?.user_id || location.state?.userId || "";
  const initialAttractions = Array.isArray(location.state?.attractions)
    ? location.state.attractions
    : [];
  const fromMlList = location.state?.isMlList === true || location.state?.source === "ml";

  // Google Places
  const { isLoaded, loadError } = useLoadScript({
    googleMapsApiKey: process.env.REACT_APP_GOOGLE_MAPS_API_KEY || "",
    libraries: ["places"],
    language: "ko",
    region: "KR",
  });
  const placesDivRef = useRef(null);
  const placesServiceRef = useRef(null);
  const ensurePlacesService = () => {
    if (!placesServiceRef.current && window.google && placesDivRef.current) {
      placesServiceRef.current = new window.google.maps.places.PlacesService(placesDivRef.current);
    }
    return placesServiceRef.current;
  };

  // 상태
  const [loading, setLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("전체");
  const [touristSpots, setTouristSpots] = useState([]);
  const [selectedSpots, setSelectedSpots] = useState([]);
  const [expanded, setExpanded] = useState(false);
  const [photoMap, setPhotoMap] = useState({});
  const [wishSet, setWishSet] = useState(new Set()); // place_id Set

  // 초기 ML 20개 정규화 반영 (원본 로직 유지)
  useEffect(() => {
    const normalized = (initialAttractions || []).map((s, idx) => normalizeMlSpot(s, idx));
    setTouristSpots(normalized);
    setExpanded(normalized.length > 0);
  }, [initialAttractions]);

  // 위시 상태
  useEffect(() => {
    if (!userId || !touristSpots.length) return;
    let cancelled = false;
    (async () => {
      const results = await Promise.allSettled(
        touristSpots.map((s) => getWishStatus({ user_id: userId, place_id: String(s.id || s._id) }))
      );
      if (cancelled) return;
      const next = new Set();
      results.forEach((r, idx) => {
        if (r.status === "fulfilled" && r.value.wished) {
          const pid = String(touristSpots[idx].id || touristSpots[idx]._id);
          if (pid) next.add(pid);
        }
      });
      setWishSet(next);
    })();
    return () => { cancelled = true; };
  }, [userId, touristSpots]);

  // 사진 보강(Google)
  const setPhoto = useCallback((id, url) => {
    setPhotoMap((prev) => (prev[id] ? prev : { ...prev, [id]: url }));
  }, []);
  const fetchPhotoForName = useCallback(
    async (id, name) => {
      if (!isLoaded || !window.google) return;
      if (photoMap[id]) return;
      const svc = ensurePlacesService();
      if (!svc) return;

      const request = {
        query: `부산 ${name}`,
        location: new window.google.maps.LatLng(BUSAN_CENTER.lat, BUSAN_CENTER.lng),
        radius: 50000,
        language: "ko",
      };
      const place = await new Promise((resolve) => {
        svc.textSearch(request, (results) =>
          resolve(Array.isArray(results) && results.length ? results[0] : null)
        );
      });
      if (!place?.place_id) return;
      const detail = await new Promise((resolve) => {
        svc.getDetails({ placeId: place.place_id, language: "ko", fields: ["photos"] }, (d) => resolve(d || null));
      });
      const url = detail?.photos?.[0]?.getUrl({ maxWidth: 1200, maxHeight: 900 });
      if (url) setPhoto(id, url);
    },
    [isLoaded, photoMap, setPhoto]
  );
  useEffect(() => {
    if (!isLoaded) return;
    touristSpots.slice(0, 24).forEach((s) => {
      const id = String(s.id || s._id);
      if (!id) return;
      if (isPlaceholder(s.image)) fetchPhotoForName(id, s.name);
    });
  }, [isLoaded, touristSpots, fetchPhotoForName]);

  // 새 추천(샘플)
  const fetchRecommendations = async () => {
    setLoading(true);
    try {
      await new Promise((r) => setTimeout(r, 800));
    } finally {
      setLoading(false);
    }
  };

  // 위시 토글
  const toggleWish = async (spot) => {
    if (!userId) return alert("로그인이 필요합니다.");
    const place_id = String(spot.id || spot._id);
    if (!place_id) return;
    const isWished = wishSet.has(place_id);
    setWishSet((prev) => {
      const n = new Set(prev);
      isWished ? n.delete(place_id) : n.add(place_id);
      return n;
    });
    try {
      if (isWished) await removeWish({ user_id: userId, place_id });
      else await addWish({ user_id: userId, place_id });
    } catch {
      setWishSet((prev) => {
        const n = new Set(prev);
        isWished ? n.add(place_id) : n.delete(place_id);
        return n;
      });
      alert("위시 처리 실패");
    }
  };

  // 일정 담기
  const addToSelectedSpots = (spot) => {
    const id = String(spot.id || spot._id);
    if (!id) return;
    if (!selectedSpots.some((s) => String(s.id) === id)) {
      const googlePhoto = photoMap[id];
      const compact = {
        id,
        name: spot.name,
        backendId: id,
        image: googlePhoto && !isPlaceholder(googlePhoto) ? googlePhoto : spot.image,
        category: spot.category,
        rating: spot.rating,
        reviews: spot.reviews,
        address: spot.address,
        tags: spot.tags?.slice(0, 3) || [],
        distance: spot.distance,
        lat: spot.lat,
        lng: spot.lng,
        ml_score: spot.ml_score ?? spot.mlScore ?? spot.score ?? null,
        source: spot.source || spot.origin || (fromMlList ? "ml" : null),
        dev_recommended: spot.dev_recommended || spot.curated || false,
      };
      setSelectedSpots((prev) => [...prev, compact]);
      if (!expanded) setExpanded(true);
    }
  };
  const removeFromSelectedSpots = (spotId) => {
    setSelectedSpots((prev) => prev.filter((s) => String(s.id) !== String(spotId)));
  };
  const clearSelected = () => setSelectedSpots([]);

  // 필터
  const filteredSpots = touristSpots.filter((spot) => {
    const q = searchTerm.trim().toLowerCase();
    const matchesSearch =
      q === "" ||
      (spot.name || "").toLowerCase().includes(q) ||
      (spot.tags || []).some((tag) => (tag || "").toLowerCase().includes(q));
    const matchesCategory = selectedCategory === "전체" || spot.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  // 스켈레톤
  const SpotSkeleton = () => (
    <Grid item xs={12} md={6} key="skeleton">
      <Card>
        <Skeleton variant="rectangular" height={200} />
        <CardContent>
          <Skeleton variant="text" width="60%" height={28} />
          <Skeleton variant="text" width="40%" height={20} sx={{ mb: 1 }} />
          <Skeleton variant="text" width="100%" height={16} />
          <Skeleton variant="text" width="100%" height={16} />
          <Skeleton variant="text" width="80%" height={16} sx={{ mb: 2 }} />
          <Stack direction="row" spacing={1}>
            <Skeleton variant="rectangular" width={60} height={24} sx={{ borderRadius: 3 }} />
            <Skeleton variant="rectangular" width={80} height={24} sx={{ borderRadius: 3 }} />
            <Skeleton variant="rectangular" width={70} height={24} sx={{ borderRadius: 3 }} />
          </Stack>
        </CardContent>
      </Card>
    </Grid>
  );

  const goMakeCourse = () => {
    // ✅ 선택된 spot에는 id와 name이 반드시 들어가야 함 (원본 로직 유지: Kakao 버전)
    const sanitized = selectedSpots
      .filter(s => s?.id)
      .map(s => ({ id: String(s.id), name: s.name, address: s.address, lat: s.lat, lng: s.lng }));
    navigate("/travel-plan-kakao", {
      state: { user_id: userId, spots: sanitized }
    });
  };

  return (
    <Box sx={{ 
      // 반응형 웹 전용 설정 (모바일/태블릿: xs, sm)
      width: { xs: '100%', md: '100%' },
      maxWidth: { xs: '96vw', md: '100vw' },
      margin: { xs: 0, md: "0 auto" }, 
      p: { xs: 1, sm: 2, md: 3 }, 
      pt: { xs: 9, sm: 12, md: 16, lg: 20 }, 
      display: "flex", 
      flexDirection: { xs: "column", lg: "row" },
      gap: { xs: 1.5, sm: 2, md: 3 }, 
      alignItems: "flex-start",
      minHeight: { xs: '100vh', lg: 'auto' },
      overflowX: { xs: 'hidden', md: 'hidden' },
      overflowY: 'auto',
      backgroundColor: '#fafafa',
      position: 'relative',
      boxSizing: 'border-box'
    }}>
      {/* Left */}
      <Box sx={{ flex: { xs: 1, lg: 3 }, width: { xs: '100%', lg: 'auto' } }}>
        <Paper sx={{ 
          p: { xs: 1.5, sm: 2, md: 3 }, 
          mb: { xs: 1.5, sm: 2, md: 3 }, 
          borderRadius: { xs: 1.5, sm: 2 }, 
          position: "relative" 
        }}>
          <Box sx={{ 
            display: "flex", 
            flexDirection: { xs: "column", sm: "row" }, 
            alignItems: { xs: "flex-start", sm: "center" }, 
            mb: { xs: 1.5, sm: 2 }, 
            gap: { xs: 1.5, sm: 0 } 
          }}>
            <AIIcon sx={{ 
              fontSize: { xs: 24, sm: 28, md: 32 }, 
              color: "#6366F1", 
              mr: { xs: 0, sm: 2 } 
            }} />
            <Box sx={{ flex: 1 }}>
              <Typography 
                variant="h4" 
                sx={{ 
                  fontSize: { xs: "1.25rem", sm: "1.75rem", md: "2rem" }, 
                  fontWeight: 600, 
                  mb: { xs: 0.5, sm: 1 } 
                }}
              >
                AI 추천 관광지
              </Typography>
              <Typography 
                variant="body1" 
                sx={{ 
                  fontSize: { xs: "0.75rem", sm: "0.875rem", md: "1rem" },
                  display: { xs: 'none', sm: 'block' }
                }} 
                color="text.secondary"
              >
                AI 결과로 받은 부산 관광지 20곳
              </Typography>
            </Box>
            <Button 
              variant="outlined" 
              startIcon={<RefreshIcon sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }} />} 
              onClick={fetchRecommendations} 
              disabled={loading}
              size={isMobile ? "small" : "medium"}
              fullWidth={isMobile}
              sx={{ 
                fontSize: { xs: '0.75rem', sm: '0.875rem' }, 
                py: { xs: 0.75, sm: 1 },
                minWidth: { xs: '100%', sm: 'auto' }
              }}
            >
              새로고침
            </Button>
          </Box>

          <AIChip 
            icon={<AIIcon />} 
            label={`AI 분석 완료 - ${touristSpots.length}곳`} 
            sx={{ 
              mb: { xs: 1.5, sm: 2, md: 3 }, 
              fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.875rem' },
              height: { xs: '24px', sm: '28px', md: '32px' }
            }} 
          />

          {/* Search */}
          <Stack 
            direction={{ xs: "column", sm: "row" }} 
            spacing={{ xs: 1.5, sm: 2 }} 
            sx={{ mb: { xs: 1.5, sm: 2, md: 3 } }}
          >
            <TextField
              placeholder="관광지명 또는 태그로 검색..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              size={isMobile ? "small" : "medium"}
              InputProps={{ 
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon sx={{ fontSize: { xs: '1rem', sm: '1.25rem' } }} />
                  </InputAdornment>
                ) 
              }}
              sx={{ 
                flex: 1,
                '& .MuiInputBase-input': {
                  fontSize: { xs: '0.85rem', sm: '0.95rem', md: '1rem' }
                }
              }}
            />
          </Stack>

          {/* Filter */}
          <Stack 
            direction="row" 
            spacing={1} 
            sx={{ 
              flexWrap: "wrap", 
              gap: { xs: 0.75, sm: 1 },
              mb: { xs: 1, sm: 0 }
            }}
          >
            {categories.map((category) => (
              <Chip
                key={category}
                label={category}
                onClick={() => setSelectedCategory(category)}
                variant={selectedCategory === category ? "filled" : "outlined"}
                color={selectedCategory === category ? "primary" : "default"}
                size={isMobile ? "small" : "medium"}
                sx={{ 
                  fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.875rem' }, 
                  height: { xs: '24px', sm: '28px', md: '32px' },
                  px: { xs: 1, sm: 1.5 }
                }}
              />
            ))}
          </Stack>

          {/* 🔔 안내 툴팁 */}
          {/* 🔔 안내 툴팁 */}
<Tooltip
  arrow
  placement={isMobile ? "top" : "left"}
  componentsProps={{
    tooltip: {
      sx: {
        maxWidth: 520,
        p: 2,
        bgcolor: "rgba(17, 24, 39, 0.98)",            // 거의 불투명한 어두운 배경
        color: "rgba(255,255,255,0.95)",               // 본문 글씨 색
        border: "1px solid rgba(255,255,255,0.12)",    // 얇은 윤곽선
        boxShadow: 8,                                  // 그림자 진하게
        "& .MuiTypography-subtitle1": { color: "#fff" },
        "& .MuiTypography-body2": { color: "rgba(255,255,255,0.88)" },
        "& .MuiChip-root": {
          borderColor: "rgba(255,255,255,0.18)"
        }
      }
    },
    arrow: {
      sx: { color: "rgba(17, 24, 39, 0.98)" }
    }
  }}
  title={
    <Box sx={{ lineHeight: 1.7 }}>
      {/* 상위 3개 추천 */}
      <Typography
        variant="subtitle1"
        fontWeight={800}
        sx={{ fontSize: { xs: '0.9rem', sm: '1rem', md: '1.05rem' }, mb: 0.5 }}
      >
        📌 상위 3개 추천
      </Typography>
      <Typography
        variant="body2"
        sx={{
          fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' },
          mb: 1.75
        }}
      >
        사용자의 초기 설문조사와 라운드별 피드백이 모두 일치하는 최적 매칭 관광지입니다.
        개인 선호도와 실제 반응을 종합 분석한 고정확도 추천 결과입니다.
      </Typography>

      {/* 개발자 추천 (제목 + 진짜 칩) */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
        <Typography
          variant="subtitle1"
          fontWeight={800}
          sx={{ fontSize: { xs: '0.9rem', sm: '1rem', md: '1.05rem' } }}
        >
          🧑‍💻 개발자 추천
        </Typography>
      </Box>

      <Typography
        variant="body2"
        sx={{
          fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' },
          mb: 0.75
        }}
      >
        <Chip
          size="small"
          label="개발자 추천"
          color="success"
          sx={{ color: '#fff', fontSize: '0.6rem', height: '20px', ml: 0.25 }}
        />{' '}
        태그는 개인 취향뿐만 아니라 사회적 가치를 고려한 특별 추천입니다.
      </Typography>

      <Box component="ul" sx={{ pl: 2.25, mb: 1.75 }}>
        <li>
          <Typography
            variant="body2"
            sx={{
              fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' }
            }}
          >
            오버투어리즘 해소: 과밀 관광지에 편향을 분산하고자 하는 목적
          </Typography>
        </li>
        <li>
          <Typography
            variant="body2"
            sx={{
              fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' }
            }}
          >
            지역경제 균형: 관광 수익이 편중되지 않으면서 경제 침체 해결
          </Typography>
        </li>
        <li>
          <Typography
            variant="body2"
            sx={{
              fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' }
            }}
          >
            개발자 추천이라는 태그에서 여러 관광지 여행 유도
          </Typography>
        </li>
      </Box>

      {/* 기타 추천 */}
      <Typography
        variant="subtitle1"
        fontWeight={800}
        sx={{
          fontSize: { xs: '0.9rem', sm: '1rem', md: '1.05rem' },
          mb: 0.5
        }}
      >
        🧭 기타 추천
      </Typography>
      <Typography
        variant="body2"
        sx={{
          fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' },
          mb: 1.75
        }}
      >
        사용자와 유사한 취향을 가진 다른 사용자들의 방문 패턴을 분석하여 도출한 협업 필터링 기반 추천 결과입니다.
      </Typography>

      <Typography
        variant="body2"
        fontWeight={700}
        sx={{
          fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' },
          color: 'primary.main'
        }}
      >
        여러분들의 개발자 추천 관광지의 관심은 부산 관광 산업 문제 해결에 기여됩니다!
      </Typography>
    </Box>
  }
>
  <IconButton
    size="small"
    sx={{
      position: 'absolute',
      bottom: { xs: 8, sm: 12 },
      right: { xs: 8, sm: 12 },
      bgcolor: 'rgba(255,255,255,0.98)',
      boxShadow: 1,
      width: { xs: 28, sm: 32, md: 36 },
      height: { xs: 28, sm: 32, md: 36 },
      '&:hover': { bgcolor: '#fff' }
    }}
    aria-label="도움말"
  >
    <PriorityHighIcon
      sx={{ fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' } }}
    />
  </IconButton>
</Tooltip>


        </Paper>

        {loading && (
          <Grid container spacing={{ xs: 1.5, sm: 2, md: 3 }}>
            {[...Array(4)].map((_, i) => (<SpotSkeleton key={i} />))}
          </Grid>
        )}

        {!loading && (
          <Grid container spacing={{ xs: 1.5, sm: 2, md: 3 }}>
            {filteredSpots.map((spot) => {
              const id = String(spot.id || spot._id);
              const isSel = selectedSpots.some((s) => String(s.id) === id);
              const googlePhoto = photoMap[id];
              const finalImage = googlePhoto && !isPlaceholder(googlePhoto) ? googlePhoto : spot.image;

              const mlScore = getMlScoreValue(spot);
              const mlPct = toMlPercent(mlScore);
              const isDeveloper = (spot.category_type ?? spot.categoryType) === 'developer';
              const showMlBadge = (mlPct != null) && !isDeveloper; // 개발자 추천일 때는 ML 배지 숨김
              const meta = getMlTypeMeta(spot); // category_type 우선
              const showDev = isDevRecommended(spot);

              return (
                <Grid item xs={12} sm={6} md={6} lg={4} key={id}>
                  <StyledCard
                    sx={{
                      border: isSel ? "2px solid #6366F1" : "none",
                      boxShadow: isSel ? (theme) => theme.shadows[8] : undefined,
                      backgroundColor: isSel ? "rgba(99, 102, 241, 0.06)" : "white",
                    }}
                  >
                    <Box sx={{ position: "relative", height: { xs: 180, sm: 200, md: 220 } }}>
                      {finalImage && !isPlaceholder(finalImage) ? (
                        <CardMedia component="img" image={finalImage} alt={spot.name} sx={{ height: "100%", width: "100%", objectFit: "cover" }} />
                      ) : (
                        <CardMedia
                          component="div"
                          sx={{ height: "100%", backgroundColor: "#eef3ff", display: "flex", justifyContent: "center", alignItems: "center" }}
                        >
                          <MuseumIcon sx={{ fontSize: 60, color: "#666" }} />
                        </CardMedia>
                      )}

                      {/* ML 점수 - 좌상단 */}
                      {showMlBadge && (
                        <Chip
                          label={`AI ${mlPct}%`}
                          size="small"
                          color="primary"
                          sx={{ position: "absolute", top: 8, left: 8, bgcolor: "rgba(99,102,241,0.95)", color: "#fff", fontWeight: 700 }}
                        />
                      )}

                      {/* 위시 버튼 - 우상단 */}
                      <IconButton
                        sx={{ position: "absolute", top: 8, right: 8, backgroundColor: "rgba(255,255,255,0.9)" }}
                        onClick={() => toggleWish(spot)}
                        aria-label={wishSet.has(id) ? "찜 해제" : "찜 추가"}
                      >
                        {wishSet.has(id) ? <FavoriteIcon sx={{ color: "#FF6B6B" }} /> : <FavoriteBorderIcon />}
                      </IconButton>
                    </Box>

                    <CardContent sx={{ p: { xs: 1.5, sm: 2 } }}>
                      {/* 제목 */}
                      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", mb: 1 }}>
                        <Typography 
                          variant="h6" 
                          sx={{ fontWeight: 600, fontSize: { xs: '1rem', sm: '1.1rem', md: '1.25rem' } }}
                        >
                          {spot.name}
                        </Typography>
                        <IconButton size="small">
                          <ShareIcon sx={{ fontSize: { xs: '1rem', sm: '1.1rem' } }} />
                        </IconButton>
                      </Box>

                      {/* 주소/거리 */}
                      <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
                        <LocationOnIcon 
                          fontSize="small" 
                          color="action" 
                          sx={{ mr: 0.5, fontSize: { xs: '1rem', sm: '1.1rem' } }} 
                        />
                        <Typography 
                          variant="body2" 
                          color="text.secondary"
                          sx={{ fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' } }}
                        >
                          {(spot.address || "").split(" ").slice(0, 3).join(" ")}
                          {spot.distance ? ` · ${spot.distance}` : ""}
                        </Typography>
                      </Box>

                      {/* 평점 */}
                      {typeof spot.rating === "number" && (
                        <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                          <Rating value={spot.rating} precision={0.1} size={isMobile ? "small" : "medium"} readOnly />
                          <Typography variant="body2" sx={{ ml: 1, fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' } }}>{spot.rating}</Typography>
                        </Box>
                      )}

                      {/* 설명 */}
                      {spot.description && (
                        <Typography 
                          variant="body2" 
                          color="text.secondary" 
                          sx={{ 
                            mb: 2, lineHeight: 1.6,
                            fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' },
                            display: { xs: '-webkit-box', sm: 'block' },
                            WebkitLineClamp: { xs: 2, sm: 3 },
                            WebkitBoxOrient: 'vertical',
                            overflow: 'hidden'
                          }}
                        >
                          {spot.description}
                        </Typography>
                      )}

                      {/* 추천 출처 Chip + 태그 */}
                      <Box sx={{ display: "flex", flexWrap: "wrap", gap: { xs: 0.5, sm: 0.75 }, mb: 2 }}>
                        {meta ? (
                          <Chip size="small" label={meta.label} color={meta.color} sx={{ color: "#fff", fontSize: { xs: '0.65rem', sm: '0.75rem' }, height: { xs: '20px', sm: '24px' } }} />
                        ) : (
                          <>
                            {showMlBadge && (
                              <Chip size="small" label="AI 추천" color="primary" sx={{ color: "#fff", fontSize: { xs: '0.65rem', sm: '0.75rem' }, height: { xs: '20px', sm: '24px' } }} />
                            )}
                            {isDevRecommended(spot) && (
                              <Chip size="small" label="개발자 추천" color="success" sx={{ color: "#fff", fontSize: { xs: '0.65rem', sm: '0.75rem' }, height: { xs: '20px', sm: '24px' } }} />
                            )}
                          </>
                        )}
                        {(spot.tags || []).slice(0, 3).map((tag, i) => (
                          <Chip 
                            key={i} 
                            label={tag} 
                            size="small" 
                            variant="outlined"
                            sx={{ fontSize: { xs: '0.65rem', sm: '0.75rem' }, height: { xs: '20px', sm: '24px' } }}
                          />
                        ))}
                      </Box>

                      <Divider sx={{ my: { xs: 1.5, sm: 2 } }} />

                      {/* 하단 액션 */}
                      <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <Chip 
                          label={spot.category || "미분류"} 
                          size="small" 
                          sx={{ backgroundColor: "#f0f0f0", color: "#666", fontSize: { xs: '0.7rem', sm: '0.75rem' }, height: { xs: '24px', sm: '28px' } }} 
                        />
                        <Button 
                          variant="contained" 
                          size={isMobile ? "small" : "medium"}
                          onClick={() => addToSelectedSpots(spot)} 
                          disabled={isSel}
                          sx={{ fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.875rem' }, py: { xs: 0.5, sm: 0.75 }, px: { xs: 1, sm: 1.5 } }}
                        >
                          {isSel ? "추가됨" : "일정에 추가"}
                        </Button>
                      </Box>
                    </CardContent>
                  </StyledCard>
                </Grid>
              );
            })}
          </Grid>
        )}

        {!loading && filteredSpots.length === 0 && touristSpots.length > 0 && (
          <Paper sx={{ p: { xs: 2, sm: 3, md: 4 }, textAlign: "center", mt: { xs: 2, sm: 3 } }}>
            <MuseumIcon sx={{ fontSize: { xs: 48, sm: 56, md: 60 }, color: "#ccc", mb: { xs: 1.5, sm: 2 } }} />
            <Typography variant="h6" color="text.secondary" sx={{ fontSize: { xs: '1rem', sm: '1.15rem', md: '1.25rem' } }}>
              검색 결과가 없습니다
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem', md: '0.95rem' } }}>
              다른 검색어나 카테고리를 선택해보세요
            </Typography>
          </Paper>
        )}

        {!loading && touristSpots.length === 0 && (
          <Alert 
            severity="error" 
            action={
              <Button color="inherit" size="small" onClick={fetchRecommendations} sx={{ fontSize: { xs: '0.7rem', sm: '0.8rem' } }}>
                다시 시도
              </Button>
            }
            sx={{ fontSize: { xs: '0.8rem', sm: '0.9rem', md: '1rem' } }}
          >
            추천 데이터를 불러오지 못했습니다.
          </Alert>
        )}
      </Box>

      {/* Right: 담은 관광지 리스트 */}
      <Accordion
        expanded={expanded}
        onChange={() => setExpanded((prev) => !prev)}
        disableGutters elevation={0}
        sx={{
          width: { xs: '100%', lg: 460 }, 
          minWidth: { xs: 'auto', lg: 400 },
          border: selectedSpots.length === 0 ? "none" : "1px solid #ddd",
          borderRadius: 2,
          backgroundColor: selectedSpots.length === 0 ? "transparent" : "#fafafa",
          boxShadow: "none",
          alignSelf: "flex-start",
          position: { xs: 'relative', lg: 'sticky' }, 
          top: { xs: 0, lg: 80 },
          maxHeight: { xs: 'none', lg: 'calc(100vh - 100px)' },
          overflowY: { xs: 'visible', lg: 'auto' }, 
          zIndex: 10,
        }}
      >
        <AccordionSummary 
          expandIcon={<ExpandMoreIcon sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }} />} 
          sx={{ px: { xs: 1.5, sm: 2 }, py: { xs: 1.25, sm: 1.5 } }}
        >
          <Box sx={{ display: "flex", flexDirection: { xs: 'column', sm: 'row' }, alignItems: { xs: 'stretch', sm: 'center' }, gap: { xs: 1, sm: 1 }, width: "100%" }}>
            <Typography variant="h6" sx={{ fontSize: { xs: '1rem', sm: '1.15rem', md: '1.25rem' }, fontWeight: 700, flex: 1 }}>
              담은 관광지 ({selectedSpots.length})
            </Typography>
            <Box sx={{ display: 'flex', gap: { xs: 0.75, sm: 1 } }}>
              <Button
                size={isMobile ? "small" : "medium"}
                variant="outlined"
                color="error"
                onClick={(e) => { e.stopPropagation(); clearSelected(); }}
                disabled={selectedSpots.length === 0}
                sx={{ flex: { xs: 1, sm: 'auto' }, fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.875rem' }, py: { xs: 0.5, sm: 0.75 } }}
              >
                전체 비우기
              </Button>
              <Button
                size={isMobile ? "small" : "medium"}
                variant="contained"
                onClick={(e) => { e.stopPropagation(); goMakeCourse(); }}
                disabled={selectedSpots.length === 0}
                sx={{ flex: { xs: 1, sm: 'auto' }, fontSize: { xs: '0.7rem', sm: '0.8rem', md: '0.875rem' }, py: { xs: 0.5, sm: 0.75 } }}
              >
                코스 짜기
              </Button>
            </Box>
          </Box>
        </AccordionSummary>

        <AccordionDetails sx={{ px: { xs: 1.5, sm: 2 }, pt: 0, pb: { xs: 1.5, sm: 2 } }}>
          {selectedSpots.length === 0 ? (
            <Paper variant="outlined" sx={{ p: { xs: 1.5, sm: 2 }, textAlign: "center", borderRadius: { xs: 1.5, sm: 2 } }}>
              <Typography variant="body2" color="text.secondary" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem', md: '0.95rem' } }}>
                마음에 드는 관광지를 <b>일정에 추가</b>해 보세요!
              </Typography>
            </Paper>
          ) : (
            selectedSpots.map((spot) => {
              const id = String(spot.id);
              const googlePhoto = photoMap[id];
              const finalImage = googlePhoto && !isPlaceholder(googlePhoto) ? googlePhoto : spot.image;

              return (
                <SelectedCard key={id}>
                  <CardContent sx={{ p: { xs: 1.25, sm: 1.5 } }}>
                    <Box sx={{ display: "flex", alignItems: "center", gap: { xs: 1, sm: 1.5 } }}>
                      {/* 썸네일 */}
                      <Box sx={{ width: { xs: 90, sm: 100, md: 112 }, height: { xs: 68, sm: 75, md: 84 }, borderRadius: 1.2, overflow: "hidden", flex: "0 0 auto", bgcolor: "#eef3ff", position: "relative" }}>
                        {finalImage && !isPlaceholder(finalImage) ? (
                          <CardMedia component="img" image={finalImage} alt={spot.name} sx={{ width: "100%", height: "100%", objectFit: "cover" }} />
                        ) : (
                          <Box sx={{ width: "100%", height: "100%", display: "flex", alignItems: "center", justifyContent: "center" }}>
                            <MuseumIcon sx={{ fontSize: 38, color: "#9aa5b1" }} />
                          </Box>
                        )}
                      </Box>

                      {/* 본문 */}
                      <Box sx={{ flex: 1, minWidth: 0 }}>
                        <Box sx={{ display: "flex", alignItems: "flex-start", gap: { xs: 0.75, sm: 1 }, mb: 0.25, flexWrap: "wrap" }}>
                          <Typography
                            variant="subtitle1"
                            sx={{ fontWeight: 700, lineHeight: 1.2, fontSize: { xs: '0.85rem', sm: '0.95rem', md: '1rem' }, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden", wordBreak: "keep-all" }}
                            title={spot.name}
                          >
                            {spot.name}
                          </Typography>
                          <Chip size="small" label={spot.category || "미분류"} sx={{ bgcolor: "#f2f2f2", color: "#666", fontSize: { xs: '0.65rem', sm: '0.7rem' }, height: { xs: '20px', sm: '24px' } }} />
                        </Box>

                        {typeof spot.rating === "number" && (
                          <Stack direction="row" spacing={{ xs: 0.75, sm: 1 }} alignItems="center" sx={{ mt: 0.25 }}>
                            <Rating value={spot.rating} precision={0.1} size="small" readOnly sx={{ fontSize: { xs: '0.9rem', sm: '1rem' } }} />
                            <Typography variant="caption" sx={{ fontSize: { xs: '0.7rem', sm: '0.75rem' } }}>
                              {spot.rating}
                            </Typography>
                          </Stack>
                        )}

                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.25, display: "block", wordBreak: "keep-all", whiteSpace: "normal", fontSize: { xs: '0.7rem', sm: '0.75rem' }, lineHeight: 1.3 }} title={spot.address}>
                          {spot.address}
                        </Typography>
                      </Box>

                      {/* 액션 */}
                      <IconButton color="error" onClick={() => removeFromSelectedSpots(id)} size="small" sx={{ ml: { xs: 0, sm: 0.5 }, width: { xs: 32, sm: 36 }, height: { xs: 32, sm: 36 } }} aria-label={`${spot.name} 제거`}>
                        <DeleteIcon sx={{ fontSize: { xs: '1rem', sm: '1.1rem' } }} />
                      </IconButton>
                    </Box>
                  </CardContent>
                </SelectedCard>
              );
            })
          )}

        </AccordionDetails>
      </Accordion>

      {/* PlacesService 더미 */}
      <div ref={placesDivRef} style={{ width: 0, height: 0, overflow: "hidden", position: "absolute" }} />
      {loadError && (
        <Alert severity="error" sx={{ position: "fixed", bottom: { xs: 12, sm: 16 }, right: { xs: 12, sm: 16 }, left: { xs: 12, sm: 'auto' }, maxWidth: { xs: 'calc(100vw - 24px)', sm: '400px' }, fontSize: { xs: '0.8rem', sm: '0.9rem', md: '1rem' } }}>
          Google Maps/Places 로딩 오류: API 키와 권한을 확인하세요.
        </Alert>
      )}
    </Box>
  );
};

export default TouristSpotRecommendPage;
