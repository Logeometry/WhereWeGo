/* global google */

// src/pages/SurveyPage.jsx
import React, { useEffect, useState, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { Loader } from "@googlemaps/js-api-loader";
import {
  Alert, Box, Button, ButtonGroup, Card, CardActions, CardContent, CardHeader,
  Chip, CircularProgress, LinearProgress, Container, Divider, FormControl, Grid,
  IconButton, InputLabel, MenuItem, Select, Snackbar,
  Stack, Stepper, Step, StepLabel, Tooltip, Typography,
  Skeleton, Badge, MobileStepper, Paper, useMediaQuery
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import LoginIcon from "@mui/icons-material/Login";
import GoogleIcon from "@mui/icons-material/Google";
import ChatBubbleIcon from "@mui/icons-material/ChatBubble";
import HowToVoteIcon from "@mui/icons-material/HowToVote";
import LogoutIcon from "@mui/icons-material/Logout";
import CheckCircleIcon from "@mui/icons-material/CheckCircle";
import ErrorIcon from "@mui/icons-material/Error";
import ScienceIcon from "@mui/icons-material/Science";
import SendIcon from "@mui/icons-material/Send";
import ChecklistIcon from "@mui/icons-material/Checklist";
import PendingIcon from "@mui/icons-material/Pending";
import PlaceIcon from "@mui/icons-material/Place";
import { Search as SearchIcon, ArrowBack, ArrowForward } from "@mui/icons-material";
import { AnimatePresence, motion } from "framer-motion";

// UA 기반 감지
import { isMobile as isMobileUA, isAndroid, isIOS } from "react-device-detect";

/* ==========================================================================
   환경 변수 / 상수
   ========================================================================== */
const API_PREFIX =
  process.env.REACT_APP_API_PREFIX ||
  (typeof import.meta !== "undefined" &&
    import.meta.env &&
    import.meta.env.VITE_API_PREFIX) ||
  "http://localhost:8000";
const API_BASE = `${API_PREFIX.replace(/\/$/, "")}/api/v1`;
const GOOGLE_LOGIN_URL = `${API_BASE}/auth/google/login`;
const KAKAO_LOGIN_URL = `${API_BASE}/auth/kakao/login`;
const GMAPS_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY || "";

// 로컬 관리자 우회 플래그 키
const BYPASS_KEY = "wwg_admin_bypass";

/* ==========================================================================
   팔레트
   ========================================================================== */
const tone = {
  primary: "#4338CA",
  primarySoft: "#EEF2FF",
  accent: "#0D9488",
  paper: "#ffffff",
  subtle: "#F7F7FB",
  border: "#E6E8EF",
  cardGrad: "linear-gradient(135deg, #F9FAFB 0%, #EEF2FF 40%, #ECFEFF 100%)",
};

/* ==========================================================================
   유틸
   ========================================================================== */
const toNum = (v) => {
  const n = Number(v);
  return Number.isFinite(n) ? n : null;
};

const normalizeMlSpot = (p, i = 0) => {
  const primaryId = p?.item_id || p?._id || p?.content_id || p?.id || p?.ml_index || (i + 1);
  return {
    id: String(primaryId),
    item_id: p?.item_id ? String(p.item_id) : undefined,
    _id: p?._id ? String(p._id) : undefined,
    name: p?.item_name || p?.name || "(이름 없음)",
    category_type: p?.category_type ?? p?.categoryType ?? null,
    address: p?.address || p?.road_address || "",
    lat: toNum(p?.lat ?? p?.latitude ?? p?.y),
    lng: toNum(p?.lng ?? p?.longitude ?? p?.x),
    category: p?.category || p?.category_type || "",
    rating: typeof p?.rating === "number" ? p.rating : null,
    image:
      p?.photoUrl ||
      p?.image ||
      (p?.photo_reference
        ? `https://maps.googleapis.com/maps/api/place/photo?maxwidth=1200&photo_reference=${encodeURIComponent(
          p.photo_reference
        )}&key=${GMAPS_KEY}`
        : PLACEHOLDER_URL),
    ml_score: typeof p?.score === "number" ? p.score : null,
    reason: p?.reason || "",
    source: "ml",
  };
};

async function apiCall(url, options = {}) {
  const body = options.body ? JSON.stringify(options.body) : undefined;
  const res = await fetch(url, {
    method: options.method || "GET",
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(options.headers || {}),
    },
    body,
  });
  if (res.status === 204) return {};
  if (!res.ok) {
    let errDetail = `HTTP ${res.status}`;
    try {
      const err = await res.json();
      errDetail = err.detail || err.message || errDetail;
    } catch { }
    throw new Error(errDetail);
  }
  try {
    return await res.json();
  } catch {
    return {};
  }
}

/* ==========================================================================
   이미지 헬퍼
   ========================================================================== */
const PLACEHOLDER_SVG = `
<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='675' viewBox='0 0 1200 675'>
  <defs>
    <linearGradient id='g' x1='0' x2='1' y1='0' y2='1'>
      <stop offset='0%' stop-color='#eef2f7'/>
      <stop offset='100%' stop-color='#e5ecf5'/>
    </linearGradient>
  </defs>
  <rect width='1200' height='675' fill='url(#g)'/>
  <g fill='none' stroke='#9aa4b2' stroke-width='28' stroke-linecap='round' stroke-linejoin='round'>
    <rect x='170' y='140' width='860' height='460' rx='32'/>
    <circle cx='410' cy='340' r='70'/>
    <path d='M220 570l230-230 150 150 140-190 240 270z'/>
  </g>
</svg>`;
const PLACEHOLDER_URL = `data:image/svg+xml;utf8,${encodeURIComponent(PLACEHOLDER_SVG)}`;

function extractPhotoUrl(place) {
  const first = (arr) => (Array.isArray(arr) && arr.length ? arr[0] : null);
  const candidates = [
    place?.photoUrl, place?.image, place?.thumbnail, place?.coverImage, place?.cover,
    place?.img, place?.picture, place?.mainImage, first(place?.images), first(place?.image_urls),
    place?.photo_url, place?.img_url, place?.image_url, first(place?.photos)?.url || first(place?.photos)?.photoUrl,
  ].filter(Boolean);
  if (candidates.length) return candidates[0];

  const photoRef =
    place?.photo_reference ||
    place?.photoReference ||
    (first(place?.photos)?.photo_reference ?? first(place?.photos)?.photoReference);
  if (photoRef && GMAPS_KEY) {
    return `https://maps.googleapis.com/maps/api/place/photo?maxwidth=1200&photo_reference=${encodeURIComponent(
      photoRef
    )}&key=${GMAPS_KEY}`;
  }
  return "";
}

/* ==========================================================================
   Google Places: 라운드 카드 이미지 보강
   ========================================================================== */
async function augmentRoundImages(rounds) {
  if (!GMAPS_KEY) return rounds;

  const loader = new Loader({
    apiKey: GMAPS_KEY,
    libraries: ["places"],
    region: "KR",
    language: "ko",
  });
  await loader.load();

  const mapDiv = document.createElement("div");
  const service = new window.google.maps.places.PlacesService(mapDiv);
  const BUSAN_CENTER = { lat: 35.1796, lng: 129.0756 };

  const next = rounds.map((r) => ({
    ...r,
    primary: r.primary ? { ...r.primary } : null,
    alternative: r.alternative ? { ...r.alternative } : null,
  }));

  const fillPhoto = async (spot) => {
    if (!spot) return;
    const already =
      spot.image &&
      !/^data:image/i.test(spot.image) &&
      !/placeholder/i.test(spot.image);
    if (already) return;

    const q = (spot.name || "").trim();
    if (!q) return;

    const place = await new Promise((resolve) => {
      service.textSearch(
        {
          query: `부산 ${q}`,
          location: new window.google.maps.LatLng(BUSAN_CENTER.lat, BUSAN_CENTER.lng),
          radius: 50000,
          language: "ko",
        },
        (results) => resolve(Array.isArray(results) && results.length ? results[0] : null)
      );
    });
    if (!place?.place_id) return;

    const details = await new Promise((resolve) => {
      service.getDetails(
        { placeId: place.place_id, language: "ko", fields: ["photos"] },
        (d) => resolve(d || null)
      );
    });

    const url = details?.photos?.[0]?.getUrl({ maxWidth: 1200, maxHeight: 900 });
    if (url) spot.image = url;
  };

  for (const r of next) {
    await fillPhoto(r.primary);
    await fillPhoto(r.alternative);
  }
  return next;
}

/* ==========================================================================
   애니메이션
   ========================================================================== */
const pageVariants = {
  initial: { opacity: 0, y: 24, scale: 0.98 },
  in: { opacity: 1, y: 0, scale: 1 },
  out: { opacity: 0, y: -20, scale: 0.98 },
};
const pageTransition = { type: "spring", stiffness: 260, damping: 24 };

// 스텝: 로그인, 설문, 투표, AI 추천 (Step4/Step5 제거)
const steps = ["로그인", "설문", "투표", "AI 추천"];

const cardEnter = {
  hidden: { opacity: 0, scale: 0.96, y: 12 },
  show: { opacity: 1, scale: 1, y: 0, transition: { type: "spring", stiffness: 220, damping: 18 } },
};
const cardTap = { whileTap: { scale: 0.98 } };
const selectedPulse = {
  animate: { boxShadow: ["0 0 0 0px rgba(13,148,136,0.45)", "0 0 0 16px rgba(13,148,136,0)"] },
  transition: { duration: 1.25, repeat: Infinity, ease: "easeOut" },
};

/* ==========================================================================
   공용 컴포넌트
   ========================================================================== */
const DetailTooltipTitle = (p) => (
  <Box sx={{ p: 0.5 }}>
    <Typography variant="subtitle2" fontWeight={700}>{p?.name || "이름 없음"}</Typography>
    <Typography variant="caption">📍 {p?.address || "-"}</Typography><br />
    <Typography variant="caption">🏷️ {p?.category || "-"}</Typography><br />
    <Typography variant="caption">⭐ {p?.rating ?? "N/A"}</Typography>
    {p?.description && (
      <>
        <Divider sx={{ my: 0.5 }} />
        <Typography variant="caption" sx={{ whiteSpace: "pre-wrap" }}>{p.description}</Typography>
      </>
    )}
  </Box>
);

function BigChoiceCardInner({ label, place, selected, onSelect, compact = false, disabled = false }) {
  const [src, setSrc] = React.useState("");
  const [imgLoaded, setImgLoaded] = React.useState(false);

  React.useEffect(() => {
    const url = extractPhotoUrl(place) || PLACEHOLDER_URL;
    setImgLoaded(false);
    setSrc(url);
  }, [place]);

  const handleSelect = React.useCallback(() => {
    if (!disabled) onSelect();
  }, [disabled, onSelect]);

  return (
    <Badge
      invisible={!selected}
      overlap="circular"
      anchorOrigin={{ vertical: "top", horizontal: "left" }}
      badgeContent={
        <Chip
          label="선택됨"
          color="success"
          size="small"
          sx={{ fontWeight: 700, fontSize: { xs: "0.65rem", sm: "0.75rem" } }}
        />
      }
      sx={{ width: "100%" }}
    >
      <motion.div variants={cardEnter} initial="hidden" animate="show" {...cardTap} style={{ width: "100%" }}>
        <motion.div {...(selected ? selectedPulse : {})} style={{ borderRadius: 20 }}>
          <Card
            role="button"
            tabIndex={0}
            aria-disabled={disabled}
            onKeyDown={(e) => !disabled && ((e.key === "Enter" || e.key === " ") && handleSelect())}
            variant="outlined"
            onClick={handleSelect}
            sx={{
              outline: "none",
              borderWidth: 2,
              borderColor: selected ? tone.accent : tone.border,
              cursor: disabled ? "not-allowed" : "pointer",
              position: "relative",
              transition: "all .2s",
              background: tone.cardGrad,
              minHeight: compact ? { xs: 220, sm: 260 } : { xs: 280, md: 360 },
              display: "flex",
              flexDirection: "column",
              "&:hover": disabled ? {} : {
                borderColor: tone.primary,
                transform: "translateY(-2px)",
                boxShadow: "0 12px 30px rgba(0,0,0,0.06)",
              },
              ...(selected && { boxShadow: `0 0 0 3px ${tone.accent}33 inset` }),
            }}
          >
            <CardContent sx={{ p: compact ? { xs: 1.5, sm: 2 } : { xs: 2, sm: 2.5, md: 3 }, flex: 1 }}>
              <Stack direction="row" alignItems="flex-start" spacing={{ xs: 0.75, sm: 1.25 }} sx={{ mb: { xs: 0.75, sm: 1 } }}>
                <PlaceIcon sx={{ color: tone.primary, mt: "3px", fontSize: { xs: 18, sm: 22 }, pointerEvents: "none" }} />
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography variant="h6" fontWeight={900} noWrap sx={{ fontSize: { xs: "0.95rem", sm: "1.1rem" } }}>
                    {compact ? label + " · " : ""}{place?.name || "-"}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9, fontSize: { xs: "0.75rem", sm: "0.9rem" } }} noWrap>
                    📍 {place?.address || "-"}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.8, fontSize: { xs: "0.75rem", sm: "0.9rem" } }} noWrap>
                    🏷️ {place?.category || "-"} · ⭐ {place?.rating ?? "N/A"}
                  </Typography>
                </Box>

                <Tooltip title={DetailTooltipTitle(place)} arrow placement="left" componentsProps={{ tooltip: { sx: { maxWidth: 320 } } }}>
                  <span>
                    <IconButton
                      type="button"
                      size="small"
                      onClick={(e) => e.stopPropagation()}
                      aria-label="상세보기"
                      sx={{ p: { xs: 0.5, sm: 0.75 } }}
                    >
                      <SearchIcon sx={{ fontSize: { xs: "1rem", sm: "1.25rem" } }} />
                    </IconButton>
                  </span>
                </Tooltip>
              </Stack>

              <Box
                onClick={handleSelect}
                sx={{
                  mt: { xs: 0.75, sm: 1.25 },
                  borderRadius: { xs: 1.5, sm: 2.5 },
                  overflow: "hidden",
                  bgcolor: "#eef2f7",
                  position: "relative",
                  aspectRatio: "16/9",
                  cursor: disabled ? "not-allowed" : "pointer",
                }}
              >
                {!imgLoaded && (
                  <Skeleton
                    variant="rectangular"
                    width="100%"
                    height="100%"
                    sx={{ position: "absolute", inset: 0, pointerEvents: "none" }}
                  />
                )}
                <img
                  src={src}
                  alt={place?.name || "place"}
                  loading="lazy"
                  referrerPolicy="no-referrer"
                  style={{ display: imgLoaded ? "block" : "none", width: "100%", height: "100%", objectFit: "cover" }}
                  onLoad={() => setImgLoaded(true)}
                  onError={(e) => { e.currentTarget.src = PLACEHOLDER_URL; setImgLoaded(true); }}
                />
              </Box>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </Badge>
  );
}
const BigChoiceCard = React.memo(BigChoiceCardInner);

/* ==========================================================================
   메인 컴포넌트
   ========================================================================== */
export default function SurveyPage() {
  const navigate = useNavigate();
  const theme = useTheme();
  // ML 자동 로딩 TIP/진행
  const [mlLoading, setMlLoading] = useState(false);
  const [mlProgress, setMlProgress] = useState(0);
  const [mlTipIdx, setMlTipIdx] = useState(0);

  // 로딩 화면 TIP (제목은 "그거 아셨나요?"이지만, 본문 끝의 "…아셨나요?"는 제거)
// 로딩 화면 TIP (부산 관광지 흥미로운 사실)
const LOADING_TIPS = [
  "감천문화마을은 색색의 집들이 산비탈에 늘어선 예술 마을로, ‘한국의 마추픽추’라 불립니다.",
  "광안대교는 야간에 매일 다른 색의 경관 조명을 선보이며, 부산 야경 명소 1순위로 꼽힙니다.",
  "해운대 해수욕장은 조선 시대부터 경승지로 기록되었고, 이름은 신라 학자 최치원의 호 ‘해운(海雲)’에서 유래했습니다.",
  "자갈치시장은 한국 최대의 수산 시장 중 하나로, ‘오이소ㆍ보이소ㆍ사이소’ 사투리로 유명합니다.",
  "태종대는 절벽 위 전망대에서 대한해협을 조망할 수 있고, 맑은 날엔 대마도도 보인다는 후기가 많습니다.",
  "부산 영화의전당은 세계에서 가장 긴 ‘캔틸레버 지붕’으로 기네스 기록을 보유했습니다.",
  "국제시장 골목은 6.25 전후 자연발생한 시장으로, 골목마다 테마가 달라 하루 코스로도 모자랍니다.",
  "용궁사는 바다와 가장 가까운 사찰 중 하나로, 일출 명소로 특히 유명합니다.",
  "송정 해수욕장은 ‘서핑 메카’로 급부상하여 초보자 강습 시설이 몰려 있습니다.",
  "부산 현대미술관(MoCA)은 을숙도 철새도래지 근처에 있어 자연과 전시 관람을 함께 즐기기 좋습니다."
];


  // 화면폭 기반 감지 (깜빡임 방지: noSsr)
  const isViewportMobile = useMediaQuery(theme.breakpoints.down("sm"), { noSsr: true });
  const isDeviceMobile = isMobileUA || isAndroid || isIOS;
  const isMobile = useMemo(() => {
    const params = new URLSearchParams(typeof window !== "undefined" ? window.location.search : "");
    let v = isDeviceMobile || isViewportMobile;
    if (params.get("m") === "1") v = true;
    if (params.get("m") === "0") v = false;
    return v;
  }, [isViewportMobile, isDeviceMobile]);

  /* ------------------ 상태 ------------------ */
  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState({ open: false, message: "", severity: "info" });
  const [activeStep, setActiveStep] = useState(0);

  // 로그인 상태
  const [loginStatus, setLoginStatus] = useState({
    user_id: "",
    logged_in: false,
    has_survey_data: false,
    has_votes: false,
    status: "",
  });

  // 설문 입력 (원본 그대로 유지: 5개)
  const [activity, setActivity] = useState("");
  const [activityLevel, setActivityLevel] = useState("");
  const [time, setTime] = useState("");
  const [season, setSeason] = useState("");
  const [preference, setPreference] = useState("");

  // 추천/투표/ML
  const [placeRecs, setPlaceRecs] = useState([]);
  const [currentVotes, setCurrentVotes] = useState([]);
  const [mlRecs, setMlRecs] = useState([]);

  // 투표 UX
  const [currentRoundIdx, setCurrentRoundIdx] = useState(0);
  const [selectedMessage, setSelectedMessage] = useState("");
  const [isAdvancing, setIsAdvancing] = useState(false);

  useEffect(() => { (async () => { await handleCheckLogin(); })(); /* eslint-disable-next-line */ }, []);

  const showToast = (message, severity = "info") => setToast({ open: true, message, severity });
  const closeToast = () => setToast((t) => ({ ...t, open: false }));

  /* ------------------ 로그인 ------------------ */


  const handleCheckLogin = async () => {
    setLoading(true);
    try {
      if (localStorage.getItem(BYPASS_KEY) === "1") {
        const dummy = { user_id: "dev-admin", logged_in: true, has_survey_data: false, has_votes: false, status: "bypass" };
        setLoginStatus(dummy);
        setActiveStep(1);
        showToast("관리자(로컬) 로그인 유지 중", "success");
        return;
      }
      const resp = await apiCall(`${API_BASE}/survey`);
      const loggedIn = !!(resp && (resp.logged_in || resp.user_id));
      setLoginStatus({
        user_id: resp?.user_id || "",
        logged_in: loggedIn,
        has_survey_data: !!resp?.has_survey_data,
        has_votes: !!resp?.has_votes,
        status: resp?.status || "",
      });
      setActiveStep(loggedIn ? 1 : 0);
      showToast(loggedIn ? "로그인됨" : "로그인 필요", loggedIn ? "success" : "warning");
    } catch (e) {
      showToast(`로그인 상태 확인 실패: ${e.message}`, "error");
      setActiveStep(0);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    setLoading(true);
    try {
      localStorage.removeItem(BYPASS_KEY);
      try { await apiCall(`${API_BASE}/auth/logout`, { method: "POST" }); } catch { }
      setLoginStatus({ user_id: "", logged_in: false, has_survey_data: false, has_votes: false, status: "" });
      setActiveStep(0);
      showToast("로그아웃 완료", "success");
    } catch (e) {
      showToast(`로그아웃 실패: ${e.message}`, "error");
    } finally {
      setLoading(false);
    }
  };

  /* ------------------ 설문 ------------------ */
  const handleSubmitSurvey = async () => {
    const surveyDataRaw = { activity, activity_level: activityLevel, time, season, preference };
    if (!Object.values(surveyDataRaw).every(Boolean)) {
      showToast("모든 설문 항목을 선택해 주세요.", "warning");
      return;
    }
    const levelMap = { "보통": "중간" };
    const surveyData = { ...surveyDataRaw, activity_level: levelMap[surveyDataRaw.activity_level] || surveyDataRaw.activity_level };

    setLoading(true);
    try {
      const data = await apiCall(`${API_BASE}/survey/submit`, { method: "POST", body: surveyData });
      showToast(data?.message || "설문 제출 완료", "success");
      setActiveStep(2);
    } catch (e) {
      showToast(`설문 제출 실패: ${e.message}`, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleSurveyStatus = async () => {
    setLoading(true);
    try {
      const resp = await apiCall(`${API_BASE}/survey/data`);
      const msg = [
        `상태: ${resp?.status || "-"}`,
        `총 투표 수: ${resp?.total_votes ?? 0}`,
        resp?.database_info ? `DB: ${JSON.stringify(resp.database_info)}` : "",
      ].filter(Boolean).join("\n");
      showToast(msg || "상태 조회 완료", "info");
    } catch (e) {
      showToast(`설문 상태 확인 실패: ${e.message}`, "error");
    } finally {
      setLoading(false);
    }
  };

  /* ------------------ 추천/투표 ------------------ */
  const handlePlaceRecs = async () => {
    setLoading(true);
    try {
      const resp = await apiCall(`${API_BASE}/survey/place-recommendations`);
      const mapped = (resp?.recommendations || []).map((r) => ({
        round_number: r.round_number,
        primary: r.option_a?.item || null,
        alternative: r.option_b?.item || null,
      }));
      const withPhotos = await augmentRoundImages(mapped);
      setPlaceRecs(withPhotos);
      setCurrentVotes([]);
      setSelectedMessage("");
      setIsAdvancing(false);
      setCurrentRoundIdx(0);
      showToast("장소 추천 완료", "success");
    } catch (e) {
      setPlaceRecs([]);
      setCurrentVotes([]);
      showToast(`추천 실패: ${e.message}`, "error");
    } finally {
      setLoading(false);
    }
  };

  const isSelected = (roundIdx, which, name) => {
    const v = currentVotes[roundIdx];
    const want = which === "primary" ? "option_a" : "option_b";
    return v && v.choice === want && v.item_name === name;
  };

  const rounds = useMemo(() => (placeRecs || []).slice(0, 5), [placeRecs]);

  useEffect(() => {
    if (activeStep === 2 && (placeRecs?.length ?? 0) === 0) handlePlaceRecs();
  }, [activeStep]); // eslint-disable-line

  const selectVote = (roundIndex, which, item) => {
    const choice = which === "primary" ? "option_a" : "option_b";
    setCurrentVotes((prev) => {
      const copy = [...prev];
      copy[roundIndex] = { round: roundIndex + 1, choice, item_name: item?.name || null };
      return copy;
    });
  };

  const handleSelectAndAdvance = (roundIdx, which, item) => {
    if (isAdvancing) return;
    selectVote(roundIdx, which, item);
    setSelectedMessage(`${item?.name || "선택 항목"}을(를) 고르셨습니다 ✅`);
    setIsAdvancing(true);

    setTimeout(() => {
      setSelectedMessage("");
      setIsAdvancing(false);
      if (roundIdx < rounds.length - 1) setCurrentRoundIdx(roundIdx + 1);
      else showToast("마지막 라운드 선택 완료! '투표 제출'을 눌러주세요.", "info");
    }, 1000);
  };

  const handleSubmitVotes = async () => {
    if (!rounds?.length) {
      showToast("추천이 아직 준비되지 않았습니다.", "warning");
      return;
    }
    const missing = [];
    for (let i = 0; i < rounds.length; i++) {
      if (!currentVotes[i] || !currentVotes[i]?.choice || !currentVotes[i]?.item_name) missing.push(i + 1);
    }
    if (missing.length) {
      showToast(`라운드 ${missing.join(", ")}의 선택 정보가 누락되었어요. 다시 선택해 주세요.`, "warning");
      const firstMissing = Math.min(...missing) - 1;
      setCurrentRoundIdx(firstMissing);
      return;
    }

    const payloadVotes = currentVotes
      .slice(0, rounds.length)
      .map((v, i) => ({ round: i + 1, choice: v.choice, item_name: v.item_name }));

    setLoading(true);
    try {
      const resp = await apiCall(`${API_BASE}/survey/votes`, { method: "POST", body: { votes: payloadVotes } });
      showToast(resp?.message ? `투표 제출 완료: ${resp.message}` : "투표 제출 완료", "success");
      try { await handleCheckLogin(); } catch { }
      setActiveStep(3);
    } catch (e) {
      showToast(`투표 제출 실패: ${e.message}`, "error");
    } finally {
      setLoading(false);
    }
  };

  /* ------------------ ML: 자동 로딩 → 자동 이동 ------------------ */
  const handleMLRecs = async (autoNavigate = false) => {
    setLoading(true);
    setMlLoading(true);
    setMlProgress(0);

    // 진행바/팁 회전 타이머
const started = Date.now();
const progTimer = setInterval(() => {
  const elapsed = Date.now() - started;
  // 12초 기준으로 부드럽게 올리고, 실제 응답 오면 100%로 마무리
  const soft = Math.min(95, Math.round((elapsed / 12000) * 100));
  setMlProgress((p) => (p < soft ? soft : p));
}, 160); // frame 속도도 살짝 느리게

const tipTimer = setInterval(() => {
  setMlTipIdx((i) => (i + 1) % LOADING_TIPS.length);
}, 4200);

    try {
      const uid = loginStatus?.user_id;
      if (!uid) {
        throw new Error("user_id가 필요합니다. 먼저 로그인해 주세요.");
      }
      const resp = await apiCall(`${API_BASE}/survey/ml-recommendations?user_id=${encodeURIComponent(uid)}&k=20`);
      const raw = Array.isArray(resp?.recommendations) ? resp.recommendations : [];
      const normalized = raw.map((p, i) => normalizeMlSpot(p, i));

      // 맵 사진 보강 (옵션)
      if (GMAPS_KEY) {
        const loader = new Loader({ apiKey: GMAPS_KEY, libraries: ["places"], region: "KR", language: "ko" });
        await loader.load();
        const mapDiv = document.createElement("div");
        const service = new window.google.maps.places.PlacesService(mapDiv);
        const BUSAN_CENTER = { lat: 35.1796, lng: 129.0756 };
        for (const spot of normalized) {
          const hasImage = spot.image && !/^data:image/i.test(spot.image) && !/placeholder/i.test(spot.image);
          if (hasImage) continue;
          const query = (spot.name || "").trim();
          if (!query) continue;
          const place = await new Promise((resolve) => {
            service.textSearch(
              { query: `부산 ${query}`, location: new window.google.maps.LatLng(BUSAN_CENTER.lat, BUSAN_CENTER.lng), radius: 50000, language: "ko" },
              (results) => resolve(Array.isArray(results) && results.length ? results[0] : null)
            );
          });
          if (!place?.place_id) continue;
          const details = await new Promise((resolve) => {
            service.getDetails({ placeId: place.place_id, language: "ko", fields: ["photos"] }, (d) => resolve(d || null));
          });
          const url = details?.photos?.[0]?.getUrl({ maxWidth: 1200, maxHeight: 900 });
          if (url) spot.image = url;
        }
      }

      setMlRecs(normalized);
      setMlProgress(100);

      if (autoNavigate) {
        // 곧바로 추천 페이지로 이동
        navigate("/tourist-spot-recommend", {
          state: {
            user_id: loginStatus?.user_id || "",
            attractions: normalized.map((r, i) => ({
              id: String(r.id || r.item_id || r._id || r.content_id || r.ml_index || i + 1),
              name: r.name || r.item_name || "",
              address: r.address || "",
              lat: r.lat,
              lng: r.lng,
              image: r.image || "",
              category_type: r.category_type || null,
              category: r.category || "",
              score: typeof r.ml_score === "number" ? r.ml_score : r.score ?? null,
              reason: r.reason || "",
            })),
            isMlList: true,
            source: "ml",
          },
        });
      } else {
        showToast(resp?.message || `AI 추천 완료 (${normalized.length}곳)`, "success");
      }
    } catch (e) {
      showToast(`AI 추천 실패: ${e.message}`, "error");
    } finally {
      clearInterval(progTimer);
      clearInterval(tipTimer);
      setMlLoading(false);
      setLoading(false);
    }
  };

  // AI 추천 단계에 들어오면 자동 실행(로딩 TIP 화면 → 자동 이동)
  useEffect(() => {
    if (activeStep === 3) {
      setMlTipIdx(Math.floor(Math.random() * LOADING_TIPS.length));
      setMlProgress(0);
      handleMLRecs(true); // 자동 내비게이트
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeStep]);

  /* ------------------ 스텝 제어 ------------------ */
  const canGoNext = useMemo(() => {
    switch (activeStep) {
      case 0: return loginStatus.logged_in || loginStatus.status === "bypass" || loginStatus.status === "guest";
      case 1: return [activity, activityLevel, time, season, preference].every(Boolean);
      case 2: return rounds.length > 0 && currentVotes.filter(Boolean).length === rounds.length;
      case 3: return true; // 자동 진행
      default: return true;
    }
  }, [activeStep, loginStatus, activity, activityLevel, time, season, preference, rounds, currentVotes]);

  const handleNext = () => setActiveStep((s) => Math.min(s + 1, steps.length - 1));
  const handleBack = () => setActiveStep((s) => Math.max(s - 1, 0));

  /* ======================================================================
     헤더 + 스텝퍼
     ====================================================================== */
  const Header = () => (
    <Paper
      elevation={0}
      sx={{
        position: "sticky",
        top: 0,
        zIndex: 10,
        borderBottom: `1px solid ${tone.border}`,
        background: `linear-gradient(120deg, ${tone.primarySoft}, #F0FDFA)`
      }}
    >
      <Container maxWidth="lg" sx={{ py: { xs: 1.5, sm: 2, md: 2.5 }, px: { xs: 1.5, sm: 2, md: 3 } }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" spacing={2}>
          <Box>
            <Typography variant="h4" fontWeight={800} color={tone.primary} sx={{ fontSize: { xs: "1.25rem", sm: "1.5rem", md: "2rem" } }}>
              🗺️ WhereWeGo 설문 시스템
            </Typography>
          </Box>
          <Stack direction="row" spacing={1} alignItems="center">
            <Chip
              color={(loginStatus.logged_in || loginStatus.status === "bypass") ? "success" : "default"}
              label={(loginStatus.logged_in || loginStatus.status === "bypass") ? "로그인됨" : "로그아웃"}
              variant="filled"
              size={isMobile ? "small" : "medium"}
            />
            {loading && <CircularProgress size={isMobile ? 18 : 24} />}
          </Stack>
        </Stack>
      </Container>
    </Paper>
  );

  const StepperBar = () => (
    <Container maxWidth="lg" sx={{ mt: { xs: 2, sm: 3 }, px: { xs: 1.5, sm: 2, md: 3 } }}>
      <Card variant="outlined" sx={{ borderColor: tone.border }}>
        <CardContent sx={{ py: { xs: 2, sm: 2.5, md: 3 } }}>
          {isMobile ? (
            <MobileStepper
              variant="progress"
              steps={steps.length}
              position="static"
              activeStep={activeStep}
              backButton={
                <Button size="small" onClick={handleBack} disabled={activeStep === 0} sx={{ fontSize: { xs: "0.75rem", sm: "0.85rem" } }}>
                  <ArrowBack fontSize="small" />뒤로
                </Button>
              }
              nextButton={
                <Button size="small" onClick={handleNext} disabled={!canGoNext || activeStep === steps.length - 1} sx={{ fontSize: { xs: "0.75rem", sm: "0.85rem" } }}>
                  다음<ArrowForward fontSize="small" />
                </Button>
              }
              sx={{ bgcolor: "transparent", px: 0 }}
            />
          ) : (
            <Stepper activeStep={activeStep} alternativeLabel>
              {steps.map((label) => (
                <Step key={label}><StepLabel>{label}</StepLabel></Step>
              ))}
            </Stepper>
          )}
        </CardContent>
      </Card>
    </Container>
  );

  /* ======================================================================
     렌더
     ====================================================================== */
  return (
    <Box sx={{ bgcolor: tone.subtle, minHeight: "100dvh", width: { xs: "100vw", md: "100%" }, overflowX: "hidden", display: "flex", flexDirection: "column" }}>
      <Header />
      <StepperBar />

      <Container maxWidth="lg" sx={{ flex: 1, py: { xs: 2, sm: 3, md: 4 }, px: { xs: 1.5, sm: 2, md: 3 } }}>
        <AnimatePresence mode="wait" initial={false}>
          {/* STEP 0 - 로그인 */}
          {activeStep === 0 && (
            <motion.div key="step-login" variants={pageVariants} initial="initial" animate="in" exit="out" transition={pageTransition}>
              <Grid container spacing={{ xs: 2, sm: 2.5, md: 3 }}>
                <Grid item xs={12}>
                  <Card variant="outlined" sx={{ borderColor: tone.border }}>
                    <CardHeader
                      avatar={<LoginIcon color="primary" sx={{ fontSize: { xs: "1.25rem", sm: "1.5rem" } }} />}
                      title="1. 로그인"
                      subheader="Google / Kakao 또는 관리자(로컬) 로그인, 혹은 로그인 없이 진행"
                      titleTypographyProps={{ fontWeight: 700, fontSize: { xs: "1.1rem", sm: "1.25rem", md: "1.5rem" } }}
                      subheaderTypographyProps={{ fontSize: { xs: "0.75rem", sm: "0.85rem", md: "0.95rem" } }}
                    />
                    <CardContent>
                      {(loginStatus.logged_in || loginStatus.status === "bypass") ? (
                        <Alert icon={<CheckCircleIcon fontSize="inherit" />} severity="success" sx={{ mb: 2, fontSize: { xs: "0.8rem", sm: "0.9rem" } }}>
                          로그인됨 — 설문: <b>{loginStatus.has_survey_data ? "완료" : "미완료"}</b>, 투표: <b>{loginStatus.has_votes ? "완료" : "미완료"}</b>
                        </Alert>
                      ) : (
                        <Alert icon={<ErrorIcon fontSize="inherit" />} severity="warning" sx={{ mb: 2, fontSize: { xs: "0.8rem", sm: "0.9rem" } }}>
                          로그인되어 있지 않습니다.
                        </Alert>
                      )}
                      <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
                        <Button startIcon={<GoogleIcon />} variant="contained" color="primary" onClick={() => (window.location.href = GOOGLE_LOGIN_URL)} sx={{ fontSize: { xs: "0.85rem", sm: "0.95rem" }, py: { xs: 1, sm: 1.2 } }}>
                          Google 로그인
                        </Button>
                        <Button startIcon={<ChatBubbleIcon />} variant="outlined" color="primary" onClick={() => (window.location.href = KAKAO_LOGIN_URL)} sx={{ fontSize: { xs: "0.85rem", sm: "0.95rem" }, py: { xs: 1, sm: 1.2 } }}>
                          Kakao 로그인
                        </Button>
                         </Stack>
                    </CardContent>
                    <CardActions sx={{ justifyContent: "space-between", px: 2, pb: 2 }}>
                      <Stack direction="row" spacing={1}>
                        <Button onClick={handleCheckLogin} sx={{ fontSize: { xs: "0.75rem", sm: "0.85rem" } }}>상태 새로고침</Button>
                        <Button variant="contained" onClick={() => setActiveStep(1)} sx={{ fontSize: { xs: "0.75rem", sm: "0.85rem" } }}>다음으로</Button>
                      </Stack>
                      <Button color="error" startIcon={<LogoutIcon />} onClick={handleLogout} sx={{ fontSize: { xs: "0.75rem", sm: "0.85rem" } }}>
                        로그아웃
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              </Grid>
            </motion.div>
          )}

          {/* STEP 1 - 설문 (원본 5항목 유지) */}
          {activeStep === 1 && (
            <motion.div key="step-survey" variants={pageVariants} initial="initial" animate="in" exit="out" transition={pageTransition}>
              <Grid container spacing={{ xs: 2, sm: 2.5, md: 3 }}>
                <Grid item xs={12}>
                  <Card variant="outlined" sx={{ borderColor: tone.border }}>
                    <CardHeader
                      avatar={<ChecklistIcon color="primary" sx={{ fontSize: { xs: "1.25rem", sm: "1.5rem" } }} />}
                      title="2. 관광 선호도 조사"
                      subheader="중요하게 생각하는 요소를 선택해주세요"
                      titleTypographyProps={{ fontWeight: 700, fontSize: { xs: "1.1rem", sm: "1.25rem", md: "1.5rem" } }}
                      subheaderTypographyProps={{ fontSize: { xs: "0.75rem", sm: "0.85rem", md: "0.95rem" } }}
                    />
                    <CardContent>
                      <Grid container spacing={{ xs: 1.5, sm: 2 }}>
                        <Grid item xs={12} sm={6}>
                          <FormControl fullWidth size={isMobile ? "small" : "medium"}>
                            <InputLabel>활동 유형</InputLabel>
                            <Select label="활동 유형" value={activity} onChange={(e) => setActivity(e.target.value)} sx={{ fontSize: { xs: "0.85rem", sm: "0.95rem" } }}>
                              <MenuItem value=""><em>선택</em></MenuItem>
                              {["자연풍경", "자연산림", "관람및체험", "휴양", "테마거리", "예술감상", "공연관람", "트레킹"].map(v => <MenuItem key={v} value={v}>{v}</MenuItem>)}
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <FormControl fullWidth size={isMobile ? "small" : "medium"}>
                            <InputLabel>활동성</InputLabel>
                            <Select label="활동성" value={activityLevel} onChange={(e) => setActivityLevel(e.target.value)} sx={{ fontSize: { xs: "0.85rem", sm: "0.95rem" } }}>
                              <MenuItem value=""><em>선택</em></MenuItem>
                              <MenuItem value="낮음">낮음</MenuItem>
                              <MenuItem value="보통">보통</MenuItem>
                              <MenuItem value="높음">높음</MenuItem>
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <FormControl fullWidth size={isMobile ? "small" : "medium"}>
                            <InputLabel>시간대</InputLabel>
                            <Select label="시간대" value={time} onChange={(e) => setTime(e.target.value)} sx={{ fontSize: { xs: "0.85rem", sm: "0.95rem" } }}>
                              <MenuItem value=""><em>선택</em></MenuItem>
                              {["오전", "오후", "저녁", "밤"].map(v => <MenuItem key={v} value={v}>{v}</MenuItem>)}
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={12} sm={6}>
                          <FormControl fullWidth size={isMobile ? "small" : "medium"}>
                            <InputLabel>계절</InputLabel>
                            <Select label="계절" value={season} onChange={(e) => setSeason(e.target.value)} sx={{ fontSize: { xs: "0.85rem", sm: "0.95rem" } }}>
                              <MenuItem value=""><em>선택</em></MenuItem>
                              {["봄", "여름", "가을", "겨울"].map(v => <MenuItem key={v} value={v}>{v}</MenuItem>)}
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={12}>
                          <Typography component="label" htmlFor="pref-toggle" sx={{ display: "block", mb: 0.75, fontWeight: 700 }}>
                            중요 요소
                          </Typography>
                          <ButtonGroup id="pref-toggle" fullWidth aria-label="중요 요소 선택">
                            <Button onClick={() => setPreference("활동성")} variant={preference === "활동성" ? "contained" : "outlined"}>활동성</Button>
                            <Button onClick={() => setPreference("시간대")} variant={preference === "시간대" ? "contained" : "outlined"}>시간대</Button>
                          </ButtonGroup>
                          <Typography variant="caption" sx={{ display: "block", mt: 0.5, opacity: 0.7 }}>
                            버튼을 눌러 둘 중 하나를 선택하세요.
                          </Typography>
                        </Grid>
                      </Grid>
                    </CardContent>
                    <CardActions sx={{ justifyContent: "space-between", px: 2, pb: 2 }}>
                      <Button disabled={activeStep === 0} onClick={handleBack}>뒤로</Button>
                      <Stack direction="row" spacing={1} flexWrap="wrap" gap={0.5}>
                        <Button onClick={handleSurveyStatus} startIcon={<PendingIcon />}>설문 상태</Button>
                        <Button onClick={handleSubmitSurvey} variant="contained" startIcon={<SendIcon />}>설문 제출</Button>
                        <Button variant="outlined" onClick={() => setActiveStep(2)}>다음</Button>
                      </Stack>
                    </CardActions>
                  </Card>
                </Grid>
              </Grid>
            </motion.div>
          )}

          {/* STEP 2 - 투표 */}
          {activeStep === 2 && (
            <motion.div key="step-vote" variants={pageVariants} initial="initial" animate="in" exit="out" transition={pageTransition}>
              <Grid container spacing={{ xs: 2, sm: 2.5, md: 3 }}>
                <Grid item xs={12}>
                  <Card variant="outlined" sx={{ borderColor: tone.border }}>
                    <CardHeader
                      avatar={<HowToVoteIcon color="primary" sx={{ fontSize: { xs: "1.25rem", sm: "1.5rem" } }} />}
                      title={`3. 투표 (라운드 ${currentRoundIdx + 1}/${rounds.length || 0})`}
                      subheader="추천된 두 장소 중 선호하는 곳을 라운드별로 선택하세요"
                      titleTypographyProps={{ fontWeight: 700 }}
                    />
                    <CardActions sx={{ px: 2, pt: 0, flexWrap: "wrap", gap: 1 }}>
                      <Button onClick={handleSubmitVotes} variant="contained" startIcon={<HowToVoteIcon />} disabled={!rounds.length || isAdvancing}>
                        투표 제출
                      </Button>
                      {isMobile && rounds.length > 0 && (
                        <Stack direction="row" spacing={0.5} sx={{ ml: "auto" }}>
                          <IconButton size="small" disabled={currentRoundIdx === 0 || isAdvancing} onClick={() => setCurrentRoundIdx((i) => Math.max(0, i - 1))}>
                            <ArrowBack fontSize="small" />
                          </IconButton>
                          <IconButton size="small" disabled={currentRoundIdx >= rounds.length - 1 || isAdvancing} onClick={() => setCurrentRoundIdx((i) => Math.min(rounds.length - 1, i + 1))}>
                            <ArrowForward fontSize="small" />
                          </IconButton>
                        </Stack>
                      )}
                    </CardActions>

                    <CardContent sx={{ pt: 0 }}>
                      {!rounds.length ? (
                        <Alert severity="info">추천을 준비하고 있어요… 잠시만요.</Alert>
                      ) : (
                        <>
                          <AnimatePresence>
                            {selectedMessage && (
                              <motion.div initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -6 }} transition={{ duration: 0.25 }}>
                                <Alert severity="success" sx={{ my: 1.5, fontWeight: 700 }}>{selectedMessage}</Alert>
                              </motion.div>
                            )}
                          </AnimatePresence>

                          {(() => {
                            const round = rounds[currentRoundIdx] || {};
                            return (
                              <Grid container spacing={{ xs: 1.5, sm: 2, md: 3 }}>
                                <Grid item xs={12} md={6}>
                                  <BigChoiceCard
                                    label="A"
                                    place={round?.primary}
                                    selected={isSelected(currentRoundIdx, "primary", round?.primary?.name)}
                                    onSelect={() => handleSelectAndAdvance(currentRoundIdx, "primary", round?.primary)}
                                    compact={isMobile}
                                    disabled={isAdvancing}
                                  />
                                </Grid>
                                <Grid item xs={12} md={6}>
                                  <BigChoiceCard
                                    label="B"
                                    place={round?.alternative}
                                    selected={isSelected(currentRoundIdx, "alternative", round?.alternative?.name)}
                                    onSelect={() => handleSelectAndAdvance(currentRoundIdx, "alternative", round?.alternative)}
                                    compact={isMobile}
                                    disabled={isAdvancing}
                                  />
                                </Grid>
                              </Grid>
                            );
                          })()}

                          <Stack direction="row" justifyContent="space-between" alignItems="center" sx={{ mt: 2 }}>
                            <Typography variant="body1" sx={{ opacity: 0.8 }}>
                              현재 선택:{" "}
                              {currentVotes[currentRoundIdx]?.choice ? `${currentVotes[currentRoundIdx].choice} · ${currentVotes[currentRoundIdx].item_name}` : "없음"}
                            </Typography>
                            {!isMobile && (
                              <Stack direction="row" spacing={1}>
                                <Button startIcon={<ArrowBack />} disabled={currentRoundIdx === 0 || isAdvancing} onClick={() => setCurrentRoundIdx((i) => Math.max(0, i - 1))}>
                                  이전 라운드
                                </Button>
                                <Button variant="outlined" disabled={currentRoundIdx >= rounds.length - 1 || isAdvancing} onClick={() => setCurrentRoundIdx((i) => Math.min(rounds.length - 1, i + 1))}>
                                  다음 라운드
                                </Button>
                              </Stack>
                            )}
                          </Stack>
                        </>
                      )}
                    </CardContent>
                  </Card>
                </Grid>
              </Grid>
            </motion.div>
          )}

          {/* STEP 3 - ML 추천: 자동 로딩 → 자동 이동 */}
          {activeStep === 3 && (
            <motion.div
              key="step-ml"
              variants={pageVariants}
              initial="initial"
              animate="in"
              exit="out"
              transition={pageTransition}
            >
              <Grid container spacing={{ xs: 2, sm: 2.5, md: 3 }}>
                <Grid item xs={12}>
                  <Card variant="outlined" sx={{ borderColor: tone.border }}>
                    <CardHeader
  avatar={<ScienceIcon color="primary" sx={{ fontSize: { xs: "1.25rem", sm: "1.5rem" } }} />}
  title="분석 중..."
  subheader="맞춤형 부산 여행 추천을 생성하고 있습니다..."
  titleTypographyProps={{
    fontWeight: 900,
    fontSize: { xs: "1.4rem", sm: "1.6rem", md: "1.8rem" },
    color: tone.primary,
  }}
  subheaderTypographyProps={{
    fontSize: { xs: "0.9rem", sm: "1rem" },
    mt: 0.5,
  }}
/>
<CardContent>
  <Box
    sx={{
      p: { xs: 2, sm: 2.5 },
      border: `1px solid ${tone.border}`,
      borderRadius: 2,
      bgcolor: tone.paper,
    }}
  >
    {/* "알고 계셨나요?" 박스 */}
    <Box
      sx={{
        p: { xs: 1.5, sm: 2 },
        mb: 2,
        borderRadius: 2,
        bgcolor: "#F5F7FB",
      }}
    >
      <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 0.5 }}>
        알고 계셨나요?
      </Typography>
      <Typography
        variant="body2"
        sx={{ lineHeight: 1.7, color: "text.secondary" }}
      >
        {LOADING_TIPS[mlTipIdx]}
      </Typography>
    </Box>

    {/* 진행 게이지 */}
    <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
      <Box sx={{ flex: 1 }}>
        <LinearProgress variant="determinate" value={mlProgress} />
      </Box>
      <Typography variant="caption" sx={{ width: 38, textAlign: "right" }}>
        {mlProgress}%
      </Typography>
    </Box>

    <Typography variant="caption" sx={{ display: "block", mt: 1, opacity: 0.7 }}>
      AI 추천 생성이 완료되면 자동으로 다음 화면으로 이동합니다.
    </Typography>
  </Box>

  {/* 오류 시 재시도 버튼 (로직 동일) */}
  {!mlLoading && mlProgress === 0 && (
    <Stack direction="row" spacing={1} sx={{ mt: 2 }}>
      <Button variant="contained" onClick={() => handleMLRecs(true)}>다시 시도</Button>
      <Button variant="text" onClick={() => setActiveStep(2)}>투표로 돌아가기</Button>
    </Stack>
  )}
</CardContent>

                  </Card>
                </Grid>
              </Grid>
            </motion.div>
          )}

        </AnimatePresence>
      </Container>

      {/* 토스트 */}
      <Snackbar open={toast.open} autoHideDuration={5000} onClose={closeToast} anchorOrigin={{ vertical: "bottom", horizontal: "center" }}>
        <Alert onClose={closeToast} severity={toast.severity} sx={{ width: "100%" }}>
          <span style={{ whiteSpace: "pre-line" }}>{toast.message}</span>
        </Alert>
      </Snackbar>
    </Box>
  );
}
