import React, { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { Box, Typography, Button, Stack, Chip, IconButton, Tooltip } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import { ArrowBackIosNew, ArrowForwardIos, Favorite, FavoriteBorder } from "@mui/icons-material";
import "./AiPlannerBanner.scss";

const SLIDE_INTERVAL_MS = 5000;

// ─────────────────────────────────────────────────────────
// API prefix
// ─────────────────────────────────────────────────────────
const API_PREFIX =
  process.env.REACT_APP_API_PREFIX ||
  (typeof import.meta !== "undefined" &&
    import.meta.env &&
    import.meta.env.VITE_API_PREFIX) ||
  "";
const API_BASE = `${API_PREFIX.replace(/\/$/, "")}/api/v1`;

// 로컬스토리지 키 (폴백)
const WISHLIST_STORAGE_KEY = "myWishlist";

// ─────────────────────────────────────────────────────────
// API helpers
// ─────────────────────────────────────────────────────────
async function apiCheckStatus({ user_id, place_id }) {
  const url = `${API_BASE}/wish/status?user_id=${encodeURIComponent(user_id)}&place_id=${encodeURIComponent(place_id)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json(); // { wished: boolean } 형태 가정
}
async function apiAddWish({ user_id, place_id }) {
  const res = await fetch(`${API_BASE}/wish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, place_id }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
async function apiDeleteWish({ user_id, place_id }) {
  const res = await fetch(`${API_BASE}/wish`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, place_id }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// 로컬스토리지 폴백 helpers
function readLocalWishlist() {
  try {
    const saved = localStorage.getItem(WISHLIST_STORAGE_KEY);
    return saved ? JSON.parse(saved) : [];
  } catch {
    return [];
  }
}
function writeLocalWishlist(next) {
  try {
    localStorage.setItem(WISHLIST_STORAGE_KEY, JSON.stringify(next));
  } catch {}
}
function isInLocalWishlist(place_id) {
  const list = readLocalWishlist();
  return list.some((i) => i.id === place_id);
}
function addToLocalWishlist(item) {
  const list = readLocalWishlist();
  if (!list.some((i) => i.id === item.id)) {
    writeLocalWishlist([{ id: item.id, name: item.name || item.title || "이름 없음", image: item.src }, ...list]);
  }
}
function removeFromLocalWishlist(place_id) {
  const list = readLocalWishlist();
  writeLocalWishlist(list.filter((i) => i.id !== place_id));
}

export default function AiPlannerBanner() {
  // 로그인 사용자 ID (전역 상태/쿠키 등에서 주입)
  const userId = localStorage.getItem("user_id") || "";

  // placeId를 실제 DB의 place_id로 바꿔주세요. (없으면 slug로도 로컬 폴백 동작)
  const slides = useMemo(
    () => [
      { id: "place-haeundae", placeId: "haeundae", src: "/image/HaeundaeBeach.jpg", alt: "해운대 해수욕장 전경", caption: "끝없이 펼쳐진 모래사장, 해운대" },
      { id: "place-gwangalli", placeId: "gwangalli", src: "/image/gwangalli_beach.jpg", alt: "광안리 야경과 광안대교", caption: "밤이 더 빛나는 광안리" },
      { id: "place-gamcheon", placeId: "gamcheon", src: "/image/Gamcheon.jpg", alt: "감천문화마을 전경", caption: "알록달록 감천문화마을" },
      { id: "place-jagalchi", placeId: "jagalchi", src: "/image/JagalchiMarket.jpg", alt: "자갈치 시장 풍경", caption: "부산의 미각, 자갈치 시장" },
    ],
    []
  );

  const [index, setIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [isWished, setIsWished] = useState(false);
  const [checking, setChecking] = useState(false);
  const timerRef = useRef(null);

  // 이미지 프리로드
  useEffect(() => {
    slides.forEach((s) => {
      const img = new Image();
      img.src = s.src;
    });
  }, [slides]);

  // 자동 슬라이드
  useEffect(() => {
    if (isPaused) return;
    timerRef.current = setInterval(() => setIndex((p) => (p + 1) % slides.length), SLIDE_INTERVAL_MS);
    return () => clearInterval(timerRef.current);
  }, [slides.length, isPaused]);

  // 현재 슬라이드의 위시 상태 확인 (서버 → 실패시 로컬 폴백)
  const checkWish = useCallback(
    async (cur) => {
      const item = slides[cur];
      if (!item) return;
      const placeId = item.placeId || item.id; // 서버 place_id가 없으면 id 사용(로컬 폴백)
      try {
        if (!userId || !API_PREFIX) {
          // 비로그인 또는 API 미설정 시 로컬 폴백
          setIsWished(isInLocalWishlist(placeId));
          return;
        }
        setChecking(true);
        const data = await apiCheckStatus({ user_id: userId, place_id: placeId });
        setIsWished(!!data?.wished);
      } catch {
        // 서버 장애 → 로컬 폴백
        setIsWished(isInLocalWishlist(placeId));
      } finally {
        setChecking(false);
      }
    },
    [slides, userId]
  );

  // 인덱스 변경/유저 변경 시 상태 확인
  useEffect(() => {
    checkWish(index);
  }, [index, userId, checkWish]);

  const goPrev = () => setIndex((p) => (p - 1 + slides.length) % slides.length);
  const goNext = () => setIndex((p) => (p + 1) % slides.length);

  // ♥ 토글
  const toggleWish = async () => {
    const item = slides[index];
    const placeId = item.placeId || item.id;

    // 낙관적 토글
    setIsWished((w) => !w);

    try {
      if (!userId || !API_PREFIX) {
        // 비로그인/미설정 → 로컬만
        if (isInLocalWishlist(placeId)) {
          removeFromLocalWishlist(placeId);
        } else {
          addToLocalWishlist({ id: placeId, name: item.caption, src: item.src });
        }
        return;
      }

      if (isWished) {
        await apiDeleteWish({ user_id: userId, place_id: placeId });
        removeFromLocalWishlist(placeId); // 서버 성공 시 로컬도 정리
      } else {
        await apiAddWish({ user_id: userId, place_id: placeId });
        addToLocalWishlist({ id: placeId, name: item.caption, src: item.src });
      }
    } catch {
      // 실패 시 롤백
      setIsWished((w) => !w);
    }
  };

  return (
    <section
      className="ai-banner"
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      {/* 배경 */}
      <Box className="ai-banner__bg">
        {slides.map((s, i) => (
          <img
            key={s.src}
            src={s.src}
            alt={s.alt}
            className={`ai-banner__bg-img ${i === index ? "is-active" : ""}`}
            aria-hidden={i === index ? "false" : "true"}
            loading={i === 0 ? "eager" : "lazy"}
          />
        ))}
        <div className="ai-banner__bg-gradient" />
        <div className="ai-banner__shape-1" />
        <div className="ai-banner__shape-2" />
      </Box>

      {/* ♥ 위시 버튼 (배너 우상단) */}
      <Tooltip title={isWished ? "위시리스트에서 제거" : "위시리스트에 추가"}>
        <IconButton
          className="ai-banner__wish"
          aria-label="위시리스트 토글"
          onClick={toggleWish}
          disabled={checking}
        >
          {isWished ? <Favorite /> : <FavoriteBorder />}
        </IconButton>
      </Tooltip>

      {/* 컨텐츠 */}
      <Box className="ai-banner__content">
        <Box className="ai-banner__left">
          <Typography variant="h3" className="ai-banner__title">
            AI 맞춤 부산 여행, 지금 바로 시작하세요!
          </Typography>

          <Typography variant="subtitle1" className="ai-banner__subtitle">
            복잡한 계획은 AI에게 맡기고, <br />
            나만을 위한 특별한 부산 여행 코스를 경험해보세요.
          </Typography>

          <Stack direction="row" spacing={1} className="ai-banner__hashtags" useFlexGap flexWrap="wrap">
            {["#해운대", "#광안리", "#맞춤여행", "#부산맛집"].map((tag) => (
              <Chip key={tag} label={tag} className="ai-banner__chip" />
            ))}
          </Stack>

          <Stack direction="row" spacing={2} className="ai-banner__cta">
            <Button
              variant="contained"
              color="primary"
              className="ai-banner__btn"
              component={RouterLink}
              to="/survey"
              size="large"
              disableElevation
            >
              나만의 여행 코스 만들기 →
            </Button>
            <Button
              variant="outlined"
              color="inherit"
              className="ai-banner__btn-secondary"
              component={RouterLink}
              to="/explore"
              size="large"
              disableElevation
            >
              인기 코스 구경하기
            </Button>
          </Stack>

          <Typography variant="caption" className="ai-banner__caption">
            {slides[index].caption}
          </Typography>
        </Box>

        {/* 하단 컨트롤 바: ⟨ ⟩ + 점 */}
        <div className="ai-banner__controls" role="group" aria-label="슬라이드 내비게이션">
          <button className="ctrl-btn" aria-label="이전 슬라이드" onClick={goPrev}>
            <ArrowBackIosNew fontSize="small" />
          </button>

          <div className="ai-banner__dots">
            {slides.map((_, i) => (
              <button
                key={i}
                className={`ai-banner__dot ${i === index ? "is-active" : ""}`}
                aria-label={`슬라이드 ${i + 1} 보기`}
                onClick={() => setIndex(i)}
              />
            ))}
          </div>

          <button className="ctrl-btn" aria-label="다음 슬라이드" onClick={goNext}>
            <ArrowForwardIos fontSize="small" />
          </button>
        </div>
      </Box>
    </section>
  );
}
