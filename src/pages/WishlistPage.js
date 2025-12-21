// src/pages/WishlistPage.jsx
import React, { useState, useEffect, useCallback } from "react";
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardMedia,
  CardContent,
  IconButton,
  Button,
  Snackbar,
  Alert,
  CircularProgress,
} from "@mui/material";
import FavoriteBorderIcon from "@mui/icons-material/FavoriteBorder";
import FavoriteIcon from "@mui/icons-material/Favorite";
import FolderOpenIcon from "@mui/icons-material/FolderOpen";
import RefreshIcon from "@mui/icons-material/Refresh";
import { useNavigate } from "react-router-dom";
import { listPlans } from "../utils/planStorage";

const API_PREFIX =
  process.env.REACT_APP_API_PREFIX ||
  (typeof import.meta !== "undefined" &&
    import.meta.env &&
    import.meta.env.VITE_API_PREFIX) ||
  "";

const API_BASE = `${API_PREFIX.replace(/\/$/, "")}/api/v1`;

// 로컬 스토리지 키(폴백용)
const WISHLIST_STORAGE_KEY = "myWishlist";

// -----------------------------
// API helpers
// -----------------------------
async function fetchWishlist(userId) {
  const res = await fetch(`${API_BASE}/wishlist/${encodeURIComponent(userId)}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}
async function deleteWish({ user_id, place_id }) {
  const res = await fetch(`${API_BASE}/wish`, {
    method: "DELETE",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, place_id }),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json();
}

// 이미지 폴백 핸들러
const withImageFallback = (e, fallback = "/image/wish-bgr.jpg") => {
  const img = e?.target;
  if (img && img.src !== window.location.origin + fallback) {
    img.src = fallback;
  }
};

const WishlistPage = () => {
  const navigate = useNavigate();

  // 로그인 사용자 ID (앱 전역에서 주입하는 값 사용 권장)
  const userId = localStorage.getItem("user_id") || "";

  const [wishlist, setWishlist] = useState([]);
  const [plans, setPlans] = useState(() => listPlans());

  const [loading, setLoading] = useState(true);
  const [errMsg, setErrMsg] = useState("");
  const [okMsg, setOkMsg] = useState("");

  const normalizeWishlist = useCallback((data) => {
    const raw = Array.isArray(data) ? data : data?.items || [];
    return raw.map((p, i) => ({
      id: p.place_id || p._id || p.id || String(i + 1),
      name: p.name || p.title || "이름 없음",
      image: p.image || p.photoUrl || "/image/wish-bgr.jpg",
    }));
  }, []);

  const loadWishlist = useCallback(async () => {
    setLoading(true);
    try {
      if (!userId) throw new Error("no-user");
      const data = await fetchWishlist(userId);
      const normalized = normalizeWishlist(data);
      setWishlist(normalized);
      try {
        localStorage.setItem(WISHLIST_STORAGE_KEY, JSON.stringify(normalized));
      } catch {}
      setErrMsg("");
    } catch (e) {
      // 서버 실패 → 로컬 폴백
      try {
        const saved = localStorage.getItem(WISHLIST_STORAGE_KEY);
        const parsed = saved ? JSON.parse(saved) : [];
        setWishlist(parsed);
        setErrMsg("서버 연결이 어려워 로컬에 저장된 위시리스트를 불러왔습니다.");
      } catch {
        setWishlist([]);
        setErrMsg("위시리스트를 불러오지 못했습니다.");
      }
    } finally {
      setLoading(false);
    }
  }, [normalizeWishlist, userId]);

  // 위시 로드
  useEffect(() => {
    loadWishlist();
  }, [loadWishlist]);

  // 내 코스: 포커스 시 새로고침
  useEffect(() => {
    const onFocus = () => setPlans(listPlans());
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, []);

  // ♥ 토글: 위시 페이지에서는 제거만 수행
  const removeFromWishlist = async (touristItem) => {
    const placeId = touristItem.id;
    // 낙관적 제거
    const prev = wishlist;
    setWishlist((p) => p.filter((item) => item.id !== placeId));

    try {
      if (userId) await deleteWish({ user_id: userId, place_id: placeId });

      // 로컬 동기화
      try {
        const saved = JSON.parse(localStorage.getItem(WISHLIST_STORAGE_KEY) || "[]");
        const next = saved.filter((i) => i.id !== placeId);
        localStorage.setItem(WISHLIST_STORAGE_KEY, JSON.stringify(next));
      } catch {}

      setOkMsg("위시리스트에서 제거했습니다.");
    } catch (e) {
      // 롤백
      setWishlist(prev);
      setErrMsg("위시리스트 삭제 중 오류가 발생했습니다.");
    }
  };

  // 추천(샘플)
  const recommendedSpots = [
    { id: "rec-haeundae", name: "해운대", image: "/image/HaeundaeBeach.jpg" },
    { id: "rec-gwangalli", name: "광안리", image: "/image/HaeundaeBeach.jpg" },
    { id: "rec-gamcheon", name: "감천문화마을", image: "/image/Gamcheon.jpg" },
    { id: "rec-taejongdae", name: "태종대", image: "/image/Taejong-daeAmusementPark.jpg" },
  ];

  const planningSpots = [
    { image: "/image/busan-food.jpg", title: "부산 맛집 지도" },
    { image: "/image/busan-metro.jpg", title: "지하철로 여행하기" },
    { image: "/image/busan-festival.jpg", title: "축제 & 행사 일정" },
  ];

  return (
    <Box sx={{ backgroundColor: "#fffaf3", minHeight: "100vh" }}>
      {/* Hero */}
      <Box
        sx={{
          position: "relative",
          height: "300px",
          backgroundImage: "url(/image/wish-bgr.jpg)",
          backgroundSize: "cover",
          backgroundPosition: "center",
        }}
      >
        <Box
          sx={{
            position: "absolute",
            bottom: 40,
            left: "50%",
            transform: "translateX(-50%)",
            color: "#fff",
            textAlign: "center",
            textShadow: "1px 1px 5px rgba(0,0,0,0.5)",
          }}
        >
          <Typography variant="h4" fontWeight="bold">
            나의 위시리스트
          </Typography>
        </Box>
      </Box>

      <Container maxWidth="md" sx={{ pt: 6, pb: 8 }}>
        {/* 상단 상태/액션 바 */}
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center", mb: 2 }}>
          <Typography variant="h6">여행지</Typography>
          <Button
            size="small"
            startIcon={<RefreshIcon />}
            onClick={loadWishlist}
            variant="outlined"
          >
            새로고침
          </Button>
        </Box>

        {/* 로딩 상태 */}
        {loading && (
          <Box sx={{ py: 6, display: "flex", alignItems: "center", justifyContent: "center" }}>
            <CircularProgress />
          </Box>
        )}

        {/* 여행지 위시리스트 */}
        {!loading && (wishlist.length === 0 ? (
          <Box
            sx={{
              backgroundColor: "#eef6f9",
              textAlign: "center",
              borderRadius: 2,
              py: 6,
              mb: 5,
            }}
          >
            <FavoriteBorderIcon sx={{ fontSize: 48, color: "#ccc" }} />
            <Typography variant="subtitle1" sx={{ mt: 2 }}>
              아직 저장된 여행지가 없습니다
            </Typography>
            <Typography variant="body2" color="text.secondary">
              관광지의 ♥ 버튼을 눌러 여행지를 추가해보세요
            </Typography>
            <Button
              variant="contained"
              color="primary"
              sx={{ mt: 3 }}
              onClick={() => navigate("/")}
            >
              관광지 찾아보기
            </Button>
          </Box>
        ) : (
          <Grid container spacing={2} sx={{ mb: 6 }}>
            {wishlist.map((spot) => (
              <Grid item xs={6} sm={3} key={spot.id}>
                <Card
                  sx={{ position: "relative", borderRadius: 2, cursor: "pointer" }}
                  onClick={() => navigate(`/place/${encodeURIComponent(spot.id)}`)}
                >
                  <CardMedia
                    component="img"
                    height="140"
                    image={spot.image}
                    alt={spot.name || spot.title}
                    onError={(e) => withImageFallback(e)}
                  />
                  <CardContent sx={{ p: 1, pb: "8px !important", textAlign: "center" }}>
                    <Typography fontWeight="bold" noWrap title={spot.name || spot.title}>
                      {spot.name || spot.title}
                    </Typography>
                  </CardContent>

                  {/* ♥ 제거 (카드 클릭과 구분 위해 IconButton 클릭 시 이벤트 중단) */}
                  <IconButton
                    sx={{
                      position: "absolute",
                      top: 8,
                      right: 8,
                      color: "red",
                      backgroundColor: "rgba(0,0,0,0.3)",
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFromWishlist(spot);
                    }}
                    aria-label="위시에서 제거"
                  >
                    <FavoriteIcon />
                  </IconButton>
                </Card>
              </Grid>
            ))}
          </Grid>
        ))}

        {/* 내 코스(저장된 일정) */}
        <Typography variant="h6" gutterBottom sx={{ mt: 6 }}>
          내 코스
        </Typography>
        {plans.length === 0 ? (
          <Box
            sx={{
              backgroundColor: "#f4f7ff",
              textAlign: "center",
              borderRadius: 2,
              py: 4,
              mb: 5,
            }}
          >
            <FolderOpenIcon sx={{ fontSize: 44, color: "#90a4ae" }} />
            <Typography variant="subtitle1" sx={{ mt: 1 }}>
              저장된 코스가 없습니다
            </Typography>
            <Typography variant="body2" color="text.secondary">
              여행 페이지에서 ‘저장’ 버튼을 눌러 코스를 저장해보세요
            </Typography>
          </Box>
        ) : (
          <Grid container spacing={2} sx={{ mb: 6 }}>
            {plans.map((p) => (
              <Grid item xs={12} sm={6} key={p.id}>
                <Card sx={{ borderRadius: 2, display: "flex" }}>
                  <CardMedia
                    component="img"
                    image={p.cover || "/image/wish-bgr.jpg"}
                    alt={p.title}
                    onError={(e) => withImageFallback(e)}
                    sx={{ width: 140, height: 120, objectFit: "cover" }}
                  />
                  <CardContent sx={{ flex: 1 }}>
                    <Typography fontWeight="bold" noWrap title={p.title}>
                      {p.title}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {p.createdAt ? new Date(p.createdAt).toLocaleString() : ""}
                    </Typography>
                    <Box sx={{ mt: 1.2, display: "flex", gap: 1 }}>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() =>
                          navigate("/travel?planId=" + encodeURIComponent(p.id))
                        }
                      >
                        불러와서 편집
                      </Button>
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        {/* 추천 여행지(샘플) */}
        <Typography variant="h6" gutterBottom>
          추천 여행지
        </Typography>
        <Grid container spacing={2} sx={{ mb: 6 }}>
          {recommendedSpots.map((spot) => {
            const inWish = wishlist.some((item) => item.id === spot.id);
            return (
              <Grid item xs={6} sm={3} key={spot.id}>
                <Card sx={{ position: "relative", borderRadius: 2 }}>
                  <CardMedia
                    component="img"
                    height="140"
                    image={spot.image}
                    alt={spot.name}
                    onError={(e) => withImageFallback(e)}
                  />
                  <CardContent sx={{ p: 1, pb: "8px !important", textAlign: "center" }}>
                    <Typography fontWeight="bold" noWrap title={spot.name}>
                      {spot.name}
                    </Typography>
                  </CardContent>
                  <IconButton
                    sx={{
                      position: "absolute",
                      top: 8,
                      right: 8,
                      color: inWish ? "red" : "#fff",
                      backgroundColor: "rgba(0,0,0,0.3)",
                    }}
                    disabled
                  >
                    {inWish ? <FavoriteIcon /> : <FavoriteBorderIcon />}
                  </IconButton>
                </Card>
              </Grid>
            );
          })}
        </Grid>

        {/* 여행 계획하기(샘플 카드) */}
        <Typography variant="h6" gutterBottom>
          여행 계획하기
        </Typography>
        <Grid container spacing={2}>
          {planningSpots.map((spot, i) => (
            <Grid item xs={12} sm={6} md={4} key={i}>
              <Card sx={{ borderRadius: 2 }}>
                <CardMedia
                  component="img"
                  height="160"
                  image={spot.image}
                  alt={spot.title}
                  onError={(e) => withImageFallback(e)}
                />
              </Card>
            </Grid>
          ))}
        </Grid>
      </Container>

      {/* 알림 스낵바 */}
      <Snackbar
        open={!!errMsg}
        autoHideDuration={4000}
        onClose={() => setErrMsg("")}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity="warning" onClose={() => setErrMsg("")} sx={{ width: "100%" }}>
          {errMsg}
        </Alert>
      </Snackbar>
      <Snackbar
        open={!!okMsg}
        autoHideDuration={2000}
        onClose={() => setOkMsg("")}
        anchorOrigin={{ vertical: "bottom", horizontal: "center" }}
      >
        <Alert severity="success" onClose={() => setOkMsg("")} sx={{ width: "100%" }}>
          {okMsg}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default WishlistPage;
