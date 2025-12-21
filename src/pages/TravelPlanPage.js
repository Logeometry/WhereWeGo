import React, { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Box,
  Typography,
  Button,
  Paper,
  Stack,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  TextField,
} from "@mui/material";
import FlightTakeoffIcon from "@mui/icons-material/FlightTakeoff";
import EventNoteIcon from "@mui/icons-material/EventNote";
import TipsAndUpdatesIcon from "@mui/icons-material/TipsAndUpdates";
import DeleteIcon from "@mui/icons-material/Delete";
import { DragDropContext, Droppable, Draggable } from "react-beautiful-dnd";
import DragIndicatorIcon from '@mui/icons-material/DragIndicator';
import axios from 'axios';

export async function generateItinerary(requestData) {
  try {
    const res = await axios.post("http://localhost:8000/api/v1/generate", requestData);
    return res.data;
  } catch (error) {
    console.error("여행 일정을 생성하는 중 오류 발생:", error);
    throw error; // 에러를 상위 컴포넌트로 전달하여 처리
  }
}

// 이 samplePlaces와 getRecommendations 함수는 더 이상 초기 일정 생성에 직접 사용되지 않습니다.
// '관광지 검색 및 추가' 기능을 위해 남겨두거나, 더 넓은 범위의 데이터를 제공하도록 수정할 수 있습니다.
// 현재는 `availablePlaces`가 `state.surveyAttractions`에서 채워지므로, 이 부분은 그대로 두셔도 무방합니다.
const samplePlaces = [
  { id: 1, name: "해운대 해수욕장", description: "부산의 대표 해수욕장", duration: 2, locX: 129.1586, locY: 35.1586 },
  { id: 2, name: "광안리 해수욕장", description: "밤에도 아름다운 해변", duration: 2, locX: 129.1186, locY: 35.1532 },
  { id: 3, name: "자갈치 시장", description: "신선한 해산물 시장", duration: 1, locX: 129.0369, locY: 35.0962 },
  { id: 4, name: "부산타워", description: "부산의 랜드마크", duration: 1, locX: 129.0369, locY: 35.0962 },
  { id: 5, name: "태종대", description: "절경의 바다 전망", duration: 2, locX: 129.0859, locY: 35.0566 },
  { id: 6, name: "감천문화마을", description: "아름다운 벽화와 골목길", duration: 3, locX: 129.0108, locY: 35.0945 },
  { id: 7, name: "송도 해상 케이블카", description: "바다 위를 가로지르는 케이블카", duration: 2, locX: 129.0177, locY: 35.0776 },
  { id: 8, name: "국제시장", description: "다양한 상품과 먹거리가 있는 시장", duration: 2, locX: 129.0270, locY: 35.1018 },
  { id: 9, name: "벡스코", description: "국제 회의 및 전시 센터", duration: 1, locX: 129.1915, locY: 35.1681 },
  { id: 10, name: "동백섬", description: "해운대 옆 아름다운 산책로", duration: 1, locX: 129.1627, locY: 35.1578 },
];

const getRecommendations = () => samplePlaces; // 이 함수도 이제 주 용도가 아님


const getDragItemStyle = (style, snapshot) => {
  if (!snapshot.isDragging) {
    return style;
  }
  if (style?.transform) {
    // 이전 답변에서 드래그 시 x축 이동 방지 로직을 추가했지만,
    // 현재 코드에서는 원본 slice 방식을 사용하고 있어 다시 문제가 될 수 있습니다.
    // transform이 translate3d를 포함할 경우를 고려하여 수정합니다.
    const yValue = style.transform.includes('translate3d') 
        ? style.transform.split(',')[1].trim() 
        : style.transform.slice(style.transform.indexOf(',') + 1); 
    const newTransform = `translate(0px, ${yValue}`;
    return {
      ...style,
      transform: newTransform,
    };
  }
  return style;
};

const TravelPlanPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const goToPlaceDetail = (placeId) => {
    navigate(`/tourist/${placeId}`);
  };

  const { state } = location;
  const mapContainerRef = useRef(null); // Ref for the map container div
  const tmapInstanceRef = useRef(null); // Ref to hold the Tmap instance

  const [tmapLoaded, setTmapLoaded] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [travelDuration, setTravelDuration] = useState(3); // 초기값, 백엔드 응답으로 업데이트될 예정
  const [dailySchedule, setDailySchedule] = useState([]); // 백엔드에서 받아올 여행 일정
  const [travelTips, setTravelTips] = useState(""); // <-- 여기에 setTravelTips 선언이 있어야 합니다.
  const [availablePlaces, setAvailablePlaces] = useState([]); // 검색 및 추가에 사용될 전체 관광지 목록

  // --- 1. 첫 번째 useEffect: Tmap SDK 동적 로드 (이것은 이미 올바른 위치에 있음) ---
  useEffect(() => {
    if (window.Tmapv2) {
      setTmapLoaded(true);
      return;
    }

    const script = document.createElement("script");
    script.src = "https://apis.openapi.sk.com/tmap/js/v2/tmap.js?version=1&appKey=SEoFeQcobE8FEhuKdDInC8wxcVwU0yC1aDQM7zCm";
    script.async = true;
    script.onload = () => {
      console.log("Tmap SDK loaded successfully.");
      setTmapLoaded(true);
    };
    script.onerror = (error) => {
      console.error("Failed to load Tmap SDK:", error);
    };
    document.head.appendChild(script);
    return () => {
      document.head.removeChild(script);
    };
  }, []);

  // --- 2. 두 번째 useEffect: 백엔드 API 호출 및 데이터 설정 (새로 추가/이동해야 할 부분) ---
  // 이 useEffect가 이전에 다른 useEffect 안에 중첩되어 있었던 것으로 보입니다.
  // 이제 이 useEffect를 컴포넌트 최상위 레벨로 빼냅니다.
  useEffect(() => {
    if (!state) {
      navigate("/"); // state가 없으면 초기 페이지로 리다이렉트
      return;
    }

    // 설문조사 페이지에서 넘겨받은 surveyAttractions를 availablePlaces에 설정
    // 이를 통해 "관광지 검색 및 추가" 섹션에서 검색 가능한 장소 목록을 제공
    if (state.surveyAttractions) {
      setAvailablePlaces(state.surveyAttractions.map(attraction => ({
        id: attraction.id, // SurveyPage의 id를 그대로 사용
        name: attraction.name,
        description: attraction.description,
        duration: attraction.duration,
        locX: attraction.lng, // 위도, 경도 필드명에 유의 (백엔드는 [lng, lat] 배열)
        locY: attraction.lat,
      })));
    }

    const fetchAndSetItinerary = async () => {
      const {
        departureCity,
        otherCity,
        travelDuration: initialTravelDuration, // 이름 충돌 방지
        travelStartDate,
        startingPoint,
        surveyAttractions,
        preferences
      } = state;

      // 백엔드 API 요청 페이로드 구성
      const requestPayload = {
        departureCity: departureCity,
        otherCity: otherCity,
        travelDuration: initialTravelDuration, // 설문조사에서 입력받은 여행 기간 사용
        travelStartDate: travelStartDate,
        startingPoint: startingPoint, // 백엔드는 ObjectId 문자열을 기대하므로, SurveyPage에서 넘어온 ID 사용
        preferences: preferences || {}, // preferences가 없을 경우를 대비하여 빈 객체
        // surveyAttractions는 백엔드에서 이름 목록을 기대하므로 매핑
        surveyAttractions: surveyAttractions.map(attraction => attraction.name)
      };

      try {
        const data = await generateItinerary(requestPayload);
        console.log("백엔드에서 받은 여행 일정 데이터:", data);

        // 백엔드에서 받은 데이터로 state 업데이트
        setTravelDuration(data.dailySchedule.length); // 실제 일수는 백엔드에서 받아온 일정의 길이에 따름
        setDailySchedule(data.dailySchedule.map(day => ({
          ...day,
          places: day.places.map(place => ({
            id: place._id, // 백엔드의 _id를 프론트엔드의 id로 사용
            name: place.name,
            description: place.description,
            duration: place.estimated_duration, // 백엔드의 estimated_duration 사용
            locX: place.location.coordinates[0], // 백엔드 좌표 형식 [longitude, latitude]에 맞춰 매핑
            locY: place.location.coordinates[1],
          })),
          // 첫째 날과 마지막 날 플래그 동적으로 설정
          isFirstDay: day.day === 1,
          isLastDay: day.day === data.dailySchedule.length,
        })));
        setTravelTips(data.travelTips); // <-- setTravelTips는 여기서 사용

      } catch (error) {
        console.error("여행 일정을 가져오는 데 실패했습니다:", error);
        alert("여행 일정을 가져오는 데 실패했습니다. 다시 시도해 주세요.");
        navigate("/"); // 에러 발생 시 설문 페이지로 리다이렉트
      }
    };

    fetchAndSetItinerary();
  }, [state, navigate]); // state와 navigate가 변경될 때마다 이 useEffect 실행


  // --- 3. 세 번째 useEffect: Tmap 지도 초기화 및 마커/경로 표시 (이것도 올바른 위치로 이동) ---
  // 이 useEffect도 이전에는 다른 useEffect 안에 중첩되어 있었던 것으로 보입니다.
  // 이 또한 컴포넌트 최상위 레벨로 빼냅니다.
  useEffect(() => {
    // Ensure Tmap SDK is loaded and the map container element exists
    if (!tmapLoaded || !mapContainerRef.current || dailySchedule.length === 0) {
      console.log("Tmap이 로드되지 않았거나, 지도 컨테이너가 준비되지 않았거나, 일정 데이터가 없습니다.");
      return;
    }

    const places = dailySchedule[0]?.places || [];
    if (places.length === 0) {
      console.log("첫째 날 지도에 표시할 장소가 없습니다.");
      // 장소가 없으면 기존 지도 인스턴스를 파괴하여 stale 데이터를 방지
      if (tmapInstanceRef.current) {
        tmapInstanceRef.current.destroy();
        tmapInstanceRef.current = null;
      }
      return;
    }

    // 기존 지도 인스턴스가 있다면 파괴하여 여러 지도가 생성되는 것을 방지
    if (tmapInstanceRef.current) { 
      console.log("기존 Tmap 인스턴스를 파괴합니다.");
      tmapInstanceRef.current.destroy(); 
      tmapInstanceRef.current = null; 
    }

    // 지도 생성
    const initialCenter = places[0] ? new window.Tmapv2.LatLng(places[0].locY, places[0].locX) : new window.Tmapv2.LatLng(35.1798, 129.0750); // 장소가 없으면 부산 중심 좌표 기본값

    console.log("Tmap을 초기화합니다. 중심 좌표:", initialCenter);
    tmapInstanceRef.current = new window.Tmapv2.Map(mapContainerRef.current, {
      center: initialCenter,
      width: "100%",
      height: "400px",
      zoom: 13,
      // appKey는 스크립트 로드 시 이미 지정되었으므로 여기서는 선택 사항입니다.
      // appKey: "YOUR_TMAP_APP_KEY_HERE",
    });

    // 마커 추가
    const markers = [];
    places.forEach((place) => {
      if (!place.locX || !place.locY) {
        console.warn(`장소 ${place.name}에 위치 좌표가 누락되었습니다.`);
        return;
      }
      const marker = new window.Tmapv2.Marker({
        position: new window.Tmapv2.LatLng(place.locY, place.locX),
        map: tmapInstanceRef.current,
        title: place.name,
      });
      markers.push(marker);
    });
    console.log(`지도에 ${markers.length}개의 마커를 추가했습니다.`);

    // 폴리라인 경로 추가
    if (places.length >= 2) {
      const path = places.map(p => new window.Tmapv2.LatLng(p.locY, p.locX));
      new window.Tmapv2.Polyline({
        path,
        strokeColor: "#FF0000",
        strokeWeight: 3,
        map: tmapInstanceRef.current,
      });
      console.log("지도에 폴리라인 경로를 추가했습니다.");
    }

    // 정리 함수: 컴포넌트 언마운트 또는 의존성 변경 시 지도 파괴
    return () => {
      if (tmapInstanceRef.current) {
        console.log("Tmap 인스턴스를 정리합니다.");
        tmapInstanceRef.current.destroy();
        tmapInstanceRef.current = null;
      }
    };
  }, [dailySchedule, tmapLoaded]); // dailySchedule 또는 tmapLoaded가 변경될 때 다시 실행


  // 관광지 추가
  const addPlaceToDay = (dayId, place) => {
    setDailySchedule((prev) =>
      prev.map((day) =>
        day.day === dayId ? { ...day, places: [...day.places, place] } : day
      )
    );
  };

  // 관광지 삭제
  const removePlaceFromDay = (dayId, placeId) => {
    setDailySchedule((prev) =>
      prev.map((day) =>
        day.day === dayId
          ? { ...day, places: day.places.filter((p) => p.id !== placeId) }
          : day
      )
    );
  };

  // 드래그 앤 드롭 이벤트 핸들러
  const onDragEnd = (result) => {
    const { source, destination } = result;

    if (!destination) {
      return;
    }

    const dayId = parseInt(destination.droppableId, 10);
    setDailySchedule(prevSchedule =>
      prevSchedule.map(day => {
        if (day.day === dayId) {
          const reorderedPlaces = Array.from(day.places);
          const [movedItem] = reorderedPlaces.splice(source.index, 1);
          reorderedPlaces.splice(destination.index, 0, movedItem);
          return { ...day, places: reorderedPlaces };
        }
        return day;
      })
    );
  };

  // 여행 일수 추가/제거
  const addDay = () => {
    const lastDay = dailySchedule[dailySchedule.length - 1];
    const newDate = lastDay ? new Date(lastDay.date) : new Date(state.travelStartDate); // 마지막 날이 없으면 여행 시작일을 기준으로
    newDate.setDate(newDate.getDate() + 1);

    const newDay = {
      day: travelDuration + 1,
      date: newDate.toISOString().split('T')[0], // YYYY-MM-DD 형식으로 저장
      places: [],
      isFirstDay: false, // 새로 추가된 날은 첫째 날이 아님
      isLastDay: true, // 새로 추가된 날은 마지막 날
    };
    setDailySchedule((prev) => [...prev.map((day) => ({ ...day, isLastDay: false })), newDay]);
    setTravelDuration((prev) => prev + 1);
  };

  const removeDay = () => {
    if (travelDuration <= 1) return; // 1일 미만으로는 줄일 수 없음

    // 마지막 날을 제거하고, 남은 배열의 마지막 요소에 isLastDay 플래그를 true로 설정
    setDailySchedule((prev) => {
      const newSchedule = prev.slice(0, -1);
      if (newSchedule.length > 0) {
        // 기존의 마지막 날에 isLastDay를 false로 바꾸는 로직이 이미 Map에 포함되어 있으니,
        // 여기서는 새로 마지막이 될 날에만 true를 설정합니다.
        newSchedule[newSchedule.length - 1] = {
          ...newSchedule[newSchedule.length - 1],
          isLastDay: true
        };
      }
      return newSchedule;
    });
    setTravelDuration((prev) => prev - 1);
  };


  // 검색 결과 필터링
  const filteredPlaces = availablePlaces.filter((place) =>
    place.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // state가 없으면 초기 페이지로 리다이렉트
  useEffect(() => {
    if (!state) {
      navigate("/");
    }
  }, [state, navigate]);

  if (!state) {
    return (
      <Box
        sx={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          minHeight: "100vh",
          backgroundColor: "#f0f2f5",
          padding: 2,
          boxSizing: "border-box",
        }}
      >
        <Paper
          elevation={6}
          sx={{
            padding: 5,
            borderRadius: "12px",
            textAlign: "center",
            maxWidth: "500px",
            width: "100%",
          }}
        >
          <Typography variant="h5" component="h2" color="text.primary" mb={2}>
            정보를 불러오는 중...
          </Typography>
          <Typography variant="body1" color="text.secondary">
            잠시만 기다려 주세요.
          </Typography>
        </Paper>
      </Box>
    );
  }

  const {
    departureCity,
    otherCity,
    travelStartDate,
    startingPoint,
    startingPoints,
  } = state;

  const selectedStartingPoint = startingPoints?.find((p) => p.id === startingPoint) || {
    id: 0,
    name: "부산역",
    description: "부산의 중심역",
  };

  // 실제 Tmap API 호출 예시 (경로탐색)
  const fetchTmapRoute = async (startX, startY, endX, endY, passList) => {
    try {
      const response = await fetch("https://apis.openapi.sk.com/tmap/routes/pedestrian?version=1", {
        method: "POST",
        headers: {
          "accept": "application/json",
          "content-type": "application/json",
          "appKey": "IkPe7KhKNh6aOAIHUqYw75Ww42atrqtV4J5ZX0cc", // 하드코딩
        },
        body: JSON.stringify({
          startX,
          startY,
          endX,
          endY,
          passList: passList.join("_"),
          startName: "출발지",
          endName: "목적지",
        }),
      });
      return await response.json();
    } catch (err) {
      console.error("Tmap API 호출 실패:", err);
      return null;
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        minHeight: "100vh",
        backgroundColor: "#f0f2f5",
        padding: 2,
        boxSizing: "border-box",
      }}
    >
      <Paper
        elevation={6}
        sx={{
          backgroundColor: "#ffffff",
          borderRadius: "12px",
          boxShadow: "0 4px 20px rgba(0, 0, 0, 0.08)",
          padding: 5,
          width: "100%",
          maxWidth: "1200px",
          boxSizing: "border-box",
          display: "flex",
          flexDirection: "column",
          gap: 3,
        }}
      >
        <Box sx={{ width: "100%" }}>
          {/* 여행 개요 */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h4" component="h2" color="text.primary" sx={{ fontWeight: 600, mb: 2 }}>
              여행 일정
            </Typography>
            <Paper elevation={2} sx={{ borderRadius: "12px", padding: 3 }}>
              <Stack spacing={2}>
                <Typography variant="h6" component="h3" color="text.primary">
                  여행 정보
                </Typography>
                <Box>
                  <Typography variant="body1" fontWeight="medium">
                    출발지: {departureCity === "기타" ? otherCity : departureCity}
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    여행지: 부산
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    여행 기간: {travelDuration}일
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    여행 시작일: {new Date(travelStartDate).toLocaleDateString("ko-KR")}
                  </Typography>
                </Box>
              </Stack>
            </Paper>
          </Box>

          {/* 추가된 코스 (Tmap 지도) */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" component="h3" color="text.primary" sx={{ fontWeight: 600, mb: 2 }}>
              추가된 코스 (Tmap)
            </Typography>
            <Paper elevation={2} sx={{ borderRadius: "12px", padding: 3 }}>
              <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
                여행 일정에 따라 관광지 위치가 지도에 표시됩니다. (현재 첫째 날 코스만 표시)
              </Typography>
              <Box
                id="tmap-container"
                ref={mapContainerRef}
                sx={{
                  width: "100%",
                  height: "400px",
                  backgroundColor: "#e0e0f0",
                  borderRadius: "8px",
                }}
              />
            </Paper>
          </Box>

          {/* 관광지 검색 및 추가 */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" component="h3" color="text.primary" sx={{ fontWeight: 600, mb: 2 }}>
              관광지 검색 및 추가
            </Typography>
            <Paper elevation={2} sx={{ borderRadius: "12px", padding: 3 }}>
              <TextField
                fullWidth
                label="관광지 검색"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                sx={{ mb: 2 }}
              />
              <List>
                {filteredPlaces.map((place) => (
                  <ListItem
                    key={place.id}
                    secondaryAction={
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={() => {
                          const dayToAdd = prompt("추가할 날짜(DAY)를 입력하세요 (예: 1)");
                          if (dayToAdd) {
                            const dayId = parseInt(dayToAdd, 10);
                            if (dayId >= 1 && dayId <= travelDuration) {
                              addPlaceToDay(dayId, place);
                            } else {
                              alert("유효한 날짜를 입력하세요.");
                            }
                          }
                        }}
                      >
                        추가
                      </Button>
                    }
                  >
                    <ListItemText primary={place.name} secondary={place.description} />
                  </ListItem>
                ))}
              </List>
            </Paper>
          </Box>

          {/* 일자 추가/제거 */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" component="h3" color="text.primary" sx={{ fontWeight: 600, mb: 2 }}>
              여행 일수 조정
            </Typography>
            <Paper elevation={2} sx={{ borderRadius: "12px", padding: 3 }}>
              <Stack direction="row" alignItems="center" spacing={2}>
                <Typography variant="body1" color="text.primary">
                  여행 일수: {travelDuration}일
                </Typography>
                <Button variant="outlined" onClick={addDay}>
                  일자 추가
                </Button>
                <Button variant="outlined" color="error" onClick={removeDay}>
                  일자 제거
                </Button>
              </Stack>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
                일자를 추가하면 마지막 날이 추가되고, 제거하면 마지막 날이 삭제됩니다.
              </Typography>
            </Paper>
          </Box>

          {/* 일별 여행 일정 (드래그 앤 드롭 적용) */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" component="h3" color="text.primary" sx={{ fontWeight: 600, mb: 3 }}>
              일별 여행 일정
            </Typography>
            <DragDropContext onDragEnd={onDragEnd}>
              <Stack spacing={3}>
                {dailySchedule.map((dayInfo) => (
                  <Paper key={dayInfo.day} elevation={2} sx={{ borderRadius: "12px", padding: 3 }}>
                    <Box sx={{ display: "flex", alignItems: "center", mb: 2 }}>
                      <Box
                        sx={{
                          background: "linear-gradient(to right, #1976d2, #00bcd4)",
                          color: "white",
                          px: 2,
                          py: 1,
                          borderRadius: "8px",
                          fontWeight: "bold",
                          mr: 2,
                        }}
                      >
                        DAY {dayInfo.day}
                      </Box>
                      <Typography variant="body1" color="text.secondary">
                        {new Date(dayInfo.date).toLocaleDateString("ko-KR", { month: "short", day: "numeric", weekday: "short" })}
                      </Typography>
                    </Box>

                    <Stack spacing={1.5}>
                      {dayInfo.isFirstDay && (
                        <Paper sx={{ display: "flex", alignItems: "flex-start", gap: 1.5, p: 2, borderRadius: "8px" }}>
                          <Box sx={{ bgcolor: "success.main", color: "white", fontSize: "0.75rem", px: 1, py: 0.5, borderRadius: "4px", fontWeight: "bold" }}>
                            <FlightTakeoffIcon sx={{ fontSize: "1rem", verticalAlign: "middle", mr: 0.5 }} /> 출발
                          </Box>
                          <Box>
                            <Typography variant="body1" fontWeight="medium">
                              {selectedStartingPoint?.name}에서 여행 시작
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              {departureCity === "기타" ? otherCity : departureCity}에서 부산 도착 후 여행 시작
                            </Typography>
                          </Box>
                        </Paper>
                      )}

                      <Droppable droppableId={dayInfo.day.toString()}>
                        {(provided, snapshot) => (
                          <div
                            {...provided.droppableProps}
                            ref={provided.innerRef}
                            style={{
                              backgroundColor: snapshot.isDraggingOver ? '#eef2f6' : 'transparent',
                              border: snapshot.isDraggingOver ? '2px dashed #42a5f5' : '2px dashed transparent',
                              borderRadius: '12px',
                              padding: '8px',
                              transition: 'background-color 0.2s ease, border 0.2s ease',
                              minHeight: '80px',
                            }}
                          >
                            {dayInfo.places.map((place, index) => (
                              <Draggable key={place.id} draggableId={place.id.toString()} index={index}>
                                {(provided, snapshot) => (
                                  <Paper
                                    ref={provided.innerRef}
                                    {...provided.draggableProps}
                                    elevation={snapshot.isDragging ? 8 : 2}
                                    style={getDragItemStyle(provided.draggableProps.style, snapshot)}
                                    sx={{
                                      p: 2,
                                      mb: 1.5,
                                      backgroundColor: snapshot.isDragging ? '#f0f8ff' : 'white',
                                      border: snapshot.isDragging ? '2px solid #1976d2' : '1px solid #e0e0e0',
                                      borderRadius: '12px',
                                      transform: snapshot.isDragging ? 'rotate(1.5deg) scale(1.02)' : 'none',
                                      transition: 'all 0.2s cubic-bezier(0.2, 0, 0, 1)',
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: 1.5,
                                    }}
                                  >
                                    <Box {...provided.dragHandleProps} sx={{ cursor: 'grab', color: 'text.secondary', display: 'flex' }}>
                                      <DragIndicatorIcon />
                                    </Box>

                                    <Box sx={{ bgcolor: 'info.light', color: 'white', fontSize: '0.8rem', px: 1, py: 0.5, borderRadius: 1, fontWeight: 'bold' }}>
                                      {index + 1}
                                    </Box>

                                    <Box sx={{ flexGrow: 1 }}>
                                      <Typography variant="body1" fontWeight="medium">
                                        {place.name}
                                      </Typography>
                                      <Typography variant="body2" color="text.secondary">
                                        {place.description}
                                      </Typography>
                                    </Box>

                                    <Typography variant="caption" color="primary.main" sx={{ mr: 1 }}>
                                      {place.duration}시간
                                    </Typography>

                                    <IconButton
                                      size="small"
                                      onClick={() => removePlaceFromDay(dayInfo.day, place.id)}
                                    >
                                      <DeleteIcon fontSize="small" />
                                    </IconButton>
                                  </Paper>
                                )}
                              </Draggable>
                            ))}
                            {provided.placeholder}
                          </div>
                        )}
                      </Droppable>


                      {dayInfo.isLastDay && (
                        <Paper sx={{ display: "flex", alignItems: "flex-start", gap: 1.5, p: 2, borderRadius: "8px" }}>
                          <Box sx={{ bgcolor: "error.main", color: "white", fontSize: "0.75rem", px: 1, py: 0.5, borderRadius: "4px", fontWeight: "bold" }}>
                            <FlightTakeoffIcon sx={{ fontSize: "1rem", verticalAlign: "middle", mr: 0.5, transform: "scaleX(-1)" }} /> 복귀
                          </Box>
                          <Box>
                            <Typography variant="body1" fontWeight="medium">
                              부산에서 {departureCity === "기타" ? otherCity : departureCity}로 출발
                            </Typography>
                            <Typography variant="body2" color="text.secondary">
                              즐거운 여행을 마치고 집으로
                            </Typography>
                          </Box>
                        </Paper>
                      )}
                    </Stack>
                  </Paper>
                ))}
              </Stack>
            </DragDropContext>
          </Box>

          {/* 여행 팁 */}
          <Box sx={{ mb: 4 }}>
            <Typography variant="h5" component="h3" color="text.primary" sx={{ fontWeight: 600, mb: 2 }}>
              여행 팁
            </Typography>
            <Paper elevation={2} sx={{ borderRadius: "12px", padding: 3 }}>
              <Stack spacing={2}>
                <Typography variant="h6" component="h4" color="text.primary">
                  여행 준비물
                </Typography>
                <List>
                  <ListItem>
                    <ListItemIcon>
                      <TipsAndUpdatesIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText primary="여권/신분증, 현금/카드" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <TipsAndUpdatesIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText primary="필수 약품, 보조배터리" />
                  </ListItem>
                  <ListItem>
                    <ListItemIcon>
                      <TipsAndUpdatesIcon color="primary" />
                    </ListItemIcon>
                    <ListItemText primary="날씨에 맞는 옷, 우산" />
                  </ListItem>
                </List>
              </Stack>
            </Paper>
          </Box>

          {/* 다시 설문하기 버튼 */}
          <Box sx={{ display: "flex", justifyContent: "flex-end", mt: 4 }}>
            <Button
              variant="contained"
              color="primary"
              onClick={() => navigate("/")}
              sx={{ fontWeight: "bold" }}
            >
              다시 설문하기
            </Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};

export default TravelPlanPage;